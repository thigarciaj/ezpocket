"""
Endpoint de teste para o User Proposed Plan Agent
Permite testar o nó de sugestão de plano pelo usuário isoladamente
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
load_dotenv(dotenv_path)

# Adiciona o caminho do backend ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.user_proposed_plan_agent.user_proposed_plan import UserProposedPlanAgent

app = Flask(__name__)
CORS(app)

# Inicializa o agente
user_proposed_plan = UserProposedPlanAgent()


@app.route('/test-user-proposed-plan', methods=['POST'])
def test_user_proposed_plan():
    """
    Endpoint para testar o User Proposed Plan Agent isoladamente
    
    Request body:
    {
        "pergunta": "string",
        "user_proposed_plan": "string",
        "username": "string" (opcional),
        "projeto": "string" (opcional)
    }
    
    Response:
    {
        "success": bool,
        "input": {
            "pergunta": string,
            "user_proposed_plan": string,
            "username": string,
            "projeto": string
        },
        "output": {
            "plan_received": bool,
            "user_proposed_plan": string,
            "received_at": string,
            "pergunta": string,
            "username": string,
            "projeto": string
        }
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
        user_plan = data.get('user_proposed_plan', '')
        
        if not pergunta:
            return jsonify({
                "success": False,
                "error": "Campo 'pergunta' é obrigatório"
            }), 400
        
        if not user_plan:
            return jsonify({
                "success": False,
                "error": "Campo 'user_proposed_plan' é obrigatório"
            }), 400
        
        username = data.get('username', 'test_user')
        projeto = data.get('projeto', 'test_project')
        
        # Cria estado de entrada
        state = {
            "pergunta": pergunta,
            "user_proposed_plan": user_plan,
            "username": username,
            "projeto": projeto
        }
        
        print(f"\n{'='*80}")
        print(f"[TEST ENDPOINT] Testando User Proposed Plan Agent")
        print(f"[TEST ENDPOINT] Pergunta: {pergunta}")
        print(f"[TEST ENDPOINT] Sugestão: {user_plan[:100]}..." if len(user_plan) > 100 else f"[TEST ENDPOINT] Sugestão: {user_plan}")
        print(f"[TEST ENDPOINT] Username: {username}")
        print(f"[TEST ENDPOINT] Projeto: {projeto}")
        print(f"{'='*80}\n")
        
        # Recebe plano do usuário
        result = user_proposed_plan.receive_user_plan(state)
        
        # Prepara resposta
        response = {
            "success": True,
            "input": {
                "pergunta": pergunta,
                "user_proposed_plan": user_plan,
                "username": username,
                "projeto": projeto
            },
            "output": result
        }
        
        print(f"\n{'='*80}")
        print(f"[TEST ENDPOINT] Resultado:")
        print(f"[TEST ENDPOINT] Plan Received: {result.get('plan_received')}")
        print(f"[TEST ENDPOINT] Sugestão: {result.get('user_proposed_plan', '')[:80]}...")
        print(f"[TEST ENDPOINT] Timestamp: {result.get('received_at')}")
        print(f"{'='*80}\n")
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"\n[TEST ENDPOINT] ❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "agent": "UserProposedPlanAgent",
        "version": "1.0.0"
    }), 200


@app.route('/info', methods=['GET'])
def info():
    """Retorna informações sobre o agente"""
    return jsonify({
        "agent": "UserProposedPlanAgent",
        "description": "Agente que recebe sugestões do usuário sobre o que fazer (sem processamento de IA)",
        "version": "1.0.0",
        "port": 5011,
        "endpoints": {
            "/test-user-proposed-plan": "POST - Recebe sugestão do usuário",
            "/health": "GET - Health check",
            "/info": "GET - Informações do agente"
        },
        "responsibilities": [
            "Receber sugestão do usuário",
            "Validar que sugestão não está vazia",
            "Retornar sugestão sem modificações",
            "Não processar com IA"
        ],
        "note": "Este agente apenas recebe input do usuário, similar ao PlanConfirmAgent"
    }), 200


if __name__ == '__main__':
    port = int(os.getenv('USER_PROPOSED_PLAN_PORT', 5011))
    print("\n" + "="*80)
    print("🚀 User Proposed Plan Agent - Test Endpoint")
    print("="*80)
    print(f"✅ Servidor rodando em: http://localhost:{port}")
    print(f"📡 Endpoint de teste: POST http://localhost:{port}/test-user-proposed-plan")
    print(f"❤️  Health check: GET http://localhost:{port}/health")
    print(f"ℹ️  Info: GET http://localhost:{port}/info")
    print("="*80 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)
