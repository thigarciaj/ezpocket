"""
USER PROPOSED PLAN AGENT
Recebe a sugestão do usuário sobre o que fazer (sem processamento de IA)
Similar ao PlanConfirmAgent - apenas recebe input do usuário
"""

import json
import os
from datetime import datetime


class UserProposedPlanAgent:
    def __init__(self):
        """Inicializa o agente de plano proposto pelo usuário"""
        self.agent_name = "UserProposedPlanAgent"
        print("\n" + "="*80)
        print("💡 USER PROPOSED PLAN AGENT - SUGESTÃO DO USUÁRIO")
        print("="*80)
        print("✅ Agente inicializado")
        print("="*80 + "\n")
    
    def receive_user_plan(self, state: dict) -> dict:
        """
        Recebe o plano proposto pelo usuário (APENAS RECEBE - NÃO PROCESSA COM IA)
        
        Args:
            state: Dicionário com:
                - pergunta: Pergunta original
                - user_proposed_plan: Sugestão do usuário sobre o que fazer
                - username: Nome do usuário
                - projeto: Nome do projeto
        
        Returns:
            dict com o plano proposto pelo usuário
        """
        
        pergunta = state.get('pergunta', '')
        user_plan = state.get('user_proposed_plan', '')
        username = state.get('username', 'unknown')
        projeto = state.get('projeto', 'default')
        conversation_context = state.get('conversation_context', '')
        has_history = state.get('has_history', False)
        
        print("="*80)
        print("[USER_PROPOSED_PLAN] 💡 USER PROPOSED PLAN - SUGESTÃO DO USUÁRIO")
        print("="*80)
        print(f"[USER_PROPOSED_PLAN] 📥 INPUTS:")
        print(f"[USER_PROPOSED_PLAN]    👤 Username: {username}")
        print(f"[USER_PROPOSED_PLAN]    📁 Projeto: {projeto}")
        print(f"[USER_PROPOSED_PLAN]    📝 Pergunta: {pergunta}")
        print(f"[USER_PROPOSED_PLAN]    💬 Sugestão: {user_plan[:100]}...")
        print()
        
        print(f"[USER_PROPOSED_PLAN] 💡 SUGESTÃO RECEBIDA:")
        print(f"[USER_PROPOSED_PLAN]    {user_plan}")
        print()
        
        # Validação básica
        if not user_plan or user_plan.strip() == '':
            print(f"[USER_PROPOSED_PLAN] ❌ Sugestão vazia!")
            return {
                'user_proposed_plan': '',
                'plan_received': False,
                'received_at': datetime.now().isoformat(),
                'error': 'Sugestão não pode estar vazia',
                'pergunta': pergunta,
                'username': username,
                'projeto': projeto
            }
        
        # Apenas retorna a sugestão (sem processamento)
        result = {
            'user_proposed_plan': user_plan,
            'plan_received': True,
            'received_at': datetime.now().isoformat(),
            'pergunta': pergunta,
            'username': username,
            'projeto': projeto,
            # Propagar contexto para plan_refiner
            'conversation_context': conversation_context,
            'has_history': has_history
        }
        
        print(f"[USER_PROPOSED_PLAN] 📤 OUTPUT:")
        print(f"[USER_PROPOSED_PLAN]    ✅ Sugestão registrada")
        print(f"[USER_PROPOSED_PLAN]    📝 Texto: {user_plan[:80]}...")
        print(f"[USER_PROPOSED_PLAN]    🕐 Timestamp: {result['received_at']}")
        print("="*80)
        print()
        
        return result


# Exemplo de uso
if __name__ == "__main__":
    agent = UserProposedPlanAgent()
    
    # Teste
    state = {
        'pergunta': 'Quantas vendas tivemos hoje?',
        'user_proposed_plan': 'Consulte a tabela report_orders filtrando por data de hoje e conte o total de registros',
        'username': 'test_user',
        'projeto': 'test_project'
    }
    
    result = agent.receive_user_plan(state)
    print(f"\n✅ Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
