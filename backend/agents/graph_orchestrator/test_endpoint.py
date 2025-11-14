"""
Endpoint de teste para o Graph Orchestrator
Permite testar o orquestrador isoladamente
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config', '.env')
load_dotenv(dotenv_path)

# Adiciona o caminho do backend ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.graph_orchestrator.graph_orchestrator import GraphOrchestrator
from agents.graph_orchestrator.graph_config import EXPECTED_FLOW

app = Flask(__name__)
CORS(app)

# Inicializa o orquestrador
orchestrator = GraphOrchestrator()


@app.route('/test-orchestrator/health', methods=['GET'])
def health():
    """Verifica se o serviço está rodando"""
    from agents.graph_orchestrator.graph_orchestrator import REDIS_CONFIG
    
    try:
        redis_status = "connected" if orchestrator.redis.ping() else "disconnected"
    except:
        redis_status = "error"
    
    return jsonify({
        "status": "healthy",
        "service": "Graph Orchestrator Test Endpoint",
        "version": "1.0.0",
        "port": 5008,
        "redis_status": redis_status,
        "redis_host": REDIS_CONFIG['host'],
        "redis_port": REDIS_CONFIG['port']
    })

@app.route('/test-orchestrator', methods=['POST'])
def test_orchestrator():
    """
    Endpoint para testar o Graph Orchestrator isoladamente
    
    Request body:
    {
        "pergunta": "string",
        "username": "string" (opcional),
        "projeto": "string" (opcional),
        "module": "string" (opcional, default: "intent_validator")
    }
    
    Response:
    {
        "success": bool,
        "job_id": string,
        "input": {...},
        "module": string,
        "expected_flow": string,
        "instructions": string
    }
    """
    try:
        # Obtém dados do request
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "Request body vazio ou inválido"
            }), 400
        
        pergunta = data.get('pergunta', '')
        
        if not pergunta:
            return jsonify({
                "success": False,
                "error": "Campo 'pergunta' é obrigatório"
            }), 400
        
        username = data.get('username', 'test_user')
        projeto = data.get('projeto', 'test_project')
        module = data.get('module', 'intent_validator')
        
        # Cria payload
        payload = {
            "username": username,
            "projeto": projeto,
            "pergunta": pergunta
        }
        
        print(f"\n{'='*80}")
        print(f"[TEST ENDPOINT] Testando Graph Orchestrator")
        print(f"[TEST ENDPOINT] Módulo: {module}")
        print(f"[TEST ENDPOINT] Pergunta: {pergunta}")
        print(f"[TEST ENDPOINT] Username: {username}")
        print(f"[TEST ENDPOINT] Projeto: {projeto}")
        print(f"{'='*80}\n")
        
        # Submete o job com os 4 argumentos corretos
        job_id = orchestrator.submit_job(
            start_module=module,
            username=username,
            projeto=projeto,
            initial_data={"pergunta": pergunta}
        )
        
        # Usar fluxo esperado do graph_config
        flow = EXPECTED_FLOW.get(module, f"{module} (flow não definido)")
        
        return jsonify({
            "success": True,
            "job_id": job_id,
            "input": {
                "pergunta": pergunta,
                "username": username,
                "projeto": projeto
            },
            "module": module,
            "expected_flow": flow,
            "instructions": f"Use GET /test-orchestrator/status/{job_id} para acompanhar"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }), 500

@app.route('/test-orchestrator/status/<job_id>', methods=['GET'])
def job_status(job_id):
    """
    Consulta o status de um job (inclui branches paralelas)
    
    Retorna informações sobre o status atual do job e todas as branches
    """
    try:
        # Buscar job com todas as branches
        status = orchestrator.get_job_with_branches(job_id)
        
        if status is None:
            return jsonify({
                "success": False,
                "error": "Job não encontrado"
            }), 404
        
        return jsonify({
            "success": True,
            "job_id": job_id,
            "status": status
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        }), 500

@app.route('/test-orchestrator/examples', methods=['GET'])
def examples():
    """
    Retorna exemplos de uso do endpoint
    """
    examples_list = [
        {
            "name": "Pergunta válida simples",
            "request": {
                "pergunta": "Quantos pedidos temos hoje?",
                "username": "test_user",
                "projeto": "ezpag"
            },
            "expected_result": {
                "success": True,
                "module": "intent_validator",
                "expected_flow": "intent_validator -> history_preferences"
            }
        },
        {
            "name": "Consulta de relatório",
            "request": {
                "pergunta": "Mostre o relatório de vendas do mês",
                "username": "joao_silva",
                "projeto": "ezpag"
            },
            "expected_result": {
                "success": True,
                "module": "intent_validator",
                "expected_flow": "intent_validator -> history_preferences"
            }
        },
        {
            "name": "Análise de dados",
            "request": {
                "pergunta": "Qual foi o faturamento da semana passada?",
                "username": "maria_santos",
                "projeto": "ezpag"
            },
            "expected_result": {
                "success": True,
                "module": "intent_validator",
                "expected_flow": "intent_validator -> history_preferences"
            }
        }
    ]
    
    return jsonify({
        "success": True,
        "examples": examples_list,
        "total": len(examples_list)
    })

if __name__ == '__main__':
    from agents.graph_orchestrator.graph_orchestrator import REDIS_CONFIG
    
    print("=" * 80)
    print("🔄 GRAPH ORCHESTRATOR TEST ENDPOINT")
    print("=" * 80)
    print(f"Porta: 5008")
    print(f"Redis: {REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}")
    print("\nEndpoints disponíveis:")
    print("  POST /test-orchestrator          - Testar o orquestrador")
    print("  GET  /test-orchestrator/health   - Status do serviço")
    print("  GET  /test-orchestrator/status/<id> - Consultar status de job")
    print("  GET  /test-orchestrator/examples - Ver exemplos de uso")
    print("=" * 80)
    
    app.run(host='0.0.0.0', port=5008, debug=True)
