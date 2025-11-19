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
                host="localhost",
                database="ezpocket",
                user="postgres",
                password="postgres"
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
        
        # Se rating não foi fornecido, pedir ao usuário via input()
        if not rating or rating <= 0:
            print(f"\n" + "="*80)
            print(f"📊 POR FAVOR, AVALIE A RESPOSTA:")
            print(f"="*80)
            print(f"\n❓ Pergunta: {pergunta}")
            print(f"\n💬 Resposta:")
            print(f"{response_text}")
            print(f"\n" + "="*80)
            print(f"⭐ Como você avalia esta resposta?")
            print(f"   1 = Péssima")
            print(f"   2 = Ruim")
            print(f"   3 = Regular")
            print(f"   4 = Boa")
            print(f"   5 = Excelente")
            
            while True:
                try:
                    rating_input = input("\nDigite o rating (1-5): ").strip()
                    rating = int(rating_input)
                    if 1 <= rating <= 5:
                        break
                    print("❌ Rating deve ser entre 1 e 5")
                except ValueError:
                    print("❌ Digite um número válido")
                except EOFError:
                    print("\n⚠️  Input não disponível, usando rating padrão 3")
                    rating = 3
                    break
            
            # Pedir comentário opcional
            try:
                comment = input("\n💭 Comentário (Enter para pular): ").strip()
                if comment:
                    data['comment'] = comment
            except (EOFError, KeyboardInterrupt):
                comment = ""
            
            # Atualizar data com o rating
            data['rating'] = rating
            data['response_text'] = response_text
            data['is_helpful'] = rating >= 3
            data['would_recommend'] = rating >= 4
            
            print(f"\n✅ Obrigado pelo feedback!")
            print(f"="*80 + "\n")
        
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
