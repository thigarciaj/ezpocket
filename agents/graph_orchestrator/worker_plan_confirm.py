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
        redis_port = int(os.getenv('REDIS_PORT', 6493))
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        
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
            # VERIFICAR SE A CHAVE PENDENTE AINDA EXISTE (pode ter sido apagada no disconnect)
            if not redis_client.exists(pending_key):
                print(f"[PLAN_CONFIRM]    🚫 Chave pendente foi removida (usuário desconectou) - cancelando espera")
                # Retornar resultado neutro para não criar jobs subsequentes
                return {
                    'pergunta': pergunta,
                    'username': username,
                    'projeto': projeto,
                    'previous_module': 'plan_confirm',
                    'confirmed': False,
                    'cancelled': True,
                    'cancel_reason': 'user_disconnected',
                    '_next_modules': []  # Não criar próximos módulos
                }
            
            response = redis_client.get(response_key)
            if response:
                print(f"[PLAN_CONFIRM]    🔍 DEBUG - Resposta bruta do Redis: '{response}' (tipo: {type(response)})")
                print(f"[PLAN_CONFIRM]    🔍 DEBUG - response.lower(): '{response.lower()}'")
                print(f"[PLAN_CONFIRM]    🔍 DEBUG - response.strip(): '{response.strip()}'")
                
                confirmed = response.strip().lower() in ['true', 'yes', 's', 'sim', '1']
                
                print(f"[PLAN_CONFIRM]    🔍 DEBUG - confirmed final: {confirmed}")
                
                # Limpar Redis
                redis_client.delete(pending_key)
                redis_client.delete(response_key)
                
                print(f"[PLAN_CONFIRM]    ✅ Resposta recebida: {'APROVADO' if confirmed else 'REJEITADO'}")
                
                # Log será salvo automaticamente pelo History Preferences Agent
                
                # LÓGICA CONDICIONAL:
                # Se ACEITO (SIM) → [analysis_orchestrator, history_preferences] (2 paralelos)
                # Se REJEITADO (NÃO) → [user_proposed_plan, history_preferences] (2 paralelos)
                next_modules = ['analysis_orchestrator', 'history_preferences'] if confirmed else ['user_proposed_plan', 'history_preferences']
                
                print(f"[PLAN_CONFIRM]    ❗ DEBUG:")
                print(f"[PLAN_CONFIRM]       confirmed = {confirmed}")
                print(f"[PLAN_CONFIRM]       Ramo escolhido: {'ACEITO (analysis_orchestrator)' if confirmed else 'REJEITADO (user_proposed_plan)'}")
                print(f"[PLAN_CONFIRM]    🔀 Próximos módulos definidos: {next_modules}")
                
                output = {
                    'pergunta': pergunta,
                    'username': username,
                    'projeto': projeto,
                    'previous_module': 'plan_confirm',
                    'confirmed': confirmed,
                    'confirmation_method': 'interactive',
                    'confirmation_time': datetime.now().isoformat(),
                    'user_feedback': 'Plano aprovado' if confirmed else 'Plano rejeitado',
                    'plan_accepted': confirmed,
                    # Manter dados do plano para o history salvar
                    'plan': plan,
                    'plan_steps': plan_steps,
                    'estimated_complexity': data.get('estimated_complexity', 'média'),
                    'execution_time': time.time() - start,
                    '_next_modules': next_modules,
                    # Parent IDs para propagar
                    'parent_intent_validator_id': data.get('intent_validator_id'),
                    'parent_plan_builder_id': data.get('parent_id'),
                    'intent_category': data.get('intent_category')
                }
                
                print(f"[PLAN_CONFIRM]    ✅ Output contém '_next_modules': {'_next_modules' in output}")
                print(f"[PLAN_CONFIRM]    ✅ Valor de '_next_modules': {output.get('_next_modules')}")
                
                return output
            
            time.sleep(0.5)
        
        # Timeout
        redis_client.delete(pending_key)
        
        print(f"[PLAN_CONFIRM]    ⏱️  TIMEOUT - Rejeitando automaticamente")
        
        # Log será salvo automaticamente pelo History Preferences Agent
        
        output = {
            'pergunta': pergunta,
            'username': username,
            'projeto': projeto,
            'previous_module': 'plan_confirm',
            'confirmed': False,
            'confirmation_method': 'timeout',
            'confirmation_time': datetime.now().isoformat(),
            'user_feedback': 'Timeout - sem resposta do usuário',
            # Parent IDs para propagar
            'parent_intent_validator_id': data.get('intent_validator_id'),
            'parent_plan_builder_id': data.get('parent_id'),
            'intent_category': data.get('intent_category'),
            'plan_accepted': False,
            # Manter dados do plano para o history salvar
            'plan': plan,
            'plan_steps': plan_steps,
            'estimated_complexity': data.get('estimated_complexity', 'média'),
            'execution_time': timeout,
            'error_message': 'Timeout aguardando confirmação do usuário',
            # LÓGICA CONDICIONAL: Timeout = rejeitado, vai para user_proposed_plan
            '_next_modules': ['user_proposed_plan', 'history_preferences']
        }
        
        print(f"[PLAN_CONFIRM]    🔀 Próximos módulos (timeout): {output['_next_modules']}")
        
        return output


if __name__ == '__main__':
    worker = PlanConfirmWorker()
    worker.start()
