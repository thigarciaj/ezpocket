"""
Endpoint de teste para o Analysis Orchestrator Agent
Permite testar o gerador de queries SQL isoladamente
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

from agents.analysis_orchestrator_agent.analysis_orchestrator import AnalysisOrchestratorAgent

app = Flask(__name__)
CORS(app)

# Inicializa o agente
analysis_orchestrator = AnalysisOrchestratorAgent()


@app.route('/test-analysis-orchestrator', methods=['POST'])
def test_analysis_orchestrator():
    """
    Endpoint para testar o Analysis Orchestrator Agent isoladamente
    
    Request body:
    {
        "pergunta": "string",
        "plan": "string",
        "intent_category": "string" (opcional),
        "username": "string" (opcional),
        "projeto": "string" (opcional)
    }
    
    Response:
    {
        "success": bool,
        "input": {...},
        "output": {
            "query_sql": string,
            "query_explanation": string,
            "columns_used": list,
            "filters_applied": list,
            "security_validated": bool,
            "optimization_notes": string,
            "execution_time": float
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
        
        intent_category = data.get('intent_category', 'quantidade')
        username = data.get('username', 'test_user')
        projeto = data.get('projeto', 'test_project')
        
        # Cria estado de entrada
        state = {
            "pergunta": pergunta,
            "plan": plan,
            "intent_category": intent_category,
            "username": username,
            "projeto": projeto
        }
        
        print(f"\n{'='*80}")
        print(f"[TEST ENDPOINT] Testando Analysis Orchestrator Agent")
        print(f"[TEST ENDPOINT] Pergunta: {pergunta}")
        print(f"[TEST ENDPOINT] Plano: {plan[:100]}..." if len(plan) > 100 else f"[TEST ENDPOINT] Plano: {plan}")
        print(f"[TEST ENDPOINT] Categoria: {intent_category}")
        print(f"[TEST ENDPOINT] Username: {username}")
        print(f"[TEST ENDPOINT] Projeto: {projeto}")
        print(f"{'='*80}\n")
        
        # Gera query SQL
        result = analysis_orchestrator.generate_query(state)
        
        # Prepara resposta
        if result.get('error'):
            response = {
                "success": False,
                "input": {
                    "pergunta": pergunta,
                    "plan": plan,
                    "intent_category": intent_category,
                    "username": username,
                    "projeto": projeto
                },
                "error": result.get('error'),
                "execution_time": result.get('execution_time')
            }
        else:
            response = {
                "success": True,
                "input": {
                    "pergunta": pergunta,
                    "plan": plan,
                    "intent_category": intent_category,
                    "username": username,
                    "projeto": projeto
                },
                "output": {
                    "query_sql": result.get('query_sql', ''),
                    "query_explanation": result.get('query_explanation', ''),
                    "columns_used": result.get('columns_used', []),
                    "filters_applied": result.get('filters_applied', []),
                    "security_validated": result.get('security_validated', False),
                    "optimization_notes": result.get('optimization_notes', ''),
                    "execution_time": result.get('execution_time')
                }
            }
        
        print(f"\n{'='*80}")
        print(f"[TEST ENDPOINT] Resultado:")
        if result.get('error'):
            print(f"[TEST ENDPOINT] ❌ Erro: {result.get('error')}")
        else:
            print(f"[TEST ENDPOINT] ✅ Query SQL gerada")
            print(f"[TEST ENDPOINT] 🔒 Segurança: {result.get('security_validated')}")
            print(f"[TEST ENDPOINT] 📊 Colunas: {len(result.get('columns_used', []))}")
            print(f"[TEST ENDPOINT] 🎯 Filtros: {len(result.get('filters_applied', []))}")
            print(f"[TEST ENDPOINT] ⏱️  Tempo: {result.get('execution_time', 0):.2f}s")
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
        "agent": "AnalysisOrchestratorAgent",
        "version": "1.0.0"
    }), 200


@app.route('/info', methods=['GET'])
def info():
    """Retorna informações sobre o agente"""
    return jsonify({
        "agent": "AnalysisOrchestratorAgent",
        "description": "Motor principal que transforma planos em queries SQL otimizadas para AWS Athena",
        "capabilities": [
            "Transformar planos em queries SQL",
            "Validar segurança de queries",
            "Otimizar queries para Athena",
            "Aplicar regras semânticas de negócio",
            "Prevenir acesso a dados sensíveis"
        ],
        "endpoints": {
            "/test-analysis-orchestrator": "POST - Testa geração de query",
            "/health": "GET - Health check",
            "/info": "GET - Informações do agente"
        }
    }), 200


if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 INICIANDO SERVIDOR DE TESTE - ANALYSIS ORCHESTRATOR AGENT")
    print("="*80)
    print("📡 Porta: 5012")
    print("🔗 Endpoints disponíveis:")
    print("   POST /test-analysis-orchestrator - Testa geração de query")
    print("   GET  /health - Health check")
    print("   GET  /info - Informações do agente")
    print("="*80 + "\n")
    
    app.run(host='0.0.0.0', port=5012, debug=True)
