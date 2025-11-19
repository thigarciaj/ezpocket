"""
Endpoint de teste para o Plan Confirm Agent
Permite testar o nó de confirmação de plano isoladamente
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

from agents.plan_confirm_agent.plan_confirm import PlanConfirmAgent

app = Flask(__name__)
CORS(app)

# Inicializa o agente
plan_confirm = PlanConfirmAgent()


@app.route('/test-plan-confirm', methods=['POST'])
def test_plan_confirm():
    """
    Endpoint para testar o Plan Confirm Agent isoladamente
    
    Request body:
    {
        "pergunta": "string",
        "plan": "string",
        "username": "string" (opcional),
        "projeto": "string" (opcional),
        "intent_category": "string" (opcional),
        "plan_steps": ["string"] (opcional),
        "estimated_complexity": "string" (opcional),
        "data_sources": ["string"] (opcional),
        "output_format": "string" (opcional)
    }
    
    Response:
    {
        "success": bool,
        "input": {
            "pergunta": string,
            "plan": string,
            "username": string,
            "projeto": string
        },
        "output": {
            "plan_confirmed": bool,
            "confirmation_message": string,
            "user_feedback": string | null,
            "execution_time": float,
            "model_used": string
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
        plan = data.get('plan', '')
        
        if not pergunta:
            return jsonify({
                "success": False,
                "error": "Campo 'pergunta' é obrigatório"
            }), 400
        
        if not plan:
            return jsonify({
                "success": False,
                "error": "Campo 'plan' é obrigatório"
            }), 400
        
        username = data.get('username', 'test_user')
        projeto = data.get('projeto', 'test_project')
        
        # Cria estado de entrada
        state = {
            "pergunta": pergunta,
            "plan": plan,
            "username": username,
            "projeto": projeto,
            "intent_category": data.get('intent_category'),
            "plan_steps": data.get('plan_steps', []),
            "estimated_complexity": data.get('estimated_complexity'),
            "data_sources": data.get('data_sources', []),
            "output_format": data.get('output_format')
        }
        
        print(f"\n{'='*80}")
        print(f"[TEST ENDPOINT] Testando Plan Confirm Agent")
        print(f"[TEST ENDPOINT] Pergunta: {pergunta}")
        print(f"[TEST ENDPOINT] Plan: {plan[:100]}..." if len(plan) > 100 else f"[TEST ENDPOINT] Plan: {plan}")
        print(f"[TEST ENDPOINT] Username: {username}")
        print(f"[TEST ENDPOINT] Projeto: {projeto}")
        print(f"{'='*80}\n")
        
        # Executa confirmação
        result = plan_confirm.confirm_plan(state)
        
        # Prepara resposta
        response = {
            "success": True,
            "input": {
                "pergunta": pergunta,
                "plan": plan,
                "username": username,
                "projeto": projeto,
                "intent_category": state.get('intent_category'),
                "plan_steps": state.get('plan_steps'),
                "estimated_complexity": state.get('estimated_complexity'),
                "data_sources": state.get('data_sources'),
                "output_format": state.get('output_format')
            },
            "output": result
        }
        
        print(f"\n{'='*80}")
        print(f"[TEST ENDPOINT] Resultado:")
        print(f"[TEST ENDPOINT] Plan Confirmed: {result.get('plan_confirmed')}")
        print(f"[TEST ENDPOINT] Message: {result.get('confirmation_message')}")
        print(f"[TEST ENDPOINT] Execution Time: {result.get('execution_time', 0):.3f}s")
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
        "agent": "PlanConfirmAgent",
        "version": "1.0.0"
    }), 200


@app.route('/info', methods=['GET'])
def info():
    """Retorna informações sobre o agente"""
    return jsonify({
        "agent": "PlanConfirmAgent",
        "description": "Agente responsável por solicitar confirmação do usuário sobre o plano de execução gerado",
        "version": "1.0.0",
        "model": "gpt-4o",
        "temperature": 0.3,
        "port": 5010,
        "endpoints": {
            "/test-plan-confirm": "POST - Testa confirmação de plano",
            "/health": "GET - Health check",
            "/info": "GET - Informações do agente"
        },
        "responsibilities": [
            "Apresentar o plano de execução de forma clara",
            "Solicitar confirmação explícita do usuário",
            "Destacar recursos e complexidade",
            "Permitir aceite ou rejeição do plano"
        ],
        "note": "Este agente NÃO salva dados no banco de dados"
    }), 200


if __name__ == '__main__':
    port = int(os.getenv('PLAN_CONFIRM_PORT', 5010))
    print("\n" + "="*80)
    print("🚀 Plan Confirm Agent - Test Endpoint")
    print("="*80)
    print(f"✅ Servidor rodando em: http://localhost:{port}")
    print(f"📡 Endpoint de teste: POST http://localhost:{port}/test-plan-confirm")
    print(f"❤️  Health check: GET http://localhost:{port}/health")
    print(f"ℹ️  Info: GET http://localhost:{port}/info")
    print("="*80 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)
