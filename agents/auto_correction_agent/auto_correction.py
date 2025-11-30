#!/usr/bin/env python3
"""
Auto Correction Agent - Corrige queries SQL inválidas para AWS Athena
Corrige sintaxe, nomes de colunas, funções incompatíveis
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Adicionar paths necessários
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

from openai import OpenAI

class AutoCorrectionAgent:
    """
    Corrige queries SQL inválidas para AWS Athena
    - Corrige sintaxe SQL
    - Ajusta nomes de colunas incorretos
    - Substitui funções incompatíveis
    - Adapta para Presto SQL (Athena)
    - Explica as correções aplicadas
    """
    
    def __init__(self):
        """Inicializa o agente"""
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.roles = self._load_roles()
        self.model = 'gpt-4o'
        
        # Carregar regras de correção do roles.json
        self.athena_rules = self.roles.get('athena_rules', {})
        self.schema_rules = self.roles.get('schema_rules', {})
        self.correction_strategies = self.roles.get('correction_strategies', {})
        
        print("\n" + "="*80)
        print("🔧 AUTO CORRECTION AGENT - INITIALIZED")
        print("="*80)
    
    def _load_roles(self) -> Dict:
        """Carrega regras de correção do roles.json ou roles_local.json"""
        # Carregar .env para verificar BD_REFERENCE
        from dotenv import load_dotenv
        project_env = Path(__file__).parent.parent.parent / ".env"
        load_dotenv(project_env)
        
        # Verificar qual roles usar baseado em BD_REFERENCE
        bd_reference = os.getenv("BD_REFERENCE", "Athena")
        
        if bd_reference == "Local":
            roles_file = "roles_local.json"
            print(f"   🔧 Auto Correction usando roles_local.json (PostgreSQL 15)")
        else:
            roles_file = "roles.json"
            print(f"   🔧 Auto Correction usando roles.json (AWS Athena)")
        
        roles_path = Path(__file__).parent / roles_file
        with open(roles_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def correct(self,
                query_original: str,
                validation_issues: List[str],
                username: str,
                projeto: str,
                schema_context: Dict[str, Any] = None,
                conversation_context: str = "",
                has_history: bool = False) -> Dict[str, Any]:
        """
        Corrige query SQL inválida
        
        Args:
            query_original: Query SQL original (inválida)
            validation_issues: Lista de problemas encontrados pelo SQL Validator
            username: Usuário que solicitou
            projeto: Projeto do usuário
            schema_context: Contexto do schema da tabela (opcional)
            
        Returns:
            Dict com resultado da correção
        """
        print(f"\n{'='*80}")
        print(f"🔧 AUTO CORRECTION AGENT - CORREÇÃO DE QUERY")
        print(f"{'='*80}")
        print(f"📥 INPUTS:")
        print(f"   👤 Username: {username}")
        print(f"   📁 Projeto: {projeto}")
        print(f"   ⚠️  Issues: {len(validation_issues)} problemas detectados")
        print(f"   📝 Query Original (primeiros 200 chars): {query_original[:200]}...")
        print(f"{'='*80}\n")
        
        start_time = datetime.now()
        
        try:
            # 1. Análise dos problemas
            print("⚙️  PROCESSAMENTO:")
            print("   🔍 Analisando problemas...")
            
            corrections_needed = self._analyze_issues(validation_issues)
            print(f"   ✅ {len(corrections_needed)} tipos de correção identificados")
            
            # 2. Aplicar correções automáticas (regras fixas)
            query_corrected, auto_corrections = self._apply_automatic_corrections(
                query_original, 
                corrections_needed
            )
            print(f"   ✅ Correções automáticas aplicadas: {len(auto_corrections)}")
            
            # 3. Correção com GPT-4o (semântica complexa)
            gpt_result = self._gpt_correction(
                query_original=query_original,
                query_auto_corrected=query_corrected,
                validation_issues=validation_issues,
                schema_context=schema_context
            )
            
            query_final = gpt_result.get('query_corrected', query_corrected)
            gpt_corrections = gpt_result.get('corrections_applied', [])
            
            print(f"   ✅ Correções GPT aplicadas: {len(gpt_corrections)}")
            
            # 4. Consolidar resultado
            execution_time = (datetime.now() - start_time).total_seconds()
            
            all_corrections = auto_corrections + gpt_corrections
            
            result = {
                'success': True,
                'query_original': query_original,
                'query_corrected': query_final,
                'corrections_applied': all_corrections,
                'corrections_count': len(all_corrections),
                'correction_explanation': gpt_result.get('explanation', ''),
                'changes_summary': self._generate_changes_summary(all_corrections),
                'tokens_used': gpt_result.get('tokens_used', 0),
                'model_used': self.model,
                'execution_time': execution_time,
                'error': None
            }
            
            self._print_output(result)
            
            return result
            
        except Exception as e:
            error_msg = f"Erro na correção: {str(e)}"
            print(f"❌ {error_msg}")
            return self._build_error_response(error_msg, start_time)
    
    def _analyze_issues(self, validation_issues: List[str]) -> List[str]:
        """Analisa problemas e identifica tipos de correção necessários"""
        corrections_needed = []
        
        for issue in validation_issues:
            issue_lower = issue.lower()
            
            # Operações proibidas
            if 'operação proibida' in issue_lower or 'forbidden' in issue_lower:
                corrections_needed.append('remove_forbidden_operation')
            
            # Sintaxe incorreta
            if 'sintaxe' in issue_lower or 'syntax' in issue_lower:
                corrections_needed.append('fix_syntax')
            
            # Funções incompatíveis
            if 'função' in issue_lower or 'function' in issue_lower:
                corrections_needed.append('replace_incompatible_function')
            
            # Colunas inválidas
            if 'coluna' in issue_lower or 'column' in issue_lower:
                corrections_needed.append('fix_column_name')
            
            # SQL injection
            if 'injection' in issue_lower or 'múltiplas queries' in issue_lower:
                corrections_needed.append('remove_injection_patterns')
        
        return list(set(corrections_needed))  # Remove duplicatas
    
    def _apply_automatic_corrections(self, query: str, corrections_needed: List[str]) -> tuple:
        """Aplica correções automáticas baseadas em regras fixas"""
        corrected_query = query
        applied_corrections = []
        
        for correction_type in corrections_needed:
            if correction_type == 'remove_forbidden_operation':
                # Remove operações proibidas (INSERT, UPDATE, DELETE, DROP)
                forbidden_ops = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'TRUNCATE']
                for op in forbidden_ops:
                    if re.search(rf'\b{op}\b', corrected_query, re.IGNORECASE):
                        # Comentar operação proibida
                        corrected_query = re.sub(
                            rf'\b{op}\b',
                            f'-- {op} (REMOVIDO)',
                            corrected_query,
                            flags=re.IGNORECASE
                        )
                        applied_corrections.append(f"Removida operação proibida: {op}")
            
            elif correction_type == 'remove_injection_patterns':
                # Remove múltiplas queries (SQL injection)
                if ';' in corrected_query:
                    # Manter apenas primeira query
                    corrected_query = corrected_query.split(';')[0]
                    applied_corrections.append("Removidas múltiplas queries (SQL injection)")
                
                # Remove comentários suspeitos
                corrected_query = re.sub(r'--.*$', '', corrected_query, flags=re.MULTILINE)
                corrected_query = re.sub(r'/\*.*?\*/', '', corrected_query, flags=re.DOTALL)
                if '--' in query or '/*' in query:
                    applied_corrections.append("Removidos comentários SQL suspeitos")
            
            elif correction_type == 'replace_incompatible_function':
                # Substituir funções incompatíveis com Athena
                function_replacements = self.athena_rules.get('function_replacements', {})
                for old_func, new_func in function_replacements.items():
                    if re.search(rf'\b{old_func}\b', corrected_query, re.IGNORECASE):
                        corrected_query = re.sub(
                            rf'\b{old_func}\b',
                            new_func,
                            corrected_query,
                            flags=re.IGNORECASE
                        )
                        applied_corrections.append(f"Função substituída: {old_func} → {new_func}")
        
        return corrected_query, applied_corrections
    
    def _gpt_correction(self,
                       query_original: str,
                       query_auto_corrected: str,
                       validation_issues: List[str],
                       schema_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Correção com GPT-4o para ajustes semânticos complexos"""
        print("   🤖 Corrigindo com GPT-4o...")
        
        # Preparar contexto do schema
        schema_info = ""
        if schema_context:
            schema_info = f"""
**Schema da Tabela:**
- Colunas disponíveis: {', '.join(schema_context.get('columns', []))}
- Tipos de dados: {json.dumps(schema_context.get('column_types', {}), indent=2)}
"""
        
        issues_text = "\n".join([f"- {issue}" for issue in validation_issues])
        
        # Adicionar contexto de conversa se houver
        context_section = ""
        if has_history and conversation_context:
            context_section = f"{conversation_context}\n\n"
        
        base_prompt = self.roles['gpt_correction_prompt_intro'].format(
            query_original=query_original,
            query_auto_corrected=query_auto_corrected,
            issues_text=issues_text,
            schema_info=schema_info,
            athena_rules=self.roles['gpt_correction_athena_rules'].format(
                supported_functions=', '.join(self.athena_rules.get('supported_functions', [])[:20])
            )
        )
        
        prompt = f"{context_section}{base_prompt}"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.roles['system_role']},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extrair JSON do response
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            result = json.loads(content)
            result['tokens_used'] = response.usage.total_tokens
            
            print(f"   ✅ Correção GPT concluída (tokens: {result['tokens_used']})")
            
            return result
            
        except Exception as e:
            print(f"   ⚠️  Erro no GPT, usando correção automática: {e}")
            return {
                'query_corrected': query_auto_corrected,
                'corrections_applied': [f"Correção GPT falhou: {e}"],
                'explanation': "Usando apenas correções automáticas",
                'confidence': 0.5,
                'tokens_used': 0
            }
    
    def _generate_changes_summary(self, corrections: List[str]) -> str:
        """Gera resumo das mudanças aplicadas"""
        if not corrections:
            return "Nenhuma correção aplicada"
        
        summary = f"{len(corrections)} correções aplicadas:\n"
        for i, correction in enumerate(corrections, 1):
            summary += f"{i}. {correction}\n"
        
        return summary.strip()
    
    def _build_error_response(self, error_msg: str, start_time: datetime) -> Dict[str, Any]:
        """Constrói resposta de erro"""
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'success': False,
            'query_original': None,
            'query_corrected': None,
            'corrections_applied': [],
            'corrections_count': 0,
            'correction_explanation': '',
            'changes_summary': '',
            'tokens_used': 0,
            'model_used': self.model,
            'execution_time': execution_time,
            'error': error_msg
        }
    
    def _print_output(self, result: Dict[str, Any]):
        """Imprime resultado da correção"""
        print(f"\n{'='*80}")
        print(f"📤 OUTPUT:")
        print(f"   {'✅' if result['success'] else '❌'} Success: {result['success']}")
        print(f"   🔧 Correções Aplicadas: {result['corrections_count']}")
        print(f"   📝 Query Original (100 chars): {result['query_original'][:100]}...")
        print(f"   ✨ Query Corrigida (100 chars): {result['query_corrected'][:100]}...")
        print(f"   💡 Explicação: {result['correction_explanation'][:150]}...")
        print(f"   🤖 Tokens Usados: {result['tokens_used']}")
        print(f"   ⏱️  Tempo Execução: {result['execution_time']:.2f}s")
        
        if result['corrections_applied']:
            print(f"\n   📋 Mudanças:")
            for correction in result['corrections_applied'][:5]:  # Mostrar primeiras 5
                print(f"      • {correction}")
            if len(result['corrections_applied']) > 5:
                print(f"      • ... e mais {len(result['corrections_applied']) - 5} correções")
        
        if result['error']:
            print(f"   ❌ Erro: {result['error']}")
        
        print(f"{'='*80}\n")


def run_server():
    """Executa o agente em modo servidor"""
    agent = AutoCorrectionAgent()
    print("🚀 Auto Correction Agent iniciado em modo servidor")
    print("   Aguardando requisições...")
    import time
    while True:
        time.sleep(1)


def run_interactive():
    """Executa o agente em modo interativo"""
    agent = AutoCorrectionAgent()
    
    print("\n" + "="*80)
    print("🔧 AUTO CORRECTION AGENT - MODO INTERATIVO")
    print("="*80)
    
    # Exemplo de query inválida
    query_invalid = """
    INSERT INTO orders (id, amount) VALUES (1, 100);
    SELECT * FROM orders WHERE cpf = '12345678900'
    """
    
    validation_issues = [
        "Operação proibida detectada: INSERT",
        "🔒 ACESSO NEGADO: Coluna sensível detectada 'cpf'",
        "Múltiplas queries detectadas (não permitido)"
    ]
    
    result = agent.correct(
        query_original=query_invalid,
        validation_issues=validation_issues,
        username='test_user',
        projeto='test_project'
    )
    
    print("\n✅ Correção concluída!")
    print(f"   Success: {result['success']}")
    print(f"   Correções: {result['corrections_count']}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'server':
        run_server()
    else:
        run_interactive()
