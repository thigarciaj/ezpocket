#!/usr/bin/env python3
"""
Test Endpoint - Servidor Flask para testar Athena Executor Agent via HTTP
Porta: 5017
"""

import sys
import os
from pathlib import Path
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Adicionar paths
agents_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, agents_path)

# Carregar .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from agents.athena_executor_agent.athena_executor import AthenaExecutorAgent

app = Flask(__name__)
executor = AthenaExecutorAgent()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'athena_executor_test',
        'database': executor.database,
        'region': executor.aws_region
    })

@app.route('/test-executor', methods=['POST'])
def test_executor():
    """
    Testa execução de query no Athena
    
    Body esperado:
    {
        "query_sql": "SELECT * FROM orders LIMIT 10",
        "username": "test_user",
        "projeto": "test_project"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        query_sql = data.get('query_sql')
        if not query_sql:
            return jsonify({'error': 'query_sql is required'}), 400
        
        username = data.get('username', 'test_user')
        projeto = data.get('projeto', 'test_project')
        
        print(f"\n{'='*80}")
        print(f"📨 Requisição recebida")
        print(f"{'='*80}")
        print(f"Query: {query_sql[:100]}...")
        print(f"Username: {username}")
        print(f"Projeto: {projeto}")
        print(f"{'='*80}\n")
        
        # Executar
        result = executor.execute(
            query_sql=query_sql,
            username=username,
            projeto=projeto
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Erro no endpoint: {str(e)}")
        return jsonify({
            'error': str(e),
            'type': type(e).__name__
        }), 500

@app.route('/test-executor-mock', methods=['POST'])
def test_executor_mock():
    """
    Testa com dados mockados (não executa no Athena real)
    Útil para testar sem consumir recursos AWS
    """
    try:
        data = request.get_json()
        query_sql = data.get('query_sql', 'SELECT * FROM orders LIMIT 10')
        username = data.get('username', 'test_user')
        projeto = data.get('projeto', 'test_project')
        
        # Resultado mockado
        mock_result = {
            'success': True,
            'query_executed': query_sql,
            'execution_time_seconds': 1.23,
            'row_count': 10,
            'column_count': 5,
            'columns': ['order_id', 'customer_name', 'total', 'status', 'created_at'],
            'results_preview': [
                {'order_id': 'ORD-001', 'customer_name': 'João Silva', 'total': 250.00, 'status': 'completed', 'created_at': '2025-11-01'},
                {'order_id': 'ORD-002', 'customer_name': 'Maria Santos', 'total': 180.50, 'status': 'pending', 'created_at': '2025-11-02'}
            ],
            'data_size_mb': 0.05,
            'database': 'receivables_db',
            'region': 'us-east-1',
            'error': None,
            'mock': True
        }
        
        print(f"\n{'='*80}")
        print(f"🎭 Mock - Resultado simulado retornado")
        print(f"{'='*80}\n")
        
        return jsonify(mock_result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Athena Executor Test Server")
    print("="*60)
    print(f"Porta: 5017")
    print(f"Health: http://localhost:5017/health")
    print(f"Test Real: POST http://localhost:5017/test-executor")
    print(f"Test Mock: POST http://localhost:5017/test-executor-mock")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5017, debug=True)
