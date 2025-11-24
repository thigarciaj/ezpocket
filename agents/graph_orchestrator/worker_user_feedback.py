#!/usr/bin/env python3
"""
Worker para User Feedback Agent
Processa feedback do usuário sobre as respostas
"""

import sys
import os
import time
from pathlib import Path

# Adicionar paths
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

from agents.graph_orchestrator.graph_orchestrator import ModuleWorker
from agents.user_feedback_agent.user_feedback import UserFeedbackAgent
from typing import Dict, Any

class UserFeedbackWorker(ModuleWorker):
    """Worker para o módulo user_feedback"""
    
    def __init__(self):
        super().__init__('user_feedback')
        self.agent = UserFeedbackAgent()
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa feedback do usuário
        
        Input esperado:
            - pergunta: str
            - username: str
            - projeto: str
            - response_text: str (resposta apresentada ao usuário)
            - rating: int (1-5)
            - comment: str (opcional)
            - is_helpful: bool
            - response_quality: str (poor/fair/good/excellent)
            - user_satisfaction: str (unsatisfied/neutral/satisfied/very_satisfied)
            - would_recommend: bool
            - feedback_tags: List[str]
            - parent_response_composer_id: UUID (será buscado pelo history)
            
        Output:
            - feedback_recorded: bool
            - feedback_summary: str
            - positive_aspects: list
            - improvement_areas: list
            - sentiment: str
            - _next_modules: ['history_preferences']
        """
        
        # Extrair dados do input
        pergunta = data.get('pergunta', '')
        username = data.get('username', 'unknown')
        projeto = data.get('projeto', 'default')
        rating = data.get('rating', 0)
        
        print(f"[USER_FEEDBACK] 📊 Buscando resposta do banco para mostrar ao usuário...")
        
        # Buscar input/output do banco (response_composer_logs)
        response_text = ""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=int(os.getenv('POSTGRES_PORT', 5546)),
                database=os.getenv('POSTGRES_DB', 'ezpocket_logs'),
                user=os.getenv('POSTGRES_USER', 'ezpocket_user'),
                password=os.getenv('POSTGRES_PASSWORD', 'ezpocket_pass_2025')
            )
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT response_text, pergunta
                FROM response_composer_logs
                WHERE username = %s AND projeto = %s AND pergunta = %s
                ORDER BY horario DESC LIMIT 1
            """, (username, projeto, pergunta))
            result = cursor.fetchone()
            
            if result:
                response_text = result[0]
                print(f"[USER_FEEDBACK] ✅ Resposta encontrada no banco!")
            else:
                response_text = "(Resposta não encontrada)"
                print(f"[USER_FEEDBACK] ⚠️  Resposta não encontrada no banco")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"[USER_FEEDBACK] ❌ Erro ao buscar do banco: {e}")
            response_text = "(Erro ao buscar resposta)"
        
        # Se rating não foi fornecido, criar pending no Redis para aguardar input
        if not rating or rating <= 0:
            print(f"[USER_FEEDBACK] 📝 Criando pending no Redis...")
            
            import redis
            import os
            from dotenv import load_dotenv
            import json
            
            load_dotenv()
            REDIS_PORT = int(os.getenv('REDIS_PORT', 6493))
            r = redis.Redis(host='localhost', port=REDIS_PORT, decode_responses=True)
            
            feedback_key = f"user_feedback:pending:{username}:{projeto}"
            feedback_response_key = f"user_feedback:response:{username}:{projeto}"
            
            # Salvar dados do feedback no Redis
            r.hset(feedback_key, mapping={
                'pergunta': pergunta,
                'response_text': response_text,
                'username': username,
                'projeto': projeto
            })
            r.expire(feedback_key, 300)  # 5 minutos
            
            print(f"[USER_FEEDBACK] ⏳ Aguardando resposta do usuário...")
            
            # Aguardar resposta (timeout 5 minutos)
            comment = ''
            for _ in range(300):
                if r.exists(feedback_response_key):
                    feedback_response = json.loads(r.get(feedback_response_key))
                    rating = feedback_response.get('rating', 3)
                    comment = feedback_response.get('comment', '')
                    print(f"[USER_FEEDBACK] ✅ Resposta recebida: rating={rating}")
                    
                    # Limpar chaves
                    r.delete(feedback_key)
                    r.delete(feedback_response_key)
                    break
                time.sleep(1)
            else:
                # Timeout - usar rating padrão
                print(f"[USER_FEEDBACK] ⏱️  Timeout - usando rating padrão (3)")
                rating = 3
                comment = ''
                r.delete(feedback_key)
        else:
            # Rating já foi fornecido no input
            comment = data.get('comment', '')
        
        # Atualizar data com o rating e response_text
        data['rating'] = rating
        data['response_text'] = response_text
        data['comment'] = comment
        data['is_helpful'] = rating >= 3
        data['would_recommend'] = rating >= 4
        
        print(f"[USER_FEEDBACK] 📊 Processando feedback do usuário...")
        print(f"[USER_FEEDBACK]    Username: {username}")
        print(f"[USER_FEEDBACK]    Projeto: {projeto}")
        print(f"[USER_FEEDBACK]    Pergunta: {pergunta[:50]}...")
        print(f"[USER_FEEDBACK]    Rating: {rating}/5 ⭐")
        
        # Medir tempo de execução
        start_time = time.time()
        
        # Executar processamento - passar data completo como state
        result = self.agent.execute(data)
        
        execution_time = time.time() - start_time
        
        print(f"[USER_FEEDBACK] ✅ Feedback processado!")
        print(f"[USER_FEEDBACK]    Útil: {'Sim ✓' if result.get('is_helpful') else 'Não ✗'}")
        print(f"[USER_FEEDBACK]    Sentiment: {result.get('sentiment', 'neutral')}")
        print(f"[USER_FEEDBACK]    Aspectos positivos: {len(result.get('positive_aspects', []))}")
        print(f"[USER_FEEDBACK]    Áreas de melhoria: {len(result.get('improvement_areas', []))}")
        print(f"[USER_FEEDBACK]    Tempo de execução: {execution_time:.2f}s")
        
        # Preparar output - History vai buscar todos os parent_ids
        output = {
            'previous_module': 'user_feedback',
            'pergunta': pergunta,
            'username': username,
            'projeto': projeto,
            # Repassar TODOS os parent_ids recebidos
            'parent_response_composer_id': data.get('parent_response_composer_id'),
            'parent_python_runtime_id': data.get('parent_python_runtime_id'),
            'parent_athena_executor_id': data.get('parent_athena_executor_id'),
            'parent_auto_correction_id': data.get('parent_auto_correction_id'),
            'parent_sql_validator_id': data.get('parent_sql_validator_id'),
            'parent_analysis_orchestrator_id': data.get('parent_analysis_orchestrator_id'),
            'parent_plan_confirm_id': data.get('parent_plan_confirm_id'),
            'parent_plan_builder_id': data.get('parent_plan_builder_id'),
            'parent_intent_validator_id': data.get('parent_intent_validator_id'),
            # Resultados do feedback
            **result,
            # Tempo de execução
            'execution_time': execution_time,
            # Próximo módulo: history_preferences (salvar feedback)
            '_next_modules': ['history_preferences']
        }
        
        print(f"[USER_FEEDBACK] 🔀 Enviando feedback para: history_preferences")
        print(f"[USER_FEEDBACK] 💾 Feedback será registrado no banco de dados")
        
        return output


if __name__ == '__main__':
    worker = UserFeedbackWorker()
    worker.start()
