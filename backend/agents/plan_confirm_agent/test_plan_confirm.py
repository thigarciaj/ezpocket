#!/usr/bin/env python3
"""
Teste do Plan Confirm Agent
"""

import sys
import os

# Adicionar diretório backend ao path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from plan_confirm_agent.plan_confirm import PlanConfirmAgent


def test_plan_confirm():
    """Testa o agente de confirmação de plano"""
    
    print("="*80)
    print("🧪 TESTANDO PLAN CONFIRM AGENT")
    print("="*80)
    print()
    
    # Criar agente
    agent = PlanConfirmAgent()
    
    # Estado de teste
    test_state = {
        'pergunta': 'Quantas vendas foram feitas ontem?',
        'plan': 'Consultar a tabela report_orders aplicando filtro para a data de ontem e contar os registros.',
        'plan_steps': [
            "Consultar tabela 'report_orders' no Athena",
            'Aplicar filtro WHERE para a data de ontem',
            'Executar agregação COUNT(*)',
            'Retornar resultado como número inteiro'
        ],
        'estimated_complexity': 'baixa',
        'data_sources': ['report_orders'],
        'output_format': 'número'
    }
    
    # Executar confirmação
    result = agent.confirm_plan(test_state)
    
    # Validar resultado
    print("\n" + "="*80)
    print("✅ RESULTADO DO TESTE")
    print("="*80)
    print(f"Confirmado: {result['confirmed']}")
    print(f"Método: {result['confirmation_method']}")
    print(f"Plano aceito: {result['plan_accepted']}")
    print(f"Feedback: {result['user_feedback']}")
    print()
    
    assert result['confirmed'] == True, "Plano deveria estar confirmado"
    assert result['plan_accepted'] == True, "Plano deveria estar aceito"
    
    print("✅ Todos os testes passaram!")
    print()


if __name__ == "__main__":
    test_plan_confirm()
