#!/usr/bin/env python3
"""
Teste para UserProposedPlanAgent
Testa se o agente consegue receber sugestões do usuário
"""

import sys
from pathlib import Path

# Adicionar paths
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

from agents.user_proposed_plan_agent.user_proposed_plan import UserProposedPlanAgent
import json


def test_user_proposed_plan():
    """Testa recebimento de sugestão do usuário"""
    print("="*80)
    print("🧪 TESTE: USER PROPOSED PLAN AGENT")
    print("="*80)
    
    agent = UserProposedPlanAgent()
    
    # Teste 1: Sugestão simples
    print("\n📋 Teste 1: Sugestão simples")
    print("-"*80)
    
    state1 = {
        'pergunta': 'Quantas vendas tivemos hoje?',
        'user_proposed_plan': 'Consulte a tabela report_orders filtrando por data de hoje e conte o total',
        'username': 'test_user',
        'projeto': 'test_project'
    }
    
    result1 = agent.receive_user_plan(state1)
    
    print(f"\n✅ Resultado:")
    print(json.dumps(result1, indent=2, ensure_ascii=False))
    
    assert result1['plan_received'] == True, "Plano deveria ter sido recebido"
    assert result1['user_proposed_plan'] == state1['user_proposed_plan'], "Plano deveria ser idêntico ao enviado"
    print("\n✅ Teste 1 passou!")
    
    # Teste 2: Sugestão complexa
    print("\n📋 Teste 2: Sugestão complexa")
    print("-"*80)
    
    state2 = {
        'pergunta': 'Qual o faturamento do mês?',
        'user_proposed_plan': 'Primeiro busque todas as vendas do mês na tabela report_orders, depois some os valores da coluna amount, e por fim calcule a média diária',
        'username': 'test_user',
        'projeto': 'test_project'
    }
    
    result2 = agent.receive_user_plan(state2)
    
    print(f"\n✅ Resultado:")
    print(json.dumps(result2, indent=2, ensure_ascii=False))
    
    assert result2['plan_received'] == True, "Plano deveria ter sido recebido"
    assert result2['user_proposed_plan'] == state2['user_proposed_plan'], "Plano deveria ser idêntico ao enviado"
    print("\n✅ Teste 2 passou!")
    
    # Teste 3: Sugestão com instruções técnicas
    print("\n📋 Teste 3: Sugestão técnica")
    print("-"*80)
    
    state3 = {
        'pergunta': 'Mostre os top 5 clientes',
        'user_proposed_plan': 'SELECT customer_name, SUM(amount) as total FROM report_orders GROUP BY customer_name ORDER BY total DESC LIMIT 5',
        'username': 'test_user',
        'projeto': 'test_project'
    }
    
    result3 = agent.receive_user_plan(state3)
    
    print(f"\n✅ Resultado:")
    print(json.dumps(result3, indent=2, ensure_ascii=False))
    
    assert result3['plan_received'] == True, "Plano deveria ter sido recebido"
    assert result3['user_proposed_plan'] == state3['user_proposed_plan'], "Plano deveria ser idêntico ao enviado"
    print("\n✅ Teste 3 passou!")
    
    print("\n" + "="*80)
    print("✅ TODOS OS TESTES PASSARAM!")
    print("="*80)


if __name__ == "__main__":
    test_user_proposed_plan()
