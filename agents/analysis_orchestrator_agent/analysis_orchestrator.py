"""
Analysis Orchestrator Agent
============================
Motor principal que transforma planos em queries SQL otimizadas para AWS Athena
"""

import os
import json
import time
from openai import OpenAI
from typing import Dict, Any, List
from pathlib import Path

class AnalysisOrchestratorAgent:
    """
    Agente responsável por transformar planos de análise em queries SQL
    otimizadas para AWS Athena, respeitando todas as regras de segurança,
    semântica e sintaxe.
    """
    
    def __init__(self):
        print("\n" + "="*80)
        print("⚙️  ANALYSIS ORCHESTRATOR AGENT - MOTOR DE GERAÇÃO DE QUERIES")
        print("="*80)
        print("✅ Agente inicializado")
        print("="*80 + "\n")
        
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"
        
        # Carregar roles (contém TUDO: schemas, instruções e funções proibidas)
        roles_path = Path(__file__).parent / "roles.json"
        with open(roles_path, 'r', encoding='utf-8') as f:
            self.roles = json.load(f)
    
    def generate_query(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma um plano de análise em uma query SQL otimizada
        
        Args:
            state: Estado contendo:
                - plan: str (plano gerado pelo PlanBuilder)
                - pergunta: str
                - intent_category: str
                - username: str
                - projeto: str
                
        Returns:
            Estado atualizado com:
                - query_sql: str (query SQL otimizada)
                - query_explanation: str
                - columns_used: List[str]
                - filters_applied: List[str]
                - security_validated: bool
                - optimization_notes: str
        """
        
        plan = state.get("plan", "")
        pergunta = state.get("pergunta", "")
        intent_category = state.get("intent_category", "unknown")
        username = state.get("username", "")
        projeto = state.get("projeto", "")
        
        # Header
        print(f"\n{'='*80}")
        print(f"[ANALYSIS_ORCHESTRATOR] ⚙️  ANALYSIS ORCHESTRATOR - GERAÇÃO DE QUERY SQL")
        print(f"{'='*80}")
        
        # Inputs
        print(f"[ANALYSIS_ORCHESTRATOR] 📥 INPUTS:")
        print(f"[ANALYSIS_ORCHESTRATOR]    📝 Pergunta: {pergunta}")
        print(f"[ANALYSIS_ORCHESTRATOR]    📋 Plano: {plan[:200]}...")
        print(f"[ANALYSIS_ORCHESTRATOR]    📂 Categoria: {intent_category}")
        print(f"[ANALYSIS_ORCHESTRATOR]    👤 Username: {username}")
        print(f"[ANALYSIS_ORCHESTRATOR]    📁 Projeto: {projeto}")
        
        print(f"\n[ANALYSIS_ORCHESTRATOR] ⚙️  PROCESSAMENTO:")
        
        start_time = time.time()
        
        try:
            # Construir prompt para o GPT
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(plan, pergunta, intent_category)
            
            print(f"[ANALYSIS_ORCHESTRATOR]    🤖 Chamando OpenAI GPT-4o...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Baixa temperatura para respostas mais determinísticas
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            execution_time = time.time() - start_time
            
            # Validar segurança da query
            security_check = self._validate_security(result.get("query_sql", ""))
            
            if not security_check["valid"]:
                print(f"[ANALYSIS_ORCHESTRATOR] ❌ FALHA DE SEGURANÇA: {security_check['reason']}")
                return {
                    **state,
                    "error": f"Query rejeitada por violação de segurança: {security_check['reason']}",
                    "security_validated": False,
                    "execution_time": execution_time
                }
            
            # Output
            print(f"\n[ANALYSIS_ORCHESTRATOR] 📤 OUTPUT:")
            print(f"[ANALYSIS_ORCHESTRATOR]    ✅ Query SQL gerada")
            print(f"[ANALYSIS_ORCHESTRATOR]    🔒 Segurança validada: {security_check['valid']}")
            print(f"[ANALYSIS_ORCHESTRATOR]    📊 Colunas usadas: {len(result.get('columns_used', []))}")
            print(f"[ANALYSIS_ORCHESTRATOR]    🎯 Filtros aplicados: {len(result.get('filters_applied', []))}")
            print(f"[ANALYSIS_ORCHESTRATOR]    ⏱️  Tempo: {execution_time:.2f}s")
            
            # Adicionar ao state
            return {
                **state,
                "query_sql": result.get("query_sql", ""),
                "query_explanation": result.get("query_explanation", ""),
                "columns_used": result.get("columns_used", []),
                "filters_applied": result.get("filters_applied", []),
                "security_validated": True,
                "optimization_notes": result.get("optimization_notes", ""),
                "execution_time": execution_time,
                "previous_module": "analysis_orchestrator"
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Erro ao gerar query: {str(e)}"
            
            print(f"[ANALYSIS_ORCHESTRATOR] ❌ ERRO: {error_msg}")
            
            return {
                **state,
                "error": error_msg,
                "execution_time": execution_time,
                "previous_module": "analysis_orchestrator"
            }
    
    def _build_system_prompt(self) -> str:
        """Constrói o prompt do sistema com todas as regras e contexto"""
        
        return f"""{self.roles['system_prompt_template']}

{json.dumps(self.roles['security_rules'], indent=2, ensure_ascii=False)}

📐 REGRAS COMPLETAS (DATABASE SCHEMA + INSTRUÇÕES + FUNÇÕES PROIBIDAS):
{json.dumps(self.roles, indent=2, ensure_ascii=False)}

✅ CHECKLIST DE VALIDAÇÃO:
Antes de retornar, verifique:
1. Query é apenas SELECT?
2. Nenhuma coluna sensível está sendo retornada?
3. Colunas com espaços têm aspas duplas?
4. Agregações têm aliases?
5. Datas usam TRY(CAST(date_parse(TRIM(...))))?
6. Filtros de data usam timezone 'America/New_York'?
7. Valores nulos tratados com COALESCE?
8. Não usa funções proibidas?
9. Tabela é receivables_db.report_orders?
10. Status values são válidos?

🔒 SEGURANÇA É PRIORIDADE MÁXIMA - NUNCA comprometa dados sensíveis!
"""
    
    def _build_user_prompt(self, plan: str, pergunta: str, intent_category: str) -> str:
        """Constrói o prompt do usuário com o plano e contexto"""
        
        return self.roles['user_prompt_template'].format(
            pergunta=pergunta,
            plan=plan,
            intent_category=intent_category
        )
    
    def _validate_security(self, query: str) -> Dict[str, Any]:
        """Valida se a query respeita as regras de segurança"""
        
        query_upper = query.upper()
        
        # Verificar operações proibidas
        for operation in self.roles['security_rules']['forbidden_operations']:
            if operation in query_upper:
                return {
                    "valid": False,
                    "reason": f"Operação proibida detectada: {operation}"
                }
        
        # Verificar colunas sensíveis
        for column in self.roles['security_rules']['forbidden_columns']:
            # Verificar se a coluna aparece no SELECT (não apenas no WHERE)
            if f'"{column}"' in query.lower() and 'select' in query_upper:
                # Verificar se não está apenas em WHERE/GROUP BY
                select_part = query.upper().split('FROM')[0] if 'FROM' in query_upper else query_upper
                if f'"{column}"'.upper() in select_part:
                    return {
                        "valid": False,
                        "reason": f"Coluna sensível detectada: {column}"
                    }
        
        # Verificar SELECT *
        if 'SELECT *' in query_upper:
            return {
                "valid": False,
                "reason": "SELECT * não é permitido"
            }
        
        # Verificar se é apenas SELECT
        if not query_upper.strip().startswith('SELECT') and not query_upper.strip().startswith('WITH'):
            return {
                "valid": False,
                "reason": "Query deve começar com SELECT ou WITH"
            }
        
        return {
            "valid": True,
            "reason": "Query passou em todas as validações de segurança"
        }
