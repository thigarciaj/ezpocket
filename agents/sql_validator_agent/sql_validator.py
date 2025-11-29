#!/usr/bin/env python3
"""
SQL Validator Agent - Valida queries SQL para AWS Athena
Verifica sintaxe, permissões, custos estimados e limites
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime

# Adicionar paths necessários
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

from openai import OpenAI

class SQLValidatorAgent:
    """
    Valida queries SQL para AWS Athena
    - Valida sintaxe SQL
    - Verifica operações permitidas
    - Estima custos de execução
    - Identifica riscos de segurança
    - Verifica limites do Athena
    """
    
    def __init__(self):
        """Inicializa o agente"""
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.roles = self._load_roles()
        self.model = 'gpt-4o'
        
        # Limites do AWS Athena (valores padrão)
        self.athena_limits = {
            'max_query_string_length': 262144,  # 256 KB
            'max_query_execution_time': 1800,    # 30 minutos
            'max_concurrent_queries': 25,
            'max_result_size': 10 * 1024 * 1024 * 1024,  # 10 GB
            'scan_cost_per_tb': 5.00  # USD por TB escaneado
        }
        
        # Carregar operações permitidas/proibidas do roles.json
        athena_ops = self.roles.get('athena_supported_operations', {})
        self.allowed_operations = athena_ops.get('ddl_read_only', [])
        self.forbidden_operations = athena_ops.get('ddl_forbidden', [])
        self.dangerous_functions = athena_ops.get('dangerous_functions', [])
        
        # Regras de segurança
        self.security_rules = self.roles.get('security_rules', {})
        self.forbidden_columns = self.security_rules.get('forbidden_columns', [])
    
    def _load_roles(self) -> Dict:
        """Carrega regras e roles do roles.json ou roles_local.json"""
        # Carregar .env para verificar BD_REFERENCE
        from dotenv import load_dotenv
        project_env = Path(__file__).parent.parent.parent / ".env"
        load_dotenv(project_env)
        
        # Verificar qual roles usar baseado em BD_REFERENCE
        bd_reference = os.getenv("BD_REFERENCE", "Athena")
        
        if bd_reference == "Local":
            roles_file = "roles_local.json"
            print(f"   🔧 SQL Validator usando roles_local.json (PostgreSQL 15)")
        else:
            roles_file = "roles.json"
            print(f"   🔧 SQL Validator usando roles.json (AWS Athena)")
        
        roles_path = Path(__file__).parent / roles_file
        with open(roles_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def validate(self, 
                 query_sql: str,
                 username: str,
                 projeto: str,
                 estimated_complexity: str = 'média') -> Dict[str, Any]:
        """
        Valida query SQL para Athena
        
        Args:
            query_sql: Query SQL a ser validada
            username: Usuário que solicitou
            projeto: Projeto do usuário
            estimated_complexity: Complexidade estimada (baixa/média/alta)
            
        Returns:
            Dict com resultado da validação
        """
        print(f"\n{'='*80}")
        print(f"🔍 SQL VALIDATOR AGENT - VALIDAÇÃO DE QUERY")
        print(f"{'='*80}")
        print(f"📥 INPUTS:")
        print(f"   👤 Username: {username}")
        print(f"   📁 Projeto: {projeto}")
        print(f"   📊 Complexidade: {estimated_complexity}")
        print(f"   📝 Query (primeiros 200 chars): {query_sql[:200]}...")
        print(f"{'='*80}\n")
        
        start_time = datetime.now()
        
        try:
            # 1. Validações básicas
            basic_validation = self._basic_validation(query_sql)
            if not basic_validation['valid']:
                return self._build_error_response(
                    basic_validation['error'],
                    basic_validation,
                    start_time,
                    query_sql
                )
            
            # 2. Validação de segurança
            security_validation = self._security_validation(query_sql)
            if not security_validation['valid']:
                return self._build_error_response(
                    security_validation['error'],
                    security_validation,
                    start_time,
                    query_sql
                )
            
            # 3. Validação com GPT-4o (sintaxe Athena específica)
            gpt_validation = self._gpt_validation(query_sql, estimated_complexity)
            
            # 4. Estimativa de custos
            cost_estimation = self._estimate_costs(query_sql, gpt_validation)
            
            # 5. Consolidar resultado
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'valid': gpt_validation.get('valid', True),
                'query_validated': query_sql,
                'syntax_valid': gpt_validation.get('syntax_valid', True),
                'athena_compatible': gpt_validation.get('athena_compatible', True),
                'security_issues': security_validation.get('issues', []),
                'warnings': gpt_validation.get('warnings', []),
                'optimization_suggestions': gpt_validation.get('suggestions', []),
                'estimated_scan_size_gb': cost_estimation['scan_size_gb'],
                'estimated_cost_usd': cost_estimation['cost_usd'],
                'estimated_execution_time_seconds': cost_estimation['execution_time_seconds'],
                'risk_level': self._calculate_risk_level(cost_estimation, security_validation),
                'tokens_used': gpt_validation.get('tokens_used', 0),
                'model_used': self.model,
                'execution_time': execution_time,
                'error': None
            }
            
            self._print_output(result)
            
            return result
            
        except Exception as e:
            error_msg = f"Erro na validação: {str(e)}"
            print(f"❌ {error_msg}")
            return self._build_error_response(error_msg, {}, start_time, query_sql)
    
    def _basic_validation(self, query_sql: str) -> Dict[str, Any]:
        """Validações básicas da query"""
        print("⚙️  PROCESSAMENTO:")
        print("   🔍 Validações básicas...")
        
        issues = []
        
        # 1. Tamanho da query
        max_length = self.athena_limits.get('max_query_string_length', 262144)
        if len(query_sql) > max_length:
            return {
                'valid': False,
                'error': f"Query excede tamanho máximo ({len(query_sql)} > {max_length} bytes)"
            }
        
        # 2. Query vazia
        if not query_sql or not query_sql.strip():
            return {
                'valid': False,
                'error': "Query vazia"
            }
        
        # 3. Operações proibidas
        query_upper = query_sql.upper()
        for op in self.forbidden_operations:
            if re.search(rf'\b{op}\b', query_upper):
                issues.append(f"Operação proibida detectada: {op}")
        
        if issues:
            return {
                'valid': False,
                'error': "; ".join(issues),
                'issues': issues
            }
        
        print("   ✅ Validações básicas OK")
        return {'valid': True, 'issues': []}
    
    def _security_validation(self, query_sql: str) -> Dict[str, Any]:
        """Validação de segurança"""
        print("   🔒 Validação de segurança...")
        
        issues = []
        query_upper = query_sql.upper()
        query_lower = query_sql.lower()
        
        # 1. Colunas sensíveis (CRÍTICO - BLOQUEAR ACESSO A DADOS SENSÍVEIS)
        for forbidden_col in self.forbidden_columns:
            # Busca por SELECT coluna_sensível ou coluna_sensível em qualquer contexto
            patterns = [
                rf'\bSELECT\b.*\b{forbidden_col}\b',  # SELECT com coluna sensível
                rf'\b{forbidden_col}\b.*\bFROM\b',    # coluna sensível antes de FROM
                rf'\bWHERE\b.*\b{forbidden_col}\b',   # coluna sensível em WHERE
                rf'\bJOIN\b.*\b{forbidden_col}\b'     # coluna sensível em JOIN
            ]
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    issues.append(f"🔒 ACESSO NEGADO: Coluna sensível detectada '{forbidden_col}' - Dados pessoais protegidos por LGPD")
                    break
        
        # 2. Keywords proibidos de dados sensíveis
        forbidden_keywords = self.security_rules.get('forbidden_keywords_in_query', [])
        for keyword in forbidden_keywords:
            if keyword.lower() in query_lower:
                issues.append(f"🔒 ACESSO NEGADO: Palavra-chave proibida '{keyword}' - Solicitação de dados sensíveis")
        
        # 3. Funções perigosas
        for func in self.dangerous_functions:
            if func in query_upper:
                issues.append(f"Função perigosa detectada: {func}")
        
        # 4. Comentários SQL suspeitos (SQL Injection)
        if '--' in query_sql or '/*' in query_sql:
            issues.append("Comentários SQL detectados (possível SQL injection)")
        
        # 5. UNION attacks
        if re.search(r'\bUNION\b.*\bSELECT\b', query_upper):
            issues.append("Possível UNION attack detectado")
        
        # 6. Múltiplas queries (;)
        if query_sql.count(';') > 1:
            issues.append("Múltiplas queries detectadas (não permitido)")
        
        if issues:
            print(f"   ⚠️  Problemas de segurança encontrados: {len(issues)}")
            return {
                'valid': False,
                'error': "Problemas de segurança detectados",
                'issues': issues
            }
        
        print("   ✅ Segurança OK")
        return {'valid': True, 'issues': []}
    
    def _gpt_validation(self, query_sql: str, estimated_complexity: str) -> Dict[str, Any]:
        """Validação com GPT-4o para sintaxe Athena"""
        print("   🤖 Validando com GPT-4o (sintaxe Athena)...")
        
        prompt = self.roles['gpt_validation_prompt'].format(
            query_sql=query_sql,
            estimated_complexity=estimated_complexity
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.roles['system_role']},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extrair JSON do response
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            result = json.loads(content)
            result['tokens_used'] = response.usage.total_tokens
            
            print(f"   ✅ Validação GPT concluída (tokens: {result['tokens_used']})")
            
            return result
            
        except Exception as e:
            print(f"   ⚠️  Erro no GPT, assumindo válido: {e}")
            return {
                'valid': True,
                'syntax_valid': True,
                'athena_compatible': True,
                'warnings': [f"Não foi possível validar com GPT: {e}"],
                'suggestions': [],
                'issues': [],
                'tokens_used': 0
            }
    
    def _estimate_costs(self, query_sql: str, gpt_validation: Dict) -> Dict[str, float]:
        """Estima custos de execução no Athena"""
        print("   💰 Estimando custos...")
        
        # Heurística simples baseada na complexidade da query
        query_upper = query_sql.upper()
        
        # Fatores de custo
        scan_size_gb = 0.1  # Base: 100 MB
        
        # Ajustes baseados na query
        if 'JOIN' in query_upper:
            scan_size_gb *= 3
        if query_upper.count('JOIN') > 2:
            scan_size_gb *= 2
        if 'GROUP BY' in query_upper:
            scan_size_gb *= 1.5
        if 'ORDER BY' in query_upper:
            scan_size_gb *= 1.2
        if 'DISTINCT' in query_upper:
            scan_size_gb *= 1.3
        if '*' in query_sql:  # SELECT *
            scan_size_gb *= 2
        
        # Custo (Athena cobra por dados escaneados)
        scan_cost_per_tb = self.athena_limits.get('scan_cost_per_tb', 5.00)
        cost_usd = (scan_size_gb / 1024) * scan_cost_per_tb
        
        # Tempo estimado (heurística)
        execution_time_seconds = 2.0
        if 'JOIN' in query_upper:
            execution_time_seconds += 5.0
        if 'GROUP BY' in query_upper:
            execution_time_seconds += 3.0
        
        warnings = gpt_validation.get('warnings', [])
        if len(warnings) > 0:
            execution_time_seconds *= 1.5
        
        print(f"   ✅ Scan estimado: {scan_size_gb:.2f} GB")
        print(f"   ✅ Custo estimado: ${cost_usd:.6f} USD")
        print(f"   ✅ Tempo estimado: {execution_time_seconds:.1f}s")
        
        return {
            'scan_size_gb': round(scan_size_gb, 2),
            'cost_usd': round(cost_usd, 6),
            'execution_time_seconds': round(execution_time_seconds, 1)
        }
    
    def _calculate_risk_level(self, cost_estimation: Dict, security_validation: Dict) -> str:
        """Calcula nível de risco da query"""
        risk_score = 0
        
        # Custo
        if cost_estimation['cost_usd'] > 0.10:
            risk_score += 2
        elif cost_estimation['cost_usd'] > 0.01:
            risk_score += 1
        
        # Tempo
        if cost_estimation['execution_time_seconds'] > 30:
            risk_score += 2
        elif cost_estimation['execution_time_seconds'] > 10:
            risk_score += 1
        
        # Scan size
        if cost_estimation['scan_size_gb'] > 10:
            risk_score += 2
        elif cost_estimation['scan_size_gb'] > 1:
            risk_score += 1
        
        # Segurança
        if security_validation.get('issues'):
            risk_score += 3
        
        if risk_score >= 5:
            return 'high'
        elif risk_score >= 3:
            return 'medium'
        else:
            return 'low'
    
    def _build_error_response(self, error_msg: str, validation: Dict, start_time: datetime, query_sql: str = '') -> Dict[str, Any]:
        """Constrói resposta de erro"""
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'valid': False,
            'query_validated': query_sql,  # Retornar query original mesmo quando inválida
            'syntax_valid': False,
            'athena_compatible': False,
            'security_issues': validation.get('issues', []),
            'warnings': [],
            'optimization_suggestions': [],
            'estimated_scan_size_gb': 0,
            'estimated_cost_usd': 0,
            'estimated_execution_time_seconds': 0,
            'risk_level': 'high',
            'tokens_used': 0,
            'model_used': self.model,
            'execution_time': execution_time,
            'error': error_msg
        }
    
    def _print_output(self, result: Dict[str, Any]):
        """Imprime resultado da validação"""
        print(f"\n{'='*80}")
        print(f"📤 OUTPUT:")
        print(f"   {'✅' if result['valid'] else '❌'} Query Válida: {result['valid']}")
        print(f"   🔍 Sintaxe: {result['syntax_valid']}")
        print(f"   ☁️  Athena Compatible: {result['athena_compatible']}")
        print(f"   🔒 Security Issues: {len(result['security_issues'])}")
        print(f"   ⚠️  Warnings: {len(result['warnings'])}")
        print(f"   💡 Sugestões: {len(result['optimization_suggestions'])}")
        print(f"   📊 Scan Estimado: {result['estimated_scan_size_gb']} GB")
        print(f"   💰 Custo Estimado: ${result['estimated_cost_usd']} USD")
        print(f"   ⏱️  Tempo Estimado: {result['estimated_execution_time_seconds']}s")
        print(f"   ⚡ Nível de Risco: {result['risk_level'].upper()}")
        print(f"   🤖 Tokens Usados: {result['tokens_used']}")
        print(f"   ⏱️  Tempo Execução: {result['execution_time']:.2f}s")
        
        if result['error']:
            print(f"   ❌ Erro: {result['error']}")
        
        print(f"{'='*80}\n")


def run_server():
    """Executa o agente em modo servidor"""
    agent = SQLValidatorAgent()
    print("🚀 SQL Validator Agent iniciado em modo servidor")
    print("   Aguardando requisições...")
    # TODO: Implementar servidor Flask/FastAPI
    import time
    while True:
        time.sleep(1)


def run_interactive():
    """Executa o agente em modo interativo"""
    agent = SQLValidatorAgent()
    
    print("\n" + "="*80)
    print("🔍 SQL VALIDATOR AGENT - MODO INTERATIVO")
    print("="*80)
    
    # Exemplo de query
    query_sql = """
    SELECT COUNT(*) AS total 
    FROM receivables_db.report_orders 
    WHERE date_parse(TRIM("contract start date"), '%Y-%m-%d %I:%i %p') >= current_date
    """
    
    result = agent.validate(
        query_sql=query_sql,
        username='test_user',
        projeto='test_project',
        estimated_complexity='baixa'
    )
    
    print("\n✅ Validação concluída!")
    print(f"   Valid: {result['valid']}")
    print(f"   Risk Level: {result['risk_level']}")
    print(f"   Cost: ${result['estimated_cost_usd']} USD")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'server':
        run_server()
    else:
        run_interactive()
