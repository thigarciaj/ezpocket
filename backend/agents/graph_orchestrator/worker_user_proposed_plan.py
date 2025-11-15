"""
Worker: User Proposed Plan
Processa jobs da fila user_proposed_plan
"""

import sys
import os
from pathlib import Path

# Adicionar paths
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

from agents.graph_orchestrator.graph_orchestrator import ModuleWorker
from agents.user_proposed_plan_agent.user_proposed_plan import UserProposedPlanAgent
from typing import Dict, Any

class UserProposedPlanWorker(ModuleWorker):
    """Worker para o módulo user_proposed_plan"""
    
    def __init__(self):
        super().__init__('user_proposed_plan')
        self.agent = UserProposedPlanAgent()
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aguarda sugestão do usuário via Redis (interativo como plan_confirm)
        """
        import redis
        import json
        from datetime import datetime
        import time
        
        pergunta = data.get('pergunta', '')
        username = data.get('username', 'unknown')
        projeto = data.get('projeto', 'default')
        
        print(f"[USER_PROPOSED_PLAN]    💡 Aguardando sugestão do usuário via Redis...")
        
        # Conectar ao Redis
        redis_client = redis.Redis(host='localhost', port=6493, decode_responses=True)
        
        # Chaves Redis
        pending_key = f"user_proposed_plan:pending:{username}:{projeto}"
        response_key = f"user_proposed_plan:response:{username}:{projeto}"
        
        # Salvar contexto no Redis
        context_data = {
            'pergunta': pergunta,
            'username': username,
            'projeto': projeto,
            'timestamp': datetime.now().isoformat()
        }
        
        redis_client.hset(pending_key, mapping=context_data)
        redis_client.expire(pending_key, 300)  # Expira em 5 minutos
        
        print(f"[USER_PROPOSED_PLAN]    ✅ Contexto salvo no Redis: {pending_key}")
        print(f"[USER_PROPOSED_PLAN]    ⏳ Aguardando sugestão do usuário (máx 5 min)...")
        
        # Aguardar resposta por até 5 minutos
        timeout = 300
        start = time.time()
        
        while (time.time() - start) < timeout:
            response = redis_client.get(response_key)
            if response:
                user_suggestion = response
                
                # Limpar Redis
                redis_client.delete(pending_key)
                redis_client.delete(response_key)
                
                print(f"[USER_PROPOSED_PLAN]    ✅ Sugestão recebida!")
                print(f"[USER_PROPOSED_PLAN]    💬 Sugestão: {user_suggestion[:100]}...")
                
                # Retornar para plan_builder com a sugestão como "plan"
                wait_time = time.time() - start
                return {
                    'user_proposed_plan': user_suggestion,
                    'user_suggestion': user_suggestion,  # Para plan_refiner
                    'plan': data.get('plan', ''),  # Plano rejeitado anterior
                    'original_plan': data.get('plan', ''),  # Para plan_refiner
                    'plan_received': True,
                    'received_at': datetime.now().isoformat(),
                    'input_method': 'interactive',
                    'wait_time': wait_time,
                    'previous_module': 'user_proposed_plan',
                    'pergunta': pergunta,
                    'username': username,
                    'projeto': projeto,
                    'intent_category': data.get('intent_category'),
                    'execution_time': wait_time,
                    # Parent IDs - propagar do PlanConfirm/PlanBuilder
                    'parent_intent_validator_id': data.get('parent_intent_validator_id'),
                    'parent_plan_builder_id': data.get('parent_plan_builder_id'),
                    'parent_user_proposed_plan_id': None  # Será preenchido pelo History
                }
            
            time.sleep(0.5)
        
        # Timeout
        redis_client.delete(pending_key)
        
        print(f"[USER_PROPOSED_PLAN]    ⏱️  TIMEOUT - Usuário não forneceu sugestão")
        
        return {
            'user_proposed_plan': '',
            'plan': data.get('plan', ''),  # Plano rejeitado anterior
            'plan_received': False,
            'received_at': datetime.now().isoformat(),
            'input_method': 'timeout',
            'wait_time': timeout,
            'timeout_occurred': True,
            'error': True,
            'error_message': 'Timeout aguardando sugestão do usuário',
            'previous_module': 'user_proposed_plan',
            'pergunta': pergunta,
            'username': username,
            'projeto': projeto,
            'intent_category': data.get('intent_category'),
            'execution_time': timeout
        }

if __name__ == '__main__':
    worker = UserProposedPlanWorker()
    worker.start()
