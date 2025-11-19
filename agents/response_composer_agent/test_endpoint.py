#!/usr/bin/env python3
"""
Teste do endpoint Response Composer via Redis
"""

import sys
import os
from pathlib import Path
import json
import redis
import time
import uuid

# Adicionar paths
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

def test_endpoint():
    """Testa o endpoint response_composer via Redis"""
    
    print("=" * 80)
    print("🧪 TESTE: Response Composer Endpoint (Redis)")
    print("=" * 80)
    print()
    
    # Conectar ao Redis
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        print("✅ Conectado ao Redis")
    except Exception as e:
        print(f"❌ Erro ao conectar ao Redis: {e}")
        return False
    
    # Criar job de teste
    job_id = str(uuid.uuid4())
    
    test_data = {
        'job_id': job_id,
        'pergunta': 'Quantas vendas tivemos na última semana?',
        'username': 'test_user',
        'projeto': 'test_project',
        'analysis_summary': 'Foram registradas 850 vendas na última semana, com média diária de 121 vendas.',
        'statistics': {
            'total_semanal': 850,
            'media_diaria': 121,
            'melhor_dia': 'sexta (180 vendas)',
            'pior_dia': 'domingo (85 vendas)'
        },
        'insights': [
            {
                'title': 'Sexta-feira é o melhor dia',
                'description': 'Sexta-feira concentra 21% das vendas semanais',
                'impact': 'alto'
            },
            {
                'title': 'Domingo tem baixa performance',
                'description': 'Domingo tem apenas 10% das vendas da semana',
                'impact': 'médio'
            }
        ],
        'recommendations': [
            {
                'action': 'Reforçar equipe e estoque nas sextas-feiras',
                'priority': 'alta',
                'expected_impact': 'Maximizar vendas no melhor dia'
            },
            {
                'action': 'Criar promoções para domingos',
                'priority': 'média',
                'expected_impact': 'Aumentar volume no dia mais fraco'
            }
        ],
        'visualizations': [
            {
                'type': 'bar_chart',
                'title': 'Vendas por Dia da Semana',
                'reason': 'Visualizar padrão semanal claramente'
            }
        ]
    }
    
    print(f"📤 Enviando job {job_id} para fila response_composer...")
    print(f"   Pergunta: {test_data['pergunta']}")
    print()
    
    # Enviar para fila
    r.rpush('queue:response_composer', json.dumps(test_data))
    
    print("⏳ Aguardando processamento (máx 30s)...")
    print()
    
    # Aguardar resultado
    max_wait = 30
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        result = r.get(f'result:{job_id}')
        
        if result:
            result_data = json.loads(result)
            
            print("=" * 80)
            print("✅ RESULTADO RECEBIDO:")
            print("=" * 80)
            print()
            
            if result_data.get('error'):
                print(f"❌ ERRO: {result_data['error']}")
                return False
            
            print("📝 RESPOSTA FORMATADA:")
            print("-" * 80)
            print(result_data.get('response_text', ''))
            print("-" * 80)
            print()
            
            print("📊 MÉTRICAS:")
            print(f"   • Summary: {result_data.get('response_summary', '')}")
            print(f"   • Key Numbers: {result_data.get('key_numbers', [])}")
            print(f"   • User-Friendly Score: {result_data.get('user_friendly_score', 0)}/10")
            print(f"   • Tokens: {result_data.get('tokens_used', 0)}")
            print()
            
            # Limpar resultado do Redis
            r.delete(f'result:{job_id}')
            
            print("✅ TESTE PASSOU!")
            return True
        
        time.sleep(1)
        print(".", end="", flush=True)
    
    print()
    print("❌ TIMEOUT: Nenhum resultado recebido em 30s")
    print("   Verifique se o worker response_composer está rodando:")
    print("   python agents/graph_orchestrator/worker_response_composer.py")
    return False


if __name__ == '__main__':
    success = test_endpoint()
    sys.exit(0 if success else 1)
