"""
Teste do User Feedback Agent com Redis
"""

import sys
import json
import redis
import time
from pathlib import Path

# Adicionar path do backend
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)


def test_feedback_via_redis():
    """Testa envio de feedback via Redis"""
    
    print("\n" + "="*70)
    print("🧪 TESTE: User Feedback Agent via Redis")
    print("="*70)
    
    # Conectar ao Redis
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    print("\n[1] Conectado ao Redis")
    
    # Dados de teste - feedback positivo
    test_data = {
        'pergunta': 'Quantas vendas tivemos hoje?',
        'username': 'test_user_feedback',
        'projeto': 'vendas',
        'response_text': '🎯 Resposta Direta:\nHoje foram registradas 245 vendas...',
        'rating': 5,
        'comment': 'Excelente! Resposta muito clara e completa com bons insights.',
        'is_helpful': True,
        'response_quality': 'excellent',
        'user_satisfaction': 'very_satisfied',
        'would_recommend': True,
        'feedback_tags': ['accurate', 'fast', 'clear', 'helpful', 'complete']
    }
    
    print(f"\n[2] Enviando feedback para queue:user_feedback")
    print(f"    Username: {test_data['username']}")
    print(f"    Projeto: {test_data['projeto']}")
    print(f"    Rating: {test_data['rating']}/5 ⭐")
    print(f"    Tags: {', '.join(test_data['feedback_tags'])}")
    
    # Enviar para a fila
    r.rpush('queue:user_feedback', json.dumps(test_data))
    
    print(f"\n[3] ✅ Feedback enviado!")
    print(f"    Aguardando processamento pelo worker...")
    
    # Aguardar um pouco para o worker processar
    time.sleep(2)
    
    # Verificar se foi processado (a fila deve estar vazia)
    queue_size = r.llen('queue:user_feedback')
    
    if queue_size == 0:
        print(f"\n[4] ✅ Fila processada com sucesso!")
    else:
        print(f"\n[4] ⚠️  Ainda há {queue_size} itens na fila")
    
    print("\n" + "="*70)
    print("✅ TESTE CONCLUÍDO")
    print("="*70)
    print("\nVerifique:")
    print("  1. Os logs do worker no terminal")
    print("  2. A tabela user_feedback_logs no banco de dados")
    print("\n")


def test_multiple_feedbacks():
    """Testa envio de múltiplos feedbacks"""
    
    print("\n" + "="*70)
    print("🧪 TESTE: Múltiplos Feedbacks Diferentes")
    print("="*70)
    
    # Conectar ao Redis
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    feedbacks = [
        {
            'pergunta': 'Qual o faturamento de hoje?',
            'username': 'user1',
            'projeto': 'financeiro',
            'response_text': 'Faturamento: R$ 50.000',
            'rating': 5,
            'comment': 'Perfeito!',
            'is_helpful': True,
            'response_quality': 'excellent',
            'user_satisfaction': 'very_satisfied',
            'would_recommend': True,
            'feedback_tags': ['accurate', 'fast']
        },
        {
            'pergunta': 'Quantos produtos no estoque?',
            'username': 'user2',
            'projeto': 'estoque',
            'response_text': 'Estoque: 1500 unidades',
            'rating': 3,
            'comment': 'OK, mas poderia ser mais detalhado',
            'is_helpful': True,
            'response_quality': 'good',
            'user_satisfaction': 'neutral',
            'would_recommend': False,
            'feedback_tags': ['accurate', 'incomplete']
        },
        {
            'pergunta': 'Qual o lucro do mês?',
            'username': 'user3',
            'projeto': 'financeiro',
            'response_text': 'Lucro: R$ 10.000',
            'rating': 1,
            'comment': 'Resposta incorreta! Os dados estão errados.',
            'is_helpful': False,
            'response_quality': 'poor',
            'user_satisfaction': 'unsatisfied',
            'would_recommend': False,
            'feedback_tags': ['wrong', 'not_helpful']
        }
    ]
    
    print(f"\n[1] Enviando {len(feedbacks)} feedbacks...")
    
    for i, feedback in enumerate(feedbacks, 1):
        print(f"\n    Feedback {i}:")
        print(f"      User: {feedback['username']}")
        print(f"      Rating: {feedback['rating']}/5")
        print(f"      Tags: {', '.join(feedback['feedback_tags'])}")
        
        r.rpush('queue:user_feedback', json.dumps(feedback))
    
    print(f"\n[2] ✅ Todos os feedbacks enviados!")
    print(f"    Aguardando processamento...")
    
    time.sleep(3)
    
    queue_size = r.llen('queue:user_feedback')
    print(f"\n[3] Itens restantes na fila: {queue_size}")
    
    print("\n" + "="*70)
    print("✅ TESTE DE MÚLTIPLOS FEEDBACKS CONCLUÍDO")
    print("="*70 + "\n")


if __name__ == '__main__':
    print("\n🚀 TESTES DO USER FEEDBACK AGENT COM REDIS\n")
    
    try:
        # Verificar se Redis está acessível
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        print("✅ Redis conectado com sucesso!\n")
        
        # Executar testes
        test_feedback_via_redis()
        
        input("\n⏸️  Pressione ENTER para executar teste de múltiplos feedbacks...")
        test_multiple_feedbacks()
        
        print("\n✅ TODOS OS TESTES CONCLUÍDOS!\n")
        
    except redis.ConnectionError:
        print("❌ ERRO: Não foi possível conectar ao Redis")
        print("   Certifique-se de que o Redis está rodando: docker compose up -d\n")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERRO: {e}\n")
        sys.exit(1)
