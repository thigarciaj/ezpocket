"""
Test Endpoint para Python Runtime Agent
Servidor Flask para testes interativos
"""
import os
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from pathlib import Path
import sys

# Carregar .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Adicionar path
agents_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, agents_path)

from agents.python_runtime_agent import PythonRuntimeAgent

app = Flask(__name__)

# Inicializar agente
print("\n" + "="*80)
print("🚀 Iniciando Python Runtime Agent Test Server")
print("="*80)
agent = PythonRuntimeAgent()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'agent': 'Python Runtime Agent',
        'version': '1.0.0'
    })

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Endpoint principal para análise estatística
    
    Body esperado:
    {
        "pergunta": "Quantas vendas tivemos ontem?",
        "username": "test_user",
        "projeto": "test_project",
        "query_results": {
            "success": true,
            "row_count": 10,
            "columns": ["col1", "col2"],
            "results_full": [...],
            "results_preview": [...]
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No JSON data provided'
            }), 400
        
        print("\n" + "="*80)
        print("📥 RECEBENDO REQUISIÇÃO")
        print("="*80)
        print(f"Pergunta: {data.get('pergunta', 'N/A')}")
        print(f"Usuário: {data.get('username', 'N/A')}")
        print(f"Projeto: {data.get('projeto', 'N/A')}")
        
        # Executar análise
        result = agent.analyze(data)
        
        print("\n📤 ENVIANDO RESPOSTA")
        print(f"Sucesso: {result.get('success', False)}")
        print(f"Análise: {result.get('has_analysis', False)}")
        print("="*80 + "\n")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}\n")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/test', methods=['GET'])
def test():
    """Endpoint de teste simples"""
    
    test_state = {
        'pergunta': 'Quantas vendas tivemos nos últimos 7 dias?',
        'username': 'test_user',
        'projeto': 'test_project',
        'query_results': {
            'success': True,
            'row_count': 7,
            'column_count': 2,
            'columns': ['data', 'vendas'],
            'results_full': [
                {'data': '2024-11-13', 'vendas': 45},
                {'data': '2024-11-14', 'vendas': 52},
                {'data': '2024-11-15', 'vendas': 38},
                {'data': '2024-11-16', 'vendas': 61},
                {'data': '2024-11-17', 'vendas': 48},
                {'data': '2024-11-18', 'vendas': 55},
                {'data': '2024-11-19', 'vendas': 50}
            ],
            'results_preview': [
                {'data': '2024-11-13', 'vendas': 45},
                {'data': '2024-11-14', 'vendas': 52},
                {'data': '2024-11-15', 'vendas': 38}
            ],
            'results_message': '7 vendas encontradas'
        }
    }
    
    result = agent.analyze(test_state)
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.getenv('PYTHON_RUNTIME_PORT', 5018))
    
    print(f"\n🌐 Servidor rodando em http://localhost:{port}")
    print(f"📊 Endpoints disponíveis:")
    print(f"   GET  /health - Health check")
    print(f"   GET  /test   - Teste rápido")
    print(f"   POST /analyze - Análise estatística")
    print("\n" + "="*80 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)
