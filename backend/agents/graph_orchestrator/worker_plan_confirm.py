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
                
                # Salvar no banco de dados
                self._save_to_database(
                    username=username,
                    projeto=projeto,
                    pergunta=pergunta,
                    plan=plan,
                    plan_steps=plan_steps,
                    estimated_complexity=data.get('estimated_complexity', 'média'),
                    confirmed=confirmed,
                    confirmation_method='interactive',
                    user_feedback='Plano aprovado' if confirmed else 'Plano rejeitado',
                    plan_accepted=confirmed,
                    execution_time=time.time() - start,
                    success=True,
                    parent_plan_builder_id=data.get('parent_id'),
                    parent_intent_validator_id=data.get('intent_validator_id')
                )
                
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
        
        # Salvar no banco com timeout
        self._save_to_database(
            username=username,
            projeto=projeto,
            pergunta=pergunta,
            plan=plan,
            plan_steps=plan_steps,
            estimated_complexity=data.get('estimated_complexity', 'média'),
            confirmed=False,
            confirmation_method='timeout',
            user_feedback='Timeout - sem resposta do usuário',
            plan_accepted=False,
            execution_time=timeout,
            success=False,
            error_message='Timeout aguardando confirmação do usuário',
            parent_plan_builder_id=data.get('parent_id'),
            parent_intent_validator_id=data.get('intent_validator_id')
        )
        
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
    
    def _save_to_database(self, **kwargs):
        """Salva log no banco de dados PostgreSQL"""
        import psycopg2
        from psycopg2.extras import Json
        from datetime import datetime
        
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=5433,
                database='ezpagdb',
                user='ezpag_user',
                password='ezpag2024'
            )
            
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO plan_confirm_logs (
                    username, projeto, pergunta, plan, plan_steps,
                    estimated_complexity, confirmed, confirmation_method,
                    confirmation_time, user_feedback, plan_accepted,
                    execution_time, success, error_message,
                    parent_plan_builder_id, parent_intent_validator_id
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s
                )
            """, (
                kwargs.get('username'),
                kwargs.get('projeto'),
                kwargs.get('pergunta'),
                kwargs.get('plan'),
                kwargs.get('plan_steps'),
                kwargs.get('estimated_complexity'),
                kwargs.get('confirmed'),
                kwargs.get('confirmation_method'),
                datetime.now(),
                kwargs.get('user_feedback'),
                kwargs.get('plan_accepted'),
                kwargs.get('execution_time'),
                kwargs.get('success', True),
                kwargs.get('error_message'),
                kwargs.get('parent_plan_builder_id'),
                kwargs.get('parent_intent_validator_id')
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"[PLAN_CONFIRM]    💾 Salvo no banco de dados com sucesso")
            
        except Exception as e:
            print(f"[PLAN_CONFIRM]    ❌ Erro ao salvar no banco: {e}")


if __name__ == '__main__':
    worker = PlanConfirmWorker()
    worker.start()
