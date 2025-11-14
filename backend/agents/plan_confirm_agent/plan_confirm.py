"""
PLAN CONFIRM AGENT
Solicita confirmação do usuário antes de executar o plano
"""

import json
import os
from datetime import datetime


class PlanConfirmAgent:
    def __init__(self):
        """Inicializa o agente de confirmação"""
        self.agent_name = "PlanConfirmAgent"
        print(f"✅ {self.agent_name} carregado\n")
    
    def confirm_plan(self, state: dict) -> dict:
        """
        Solicita confirmação do usuário para o plano gerado
        
        Args:
            state: Dicionário com:
                - plan: Plano gerado
                - plan_steps: Lista de passos
                - estimated_complexity: Complexidade estimada
                - pergunta: Pergunta original
        
        Returns:
            dict com resultado da confirmação
        """
        
        pergunta = state.get('pergunta', '')
        plan = state.get('plan', '')
        plan_steps = state.get('plan_steps', [])
        complexity = state.get('estimated_complexity', 'média')
        
        print("="*80)
        print("[PLAN_CONFIRM] 🤝 PLAN CONFIRM AGENT - CONFIRMAÇÃO DE PLANO")
        print("="*80)
        print(f"[PLAN_CONFIRM] 📥 INPUTS:")
        print(f"[PLAN_CONFIRM]    📝 Pergunta: {pergunta}")
        print(f"[PLAN_CONFIRM]    📋 Plano: {plan[:100]}...")
        print(f"[PLAN_CONFIRM]    📊 Passos: {len(plan_steps)}")
        print(f"[PLAN_CONFIRM]    ⚡ Complexidade: {complexity}")
        print()
        
        print(f"[PLAN_CONFIRM] 📋 PLANO PROPOSTO:")
        print(f"[PLAN_CONFIRM]    {plan}")
        print()
        print(f"[PLAN_CONFIRM] 📊 PASSOS ({len(plan_steps)}):")
        for i, step in enumerate(plan_steps, 1):
            print(f"[PLAN_CONFIRM]    {i}. {step}")
        print()
        
        # Solicitar confirmação do usuário
        print(f"[PLAN_CONFIRM] ⚙️  PROCESSAMENTO:")
        print(f"[PLAN_CONFIRM]    🤔 Aguardando confirmação do usuário...")
        print()
        
        # Verificar se está em modo auto-confirm (worker) ou manual (interativo)
        auto_confirm = os.getenv('AUTO_CONFIRM_PLAN', 'false').lower() == 'true'
        
        if auto_confirm:
            # Modo automático (para workers)
            print(f"[PLAN_CONFIRM]    ✅ Plano confirmado automaticamente (modo worker)")
            confirmed = True
            feedback = 'Plano aprovado automaticamente em modo worker'
            method = 'auto'
        else:
            # Modo manual (pergunta ao usuário)
            print(f"[PLAN_CONFIRM]    🤔 Deseja prosseguir com este plano? (s/n): ", end='', flush=True)
            user_input = input().strip().lower()
            
            if user_input in ['s', 'sim', 'y', 'yes']:
                confirmed = True
                feedback = 'Plano aprovado pelo usuário'
                method = 'manual'
                print(f"[PLAN_CONFIRM]    ✅ Plano confirmado!")
            else:
                confirmed = False
                feedback = 'Plano rejeitado pelo usuário'
                method = 'manual'
                print(f"[PLAN_CONFIRM]    ❌ Plano rejeitado!")
        
        print()
        
        result = {
            'confirmed': confirmed,
            'confirmation_method': method,
            'confirmation_time': datetime.now().isoformat(),
            'user_feedback': feedback,
            'plan_accepted': confirmed
        }
        
        print("="*80)
        print(f"[PLAN_CONFIRM] 📤 OUTPUT:")
        print(f"[PLAN_CONFIRM]    ✅ Confirmado: {result['confirmed']}")
        print(f"[PLAN_CONFIRM]    📝 Método: {result['confirmation_method']}")
        print(f"[PLAN_CONFIRM]    💬 Feedback: {result['user_feedback']}")
        print("="*80)
        print()
        
        return result


if __name__ == "__main__":
    # Teste standalone
    agent = PlanConfirmAgent()
    
    test_state = {
        'pergunta': 'Quantas vendas hoje?',
        'plan': 'Consultar tabela report_orders filtrando por data atual',
        'plan_steps': [
            'Conectar ao Athena',
            'Filtrar WHERE date = CURRENT_DATE',
            'Executar COUNT(*)',
            'Retornar resultado'
        ],
        'estimated_complexity': 'baixa'
    }
    
    result = agent.confirm_plan(test_state)
    print(f"\n✅ Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
