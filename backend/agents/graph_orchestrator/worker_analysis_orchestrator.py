"""
Analysis Orchestrator Worker
Worker que processa jobs da fila analysis_orchestrator
"""

import sys
import os
from pathlib import Path

# Adicionar paths
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

from agents.graph_orchestrator.graph_orchestrator import ModuleWorker
from agents.analysis_orchestrator_agent.analysis_orchestrator import AnalysisOrchestratorAgent
from typing import Dict, Any

class AnalysisOrchestratorWorker(ModuleWorker):
    """Worker para o módulo analysis_orchestrator"""
    
    def __init__(self):
        super().__init__('analysis_orchestrator')
        self.agent = AnalysisOrchestratorAgent()
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa geração de query SQL a partir de um plano
        
        Input esperado:
            - plan: str (plano gerado pelo PlanBuilder)
            - pergunta: str
            - intent_category: str
            - username: str
            - projeto: str
            - plan_confirmed: bool (se veio do PlanConfirm)
            - ... (outros campos dos módulos anteriores)
            
        Output:
            - query_sql: str
            - query_explanation: str
            - columns_used: List[str]
            - filters_applied: List[str]
            - security_validated: bool
            - optimization_notes: str
        """
        
        print(f"[ANALYSIS_ORCHESTRATOR]    🔍 Debug - Data recebido no worker:")
        print(f"[ANALYSIS_ORCHESTRATOR]       pergunta: {data.get('pergunta')}")
        print(f"[ANALYSIS_ORCHESTRATOR]       plan: {data.get('plan', '')[:100]}...")
        print(f"[ANALYSIS_ORCHESTRATOR]       intent_category: {data.get('intent_category')}")
        print(f"[ANALYSIS_ORCHESTRATOR]       plan_confirmed: {data.get('plan_confirmed')}")
        print(f"[ANALYSIS_ORCHESTRATOR]       username: {data.get('username')}")
        print(f"[ANALYSIS_ORCHESTRATOR]       projeto: {data.get('projeto')}")
        
        state = dict(data)
        
        # Gerar query SQL
        result = self.agent.generate_query(state)
        
        # Verificar se houve erro
        if result.get('error'):
            print(f"[ANALYSIS_ORCHESTRATOR]    ⚠️  Query gerada com erro: {result.get('error')}")
            security_validated = False
        else:
            print(f"[ANALYSIS_ORCHESTRATOR]    ✅ Query SQL gerada com sucesso")
            print(f"[ANALYSIS_ORCHESTRATOR]    🔒 Segurança validada: {result.get('security_validated')}")
            print(f"[ANALYSIS_ORCHESTRATOR]    📊 Query: {result.get('query_sql', '')[:150]}...")
            security_validated = result.get('security_validated', False)
        
        # Retornar resultado mantendo campos importantes
        return {
            'query_sql': result.get('query_sql', ''),
            'query_explanation': result.get('query_explanation', ''),
            'columns_used': result.get('columns_used', []),
            'filters_applied': result.get('filters_applied', []),
            'security_validated': security_validated,
            'optimization_notes': result.get('optimization_notes', ''),
            'execution_time': result.get('execution_time'),
            'error': result.get('error'),
            # Identificar módulo para history_preferences salvar
            'previous_module': 'analysis_orchestrator',
            # Manter dados para próximo módulo
            'pergunta': data.get('pergunta'),
            'username': data.get('username'),
            'projeto': data.get('projeto'),
            'intent_category': data.get('intent_category'),
            'plan': data.get('plan', ''),
            'plan_confirmed': data.get('plan_confirmed', False),
            # IMPORTANTE: Propagar campos anteriores para rastreabilidade
            'intent_valid': data.get('intent_valid'),
            'plan_steps': data.get('plan_steps', []),
            'estimated_complexity': data.get('estimated_complexity', 'média'),
            # Definir próximos módulos: sql_validator e history_preferences em paralelo
            # history salva analysis_orchestrator enquanto sql_validator valida
            '_next_modules': ['sql_validator', 'history_preferences']
        }

if __name__ == '__main__':
    worker = AnalysisOrchestratorWorker()
    worker.start()
