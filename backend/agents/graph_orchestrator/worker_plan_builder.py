"""
Plan Builder Worker
Worker que processa jobs da fila plan_builder
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any
from graph_orchestrator.graph_orchestrator import ModuleWorker
from agents.plan_builder_agent import PlanBuilderAgent

class PlanBuilderWorker(ModuleWorker):
    """Worker para o módulo plan_builder"""
    
    def __init__(self):
        super().__init__('plan_builder')
        self.agent = PlanBuilderAgent()
        print(f"✅ Plan Builder Agent carregado")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa geração de plano
        
        Input esperado:
            - pergunta: str
            - intent_category: str
            - username: str
            - projeto: str
            - intent_valid: bool
            - ... (outros campos do intent_validator)
            
        Output:
            - plan: str
            - plan_steps: list
            - estimated_complexity: str
            - data_sources: list
            - output_format: str
        """
        
        print(f"   🔍 Debug - Data recebido no worker:")
        print(f"      pergunta: {data.get('pergunta')}")
        print(f"      intent_category: {data.get('intent_category')}")
        print(f"      username: {data.get('username')}")
        print(f"      projeto: {data.get('projeto')}")
        
        # IMPORTANTE: Usar TODO o data como state
        state = dict(data)
        
        # Gerar plano
        result = self.agent.build_plan(state)
        
        # Verificar se houve erro
        if result.get('error_message'):
            print(f"   ⚠️  Plano gerado com erro: {result.get('error_message')}")
        
        # Retornar resultado mantendo campos importantes
        return {
            'plan': result.get('plan', ''),
            'plan_steps': result.get('plan_steps', []),
            'estimated_complexity': result.get('estimated_complexity', 'média'),
            'data_sources': result.get('data_sources', []),
            'output_format': result.get('output_format', 'texto'),
            'tokens_used': result.get('tokens_used'),
            'model_used': result.get('model_used', 'gpt-4o'),
            'error_message': result.get('error_message'),
            # Identificar módulo para history_preferences salvar
            'previous_module': 'plan_builder',
            # Manter dados para próximo módulo
            'pergunta': data.get('pergunta'),
            'username': data.get('username'),
            'projeto': data.get('projeto'),
            'intent_category': data.get('intent_category')
        }

if __name__ == '__main__':
    worker = PlanBuilderWorker()
    worker.start()
