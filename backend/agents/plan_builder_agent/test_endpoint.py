"""
Endpoint de teste para o Plan Builder Agent
Permite testar o nó de construção de plano isoladamente
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

from agents.plan_builder_agent.plan_builder import PlanBuilderAgent

app = Flask(__name__)
CORS(app)

# Inicializa o agente
plan_builder = PlanBuilderAgent()


@app.route('/test-plan-builder', methods=['POST'])
def test_plan_builder():
    """
    Endpoint para testar o Plan Builder Agent isoladamente
    
    Request body:
    {
        "pergunta": "string",
        "intent_category": "string",
        "username": "string" (opcional),
        "projeto": "string" (opcional)
    }
    
    Response:
    {
        "success": bool,
        "input": {
            "pergunta": string,
            "intent_category": string,
            "username": string,
            "projeto": string
        },
        "output": {
            "plan": string,
            "plan_steps": list[string],
            "estimated_complexity": string,
            "data_sources": list[string],
            "output_format": string,
            "execution_time": float,
            "model_used": string,
            "tokens_used": int
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
        intent_category = data.get('intent_category', '')
        
        if not pergunta:
            return jsonify({
                "success": False,
                "error": "Campo 'pergunta' é obrigatório"
            }), 400
        
        if not intent_category:
            return jsonify({
                "success": False,
                "error": "Campo 'intent_category' é obrigatório"
            }), 400
        
        username = data.get('username', 'test_user')
        projeto = data.get('projeto', 'test_project')
        
        # Cria estado de entrada
        state = {
            "pergunta": pergunta,
            "intent_category": intent_category,
            "username": username,
            "projeto": projeto
        }
        
        print(f"\n{'='*80}")
        print(f"[TEST ENDPOINT] Testando Plan Builder Agent")
        print(f"[TEST ENDPOINT] Pergunta: {pergunta}")
        print(f"[TEST ENDPOINT] Categoria: {intent_category}")
        print(f"[TEST ENDPOINT] Username: {username}")
        print(f"[TEST ENDPOINT] Projeto: {projeto}")
        print(f"{'='*80}\n")
        
        # Executa construção do plano
        result = plan_builder.build_plan(state)
        
        # Prepara resposta
        response = {
            "success": True,
            "input": {
                "pergunta": pergunta,
                "intent_category": intent_category,
                "username": username,
                "projeto": projeto
            },
            "output": {
                "plan": result.get("plan"),
                "plan_steps": result.get("plan_steps"),
                "estimated_complexity": result.get("estimated_complexity"),
                "data_sources": result.get("data_sources"),
                "output_format": result.get("output_format"),
                "execution_time": result.get("execution_time"),
                "model_used": result.get("model_used"),
                "tokens_used": result.get("tokens_used")
            }
        }
        
        print(f"\n{'='*80}")
        print(f"[TEST ENDPOINT] ✅ Plano construído com sucesso")
        print(f"[TEST ENDPOINT] Complexidade: {result.get('estimated_complexity')}")
        print(f"[TEST ENDPOINT] Passos: {len(result.get('plan_steps', []))}")
        print(f"{'='*80}\n")
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"\n[TEST ENDPOINT] ❌ ERRO: {str(e)}\n")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/test-plan-builder/health', methods=['GET'])
def health():
    """Health check do endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Plan Builder Test Endpoint",
        "agent": "PlanBuilderAgent",
        "version": "1.0.0"
    }), 200


@app.route('/test-plan-builder/examples', methods=['GET'])
def examples():
    """Retorna exemplos de uso do endpoint"""
    return jsonify({
        "examples": [
            {
                "name": "Análise Simples - Contagem",
                "request": {
                    "pergunta": "Quantos pedidos tivemos em outubro?",
                    "intent_category": "quantidade",
                    "username": "joao.silva",
                    "projeto": "ezpocket"
                },
                "expected_result": {
                    "estimated_complexity": "baixa",
                    "plan_steps_count": 3,
                    "data_sources": ["orders_table"]
                }
            },
            {
                "name": "Análise Média - Com Filtros",
                "request": {
                    "pergunta": "Qual o valor total de vendas do cliente ABC nos últimos 3 meses?",
                    "intent_category": "quantidade",
                    "username": "maria.costa",
                    "projeto": "ezpocket"
                },
                "expected_result": {
                    "estimated_complexity": "média",
                    "plan_steps_count": 4,
                    "data_sources": ["orders_table", "customers_table"]
                }
            },
            {
                "name": "Análise Complexa - Estatística",
                "request": {
                    "pergunta": "Compare a tendência de crescimento entre os últimos 6 meses",
                    "intent_category": "analise_estatistica",
                    "username": "pedro.santos",
                    "projeto": "ezpocket"
                },
                "expected_result": {
                    "estimated_complexity": "alta",
                    "plan_steps_count": 5,
                    "data_sources": ["orders_table", "analytics_view"]
                }
            },
            {
                "name": "Conhecimentos Gerais - FAQ",
                "request": {
                    "pergunta": "O que é a EZPocket e como funciona?",
                    "intent_category": "conhecimentos_gerais",
                    "username": "ana.lima",
                    "projeto": "ezpocket"
                },
                "expected_result": {
                    "estimated_complexity": "baixa",
                    "plan_steps_count": 2,
                    "data_sources": ["faq_database", "knowledge_base"]
                }
            },
            {
                "name": "Análise Multi-Fonte",
                "request": {
                    "pergunta": "Liste os top 10 clientes por receita e suas últimas compras",
                    "intent_category": "quantidade",
                    "username": "carlos.mendes",
                    "projeto": "ezpocket"
                },
                "expected_result": {
                    "estimated_complexity": "média",
                    "plan_steps_count": 4,
                    "data_sources": ["customers_table", "orders_table", "order_items_table"]
                }
            }
        ],
        "categories": {
            "quantidade": "Perguntas sobre valores numéricos, contagens - geralmente baixa a média complexidade",
            "conhecimentos_gerais": "FAQ e informações gerais - baixa complexidade",
            "analise_estatistica": "Análises, tendências, comparações - média a alta complexidade"
        },
        "complexity_levels": {
            "baixa": "Consultas simples, 1-3 passos, uma ou duas fontes de dados",
            "média": "Consultas com filtros, agregações, joins - 3-5 passos",
            "alta": "Análises complexas, múltiplas agregações, cálculos estatísticos - 5+ passos"
        },
        "usage": {
            "endpoint": "POST /test-plan-builder",
            "content_type": "application/json",
            "required_fields": ["pergunta", "intent_category"],
            "optional_fields": ["username", "projeto"]
        }
    }), 200


if __name__ == '__main__':
    print("\n" + "="*80)
    print("🧪 PLAN BUILDER TEST ENDPOINT")
    print("="*80)
    print("Servidor iniciado em: http://localhost:5009")
    print("\nEndpoints disponíveis:")
    print("  POST   /test-plan-builder          - Testar construção de plano")
    print("  GET    /test-plan-builder/health   - Health check")
    print("  GET    /test-plan-builder/examples - Ver exemplos de uso")
    print("\n" + "="*80 + "\n")
    
    app.run(debug=True, port=5009, host='0.0.0.0')
