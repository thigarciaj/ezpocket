"""
Teste básico do User Feedback Agent (sem Redis)
"""

import sys
import json
from pathlib import Path

# Adicionar path do backend
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

from agents.user_feedback_agent.user_feedback import UserFeedbackAgent


def test_positive_feedback():
    """Teste com feedback muito positivo"""
    print("\n" + "="*70)
    print("TEST 1: Feedback Muito Positivo (5 estrelas)")
    print("="*70)
    
    agent = UserFeedbackAgent()
    
    state = {
        'pergunta': 'Quantas vendas tivemos hoje?',
        'username': 'test_user',
        'projeto': 'vendas',
        'response_text': 'Hoje foram registradas 245 vendas, representando um aumento de 15% em relação à média diária...',
        'rating': 5,
        'comment': 'Resposta perfeita! Muito clara e completa.',
        'is_helpful': True,
        'response_quality': 'excellent',
        'user_satisfaction': 'very_satisfied',
        'would_recommend': True,
        'feedback_tags': ['accurate', 'fast', 'clear', 'helpful', 'complete']
    }
    
    result = agent.execute(state)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    assert result['feedback_recorded'] == True
    assert result['sentiment'] == 'very_positive'
    assert len(result['positive_aspects']) == 5
    assert len(result['improvement_areas']) == 0
    
    print("\n✅ Teste 1 passou!")


def test_negative_feedback():
    """Teste com feedback negativo"""
    print("\n" + "="*70)
    print("TEST 2: Feedback Negativo (2 estrelas)")
    print("="*70)
    
    agent = UserFeedbackAgent()
    
    state = {
        'pergunta': 'Qual foi o lucro do mês passado?',
        'username': 'test_user',
        'projeto': 'financeiro',
        'response_text': 'O lucro foi de R$ 50.000...',
        'rating': 2,
        'comment': 'A resposta está incorreta. Os dados não batem com o relatório.',
        'is_helpful': False,
        'response_quality': 'poor',
        'user_satisfaction': 'unsatisfied',
        'would_recommend': False,
        'feedback_tags': ['wrong', 'incomplete', 'not_helpful']
    }
    
    result = agent.execute(state)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    assert result['feedback_recorded'] == True
    assert result['sentiment'] in ['negative', 'very_negative']
    assert len(result['positive_aspects']) == 0
    assert len(result['improvement_areas']) == 3
    
    print("\n✅ Teste 2 passou!")


def test_neutral_feedback():
    """Teste com feedback neutro"""
    print("\n" + "="*70)
    print("TEST 3: Feedback Neutro (3 estrelas)")
    print("="*70)
    
    agent = UserFeedbackAgent()
    
    state = {
        'pergunta': 'Quantos clientes novos cadastramos essa semana?',
        'username': 'test_user',
        'projeto': 'crm',
        'response_text': 'Foram cadastrados 42 novos clientes.',
        'rating': 3,
        'comment': 'A resposta está correta mas demorou um pouco.',
        'is_helpful': True,
        'response_quality': 'good',
        'user_satisfaction': 'neutral',
        'would_recommend': False,
        'feedback_tags': ['accurate', 'slow']
    }
    
    result = agent.execute(state)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    assert result['feedback_recorded'] == True
    assert result['sentiment'] in ['neutral', 'positive']
    assert len(result['positive_aspects']) == 1  # accurate
    assert len(result['improvement_areas']) == 1  # slow
    
    print("\n✅ Teste 3 passou!")


def test_no_comment():
    """Teste sem comentário"""
    print("\n" + "="*70)
    print("TEST 4: Feedback sem comentário (apenas rating)")
    print("="*70)
    
    agent = UserFeedbackAgent()
    
    state = {
        'pergunta': 'Qual o estoque atual do produto X?',
        'username': 'test_user',
        'projeto': 'estoque',
        'response_text': 'O estoque atual é de 150 unidades.',
        'rating': 4,
        'comment': '',  # Sem comentário
        'is_helpful': True,
        'response_quality': 'very_good',
        'user_satisfaction': 'satisfied',
        'would_recommend': True,
        'feedback_tags': ['accurate', 'clear']
    }
    
    result = agent.execute(state)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    assert result['feedback_recorded'] == True
    assert result['sentiment'] == 'very_positive'
    assert result['comment'] == ''
    
    print("\n✅ Teste 4 passou!")


def test_invalid_rating():
    """Teste com rating inválido"""
    print("\n" + "="*70)
    print("TEST 5: Feedback com rating inválido")
    print("="*70)
    
    agent = UserFeedbackAgent()
    
    state = {
        'pergunta': 'Teste',
        'username': 'test_user',
        'projeto': 'test',
        'response_text': 'Resposta teste',
        'rating': 10,  # Inválido (deve ser 1-5)
        'comment': 'Teste',
        'is_helpful': True,
        'response_quality': 'good',
        'user_satisfaction': 'satisfied',
        'would_recommend': True,
        'feedback_tags': []
    }
    
    result = agent.execute(state)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    assert result['feedback_recorded'] == True
    assert result['rating'] == 0  # Deve ser resetado para 0
    
    print("\n✅ Teste 5 passou!")


if __name__ == '__main__':
    print("\n🧪 INICIANDO TESTES DO USER FEEDBACK AGENT\n")
    
    try:
        test_positive_feedback()
        test_negative_feedback()
        test_neutral_feedback()
        test_no_comment()
        test_invalid_rating()
        
        print("\n" + "="*70)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("="*70 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TESTE FALHOU: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO: {e}\n")
        sys.exit(1)
