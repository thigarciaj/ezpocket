#!/usr/bin/env python3
"""
Worker para Plan Confirm Agent
"""

import sys
import os
from pathlib import Path

# Adicionar paths
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

from agents.graph_orchestrator.graph_orchestrator import ModuleWorker
from agents.plan_confirm_agent.plan_confirm import PlanConfirmAgent
from typing import Dict, Any

class PlanConfirmWorker(ModuleWorker):
    """Worker para o módulo plan_confirm"""
    
    def __init__(self):
        super().__init__('plan_confirm')
        self.agent = PlanConfirmAgent()
        print(f"✅ Plan Confirm Agent carregado")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa solicitação de confirmação do plano
        
        Input esperado:
            - pergunta: str
            - plan: str  
            - plan_steps: list
            - estimated_complexity: str
            - username: str
            - projeto: str
            
        Output:
            - confirmed: bool
            - confirmation_method: str
            - confirmation_time: str
            - user_feedback: str
            - plan_accepted: bool
        """
        import redis
        import json
        from datetime import datetime
        import time
        
        pergunta = data.get('pergunta', '')
        plan = data.get('plan', '')
        plan_steps = data.get('plan_steps', [])
        username = data.get('username', 'unknown')
        projeto = data.get('projeto', 'default')
        
        print(f"[PLAN_CONFIRM]    🔍 Plano recebido - Salvando no Redis...")
        
        # Conectar ao Redis
        redis_client = redis.Redis(host='localhost', port=6493, decode_responses=True)
        
        # Chaves Redis
        pending_key = f"plan_confirm:pending:{username}:{projeto}"
        response_key = f"plan_confirm:response:{username}:{projeto}"
        
        # Salvar plano no Redis
        plan_data = {
            'pergunta': pergunta,
            'plan': plan,
            'plan_steps': json.dumps(plan_steps),
            'username': username,
            'projeto': projeto,
            'timestamp': datetime.now().isoformat()
        }
        
        redis_client.hset(pending_key, mapping=plan_data)
        redis_client.expire(pending_key, 300)  # Expira em 5 minutos
        
        print(f"[PLAN_CONFIRM]    ✅ Plano salvo no Redis: {pending_key}")
        print(f"[PLAN_CONFIRM]    ⏳ Aguardando resposta do usuário (máx 5 min)...")
        
        # Aguardar resposta do test_client por até 5 minutos
        timeout = 300
        start = time.time()
        
        while (time.time() - start) < timeout:
            response = redis_client.get(response_key)
            if response:
                confirmed = response.lower() in ['true', 'yes', 's', 'sim', '1']
                
                # Limpar Redis
                redis_client.delete(pending_key)
                redis_client.delete(response_key)
                
                print(f"[PLAN_CONFIRM]    ✅ Resposta recebida: {'APROVADO' if confirmed else 'REJEITADO'}")
                
                output = {
                    'pergunta': pergunta,
                    'username': username,
                    'projeto': projeto,
                    'previous_module': 'plan_confirm',
                    'confirmed': confirmed,
                    'confirmation_method': 'interactive',
                    'confirmation_time': datetime.now().isoformat(),
                    'user_feedback': 'Plano aprovado' if confirmed else 'Plano rejeitado',
                    'plan_accepted': confirmed
                }
                
                return output
            
            time.sleep(0.5)
        
        # Timeout
        redis_client.delete(pending_key)
        
        print(f"[PLAN_CONFIRM]    ⏱️  TIMEOUT - Rejeitando automaticamente")
        
        output = {
            'pergunta': pergunta,
            'username': username,
            'projeto': projeto,
            'previous_module': 'plan_confirm',
            'confirmed': False,
            'confirmation_method': 'timeout',
            'confirmation_time': datetime.now().isoformat(),
            'user_feedback': 'Timeout - sem resposta do usuário',
            'plan_accepted': False
        }
        
        return output


if __name__ == '__main__':
    worker = PlanConfirmWorker()
    worker.start()
