"""
Endpoint de teste para o Intent Validator Agent
Permite testar o nó de validação de intenção isoladamente
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

from agents.intent_validator_agent.intent_validator import IntentValidatorAgent

app = Flask(__name__)
CORS(app)

# Inicializa o agente
intent_validator = IntentValidatorAgent()


@app.route('/test-intent-validator', methods=['POST'])
def test_intent_validator():
    """
    Endpoint para testar o Intent Validator Agent isoladamente
    
    Request body:
    {
        "pergunta": "string",
        "username": "string" (opcional),
        "projeto": "string" (opcional)
    }
    
    Response:
    {
        "success": bool,
        "input": {
            "pergunta": string,
            "username": string,
            "projeto": string
        },
        "output": {
            "intent_valid": bool,
            "intent_category": string,
            "intent_reason": string,
            "is_special_case": bool (opcional),
            "special_type": string (opcional)
        },
        "route_decision": "valid" | "invalid",
        "next_node": "router" | "out_of_scope"
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
        
        # Cria estado de entrada
        state = {
            "pergunta": pergunta,
            "username": username,
            "projeto": projeto
        }
        
        print(f"\n{'='*80}")
        print(f"[TEST ENDPOINT] Testando Intent Validator Agent")
        print(f"[TEST ENDPOINT] Pergunta: {pergunta}")
        print(f"[TEST ENDPOINT] Username: {username}")
        print(f"[TEST ENDPOINT] Projeto: {projeto}")
        print(f"{'='*80}\n")
        
        # Executa validação
        result = intent_validator.validate(state)
        
        # Determina roteamento
        intent_valid = result.get("intent_valid", False)
        route_decision = "valid" if intent_valid else "invalid"
        next_node = "router" if intent_valid else "out_of_scope"
        
        # Se inválido, gera resposta out of scope
        out_of_scope_response = None
        if not intent_valid:
            out_of_scope_response = intent_validator.generate_out_of_scope_response(result)
        
        # Prepara resposta
        response = {
            "success": True,
            "input": {
                "pergunta": pergunta,
                "username": username,
                "projeto": projeto
            },
            "output": {
                "intent_valid": result.get("intent_valid"),
                "intent_category": result.get("intent_category"),
                "intent_reason": result.get("intent_reason")
            },
            "route_decision": route_decision,
            "next_node": next_node
        }
        
        # Adiciona campos opcionais se existirem
        if "is_special_case" in result:
            response["output"]["is_special_case"] = result["is_special_case"]
        
        if "special_type" in result:
            response["output"]["special_type"] = result["special_type"]
        
        if out_of_scope_response:
            response["out_of_scope_response"] = out_of_scope_response
        
        print(f"\n{'='*80}")
        print(f"[TEST ENDPOINT] ✅ Validação concluída")
        print(f"[TEST ENDPOINT] Route: {route_decision} → {next_node}")
        print(f"{'='*80}\n")
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"\n[TEST ENDPOINT] ❌ ERRO: {str(e)}\n")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/test-intent-validator/health', methods=['GET'])
def health():
    """Health check do endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Intent Validator Test Endpoint",
        "agent": "IntentValidatorAgent",
        "version": "1.0.0"
    }), 200


@app.route('/test-intent-validator/examples', methods=['GET'])
def examples():
    """Retorna exemplos de uso do endpoint"""
    return jsonify({
        "examples": [
            {
                "name": "Quantidade - Contagem de Pedidos",
                "request": {
                    "pergunta": "Quantos pedidos tivemos em outubro?",
                    "username": "joao.silva",
                    "projeto": "ezpocket"
                },
                "expected_result": {
                    "intent_valid": True,
                    "intent_category": "quantidade",
                    "route_decision": "valid",
                    "next_node": "router"
                }
            },
            {
                "name": "Conhecimentos Gerais - Informação da Empresa",
                "request": {
                    "pergunta": "O que é a EZPocket e como funciona?",
                    "username": "maria.costa",
                    "projeto": "ezpocket"
                },
                "expected_result": {
                    "intent_valid": True,
                    "intent_category": "conhecimentos_gerais",
                    "route_decision": "valid",
                    "next_node": "router"
                }
            },
            {
                "name": "Análise Estatística - Tendências",
                "request": {
                    "pergunta": "Qual a tendência de crescimento nos últimos 3 meses?",
                    "username": "pedro.santos",
                    "projeto": "ezpocket"
                },
                "expected_result": {
                    "intent_valid": True,
                    "intent_category": "analise_estatistica",
                    "route_decision": "valid",
                    "next_node": "router"
                }
            },
            {
                "name": "Pergunta Inválida - Fora do Escopo",
                "request": {
                    "pergunta": "Qual a melhor receita de bolo de chocolate?",
                    "username": "ana.lima",
                    "projeto": "ezpocket"
                },
                "expected_result": {
                    "intent_valid": False,
                    "intent_category": "fora_escopo",
                    "route_decision": "invalid",
                    "next_node": "out_of_scope"
                }
            },
            {
                "name": "Quantidade - Valores Totais",
                "request": {
                    "pergunta": "Qual o valor total de receita este ano?",
                    "username": "carlos.mendes",
                    "projeto": "ezpocket"
                },
                "expected_result": {
                    "intent_valid": True,
                    "intent_category": "quantidade",
                    "route_decision": "valid",
                    "next_node": "router"
                }
            }
        ],
        "categories": {
            "quantidade": "Perguntas sobre valores numéricos, contagens, quantidades específicas",
            "conhecimentos_gerais": "Informações sobre a empresa, políticas, processos, FAQ",
            "analise_estatistica": "Análises, tendências, comparações, insights estatísticos",
            "fora_escopo": "Perguntas fora do domínio do sistema"
        },
        "usage": {
            "endpoint": "POST /test-intent-validator",
            "content_type": "application/json",
            "required_fields": ["pergunta"],
            "optional_fields": ["username", "projeto"]
        }
    }), 200


if __name__ == '__main__':
    print("\n" + "="*80)
    print("🧪 INTENT VALIDATOR TEST ENDPOINT")
    print("="*80)
    print("Servidor iniciado em: http://localhost:5001")
    print("\nEndpoints disponíveis:")
    print("  POST   /test-intent-validator          - Testar validação de intenção")
    print("  GET    /test-intent-validator/health   - Health check")
    print("  GET    /test-intent-validator/examples - Ver exemplos de uso")
    print("\n" + "="*80 + "\n")
    
    app.run(debug=True, port=5001, host='0.0.0.0')
