"""
Plan Refiner Worker
Processa jobs da fila plan_refiner
"""

import sys
import os
from pathlib import Path

# Adicionar paths
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

from agents.graph_orchestrator.graph_orchestrator import ModuleWorker
from agents.plan_refiner_agent.plan_refiner import PlanRefinerAgent
from typing import Dict, Any

class PlanRefinerWorker(ModuleWorker):
    """Worker para o módulo plan_refiner"""
    
    def __init__(self):
        super().__init__('plan_refiner')
        self.agent = PlanRefinerAgent()
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa refinamento de plano baseado em sugestão do usuário
        
        Input esperado:
            - pergunta: str
            - original_plan: str (plano do PlanBuilder)
            - user_suggestion: str (do UserProposedPlan)
            - intent_category: str
            - username: str
            - projeto: str
            - plan_builder_id: UUID (parent)
            - user_proposed_plan_id: UUID (parent)
            
        Output:
            - refined_plan: str
            - refinement_summary: str
            - changes_applied: List[str]
            - user_suggestions_incorporated: List[str]
            - improvements_made: List[str]
            - validation_notes: str
            - execution_time: float
            - model_used: str
        """
        
        print(f"[PLAN_REFINER]    🔍 Debug - Data recebido no worker:")
        print(f"[PLAN_REFINER]       pergunta: {data.get('pergunta')}")
        print(f"[PLAN_REFINER]       original_plan: {data.get('original_plan', data.get('plan', ''))[:100]}...")
        print(f"[PLAN_REFINER]       user_suggestion: {data.get('user_suggestion', data.get('user_proposed_plan', ''))[:100]}...")
        print(f"[PLAN_REFINER]       intent_category: {data.get('intent_category')}")
        print(f"[PLAN_REFINER]       parent_intent_validator_id: {data.get('parent_intent_validator_id')}")
        print(f"[PLAN_REFINER]       parent_plan_builder_id: {data.get('parent_plan_builder_id')}")
        print(f"[PLAN_REFINER]       parent_user_proposed_plan_id: {data.get('parent_user_proposed_plan_id')}")
        
        # Extrair dados
        pergunta = data.get('pergunta', '')
        original_plan = data.get('original_plan', data.get('plan', ''))
        user_suggestion = data.get('user_suggestion', data.get('user_proposed_plan', ''))
        intent_category = data.get('intent_category', 'unknown')
        username = data.get('username', 'unknown')
        projeto = data.get('projeto', 'unknown')
        
        if not pergunta or not original_plan or not user_suggestion:
            return {
                'error': 'Dados insuficientes para refinamento',
                'refined_plan': original_plan,  # Fallback
                'refinement_summary': 'Erro: dados insuficientes',
                'changes_applied': [],
                'user_suggestions_incorporated': [],
                'improvements_made': [],
                'validation_notes': 'Dados insuficientes',
                'execution_time': 0.0,
                'success': False
            }
        
        # Processar com o agente (passar contexto se houver)
        result = self.agent.refine_plan(
            pergunta=pergunta,
            original_plan=original_plan,
            user_suggestion=user_suggestion,
            intent_category=intent_category,
            conversation_context=data.get('conversation_context', ''),
            has_history=data.get('has_history', False)
        )
        
        # Preparar output com todos os campos necessários
        # IMPORTANTE: O plano refinado substitui o plano original
        output = {
            'pergunta': pergunta,
            'username': username,
            'projeto': projeto,
            'previous_module': 'plan_refiner',
            'plan': result.get('refined_plan', original_plan),  # Plano refinado vira o novo "plan"
            'plan_steps': result.get('plan_steps', []),  # Passos do plano refinado
            'original_plan': original_plan,  # Mantém histórico do plano original
            'user_suggestion': user_suggestion,
            'intent_category': intent_category,
            **result,
            # Parent IDs
            'parent_plan_builder_id': data.get('parent_plan_builder_id'),
            'parent_user_proposed_plan_id': data.get('parent_user_proposed_plan_id'),
            'parent_intent_validator_id': data.get('parent_intent_validator_id'),
            # Propagar contexto para próximos módulos
            'conversation_context': data.get('conversation_context', ''),
            'has_history': data.get('has_history', False)
        }
        
        print(f"[PLAN_REFINER]    ✅ Refinamento concluído")
        print(f"[PLAN_REFINER]       Plano refinado: {len(output.get('refined_plan', ''))} chars")
        print(f"[PLAN_REFINER]       Passos: {len(output.get('plan_steps', []))}")
        print(f"[PLAN_REFINER]       Mudanças: {len(output.get('changes_applied', []))}")
        
        return output


if __name__ == "__main__":
    worker = PlanRefinerWorker()
    worker.start()
