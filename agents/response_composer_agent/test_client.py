#!/usr/bin/env python3
"""
Teste simples do Response Composer Agent
"""

import sys
import os
from pathlib import Path

# Adicionar paths
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

from agents.response_composer_agent.response_composer import ResponseComposerAgent
import json

def test_basic():
    """Teste básico de formatação de resposta"""
    
    print("=" * 80)
    print("🧪 TESTE: Response Composer Agent")
    print("=" * 80)
    print()
    
    agent = ResponseComposerAgent()
    
    # Estado de teste com análise do Python Runtime
    test_state = {
        'pergunta': 'Quantas vendas tivemos ontem?',
        'username': 'test_user',
        'projeto': 'test_project',
        'row_count': 1,
        'analysis_summary': 'Foram registradas 150 vendas no dia anterior, representando um aumento de 25% em relação à média diária de 120 vendas.',
        'statistics': {
            'total_vendas': 150,
            'media_diaria': 120,
            'variacao_percentual': '+25%',
            'tendencia': 'crescimento'
        },
        'insights': [
            {
                'title': 'Volume acima da média',
                'description': 'O volume de 150 vendas está 25% acima da média diária de 120 vendas, indicando um dia de alto desempenho.',
                'impact': 'alto',
                'business_value': 'Resultado positivo que pode indicar sucesso de ações de marketing ou sazonalidade favorável'
            },
            {
                'title': 'Tendência de crescimento',
                'description': 'Observa-se uma tendência de crescimento nas últimas semanas.',
                'impact': 'médio',
                'business_value': 'Momentum positivo que deve ser mantido e potencializado'
            },
            {
                'title': 'Oportunidade de otimização',
                'description': 'Com o volume alto, há oportunidade para otimizar conversão e ticket médio.',
                'impact': 'alto',
                'business_value': 'Potencial de aumentar ainda mais a receita com mesmo volume'
            }
        ],
        'recommendations': [
            {
                'action': 'Investigar fatores que levaram ao alto volume',
                'priority': 'alta',
                'expected_impact': 'Entender causas do sucesso para replicar em outros dias'
            },
            {
                'action': 'Garantir estoque adequado para demanda crescente',
                'priority': 'alta',
                'expected_impact': 'Evitar rupturas e perda de vendas'
            },
            {
                'action': 'Analisar ticket médio e mix de produtos',
                'priority': 'média',
                'expected_impact': 'Identificar oportunidades de upsell e cross-sell'
            }
        ],
        'visualizations': [
            {
                'type': 'line_chart',
                'title': 'Evolução de Vendas (Últimos 30 dias)',
                'x_axis': 'data',
                'y_axis': 'vendas',
                'reason': 'Visualizar tendência e identificar padrões sazonais'
            },
            {
                'type': 'bar_chart',
                'title': 'Comparação: Ontem vs Média',
                'x_axis': 'periodo',
                'y_axis': 'vendas',
                'reason': 'Destacar visualmente o desempenho excepcional de ontem'
            }
        ]
    }
    
    print("📥 INPUT:")
    print(f"   Pergunta: {test_state['pergunta']}")
    print(f"   Análise: {test_state['analysis_summary'][:80]}...")
    print(f"   Insights: {len(test_state['insights'])}")
    print(f"   Recomendações: {len(test_state['recommendations'])}")
    print()
    
    print("🤖 Executando Response Composer...")
    print()
    
    result = agent.execute(test_state)
    
    print("=" * 80)
    print("📤 OUTPUT:")
    print("=" * 80)
    print()
    
    if result.get('error'):
        print(f"❌ ERRO: {result['error']}")
        return False
    
    print("📝 RESPOSTA FORMATADA:")
    print("-" * 80)
    print(result['response_text'])
    print("-" * 80)
    print()
    
    print("📊 MÉTRICAS:")
    print(f"   • Response Summary: {result['response_summary']}")
    print(f"   • Key Numbers: {result['key_numbers']}")
    print(f"   • Formatting Style: {result['formatting_style']}")
    print(f"   • User-Friendly Score: {result['user_friendly_score']}/10")
    print(f"   • Tokens Used: {result['tokens_used']}")
    print(f"   • Model: {result['model_used']}")
    print()
    
    # Validações
    success = True
    
    if not result['response_text']:
        print("❌ FALHA: response_text vazio")
        success = False
    
    if result['user_friendly_score'] < 7.0:
        print(f"⚠️  AVISO: Score baixo ({result['user_friendly_score']})")
    
    if len(result['response_text']) < 100:
        print("⚠️  AVISO: Resposta muito curta")
    
    if success:
        print("✅ TESTE PASSOU!")
    else:
        print("❌ TESTE FALHOU!")
    
    return success


if __name__ == '__main__':
    success = test_basic()
    sys.exit(0 if success else 1)
