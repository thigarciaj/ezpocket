"""
Endpoint de teste isolado para History and Preferences Agent
Permite testar o agente independentemente do grafo principal
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Adiciona backend ao path
backend_path = str(Path(__file__).parent.parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Carrega variáveis de ambiente
load_dotenv()

from agents.history_preferences_agent.history_preferences import HistoryPreferencesAgent

app = Flask(__name__)
CORS(app)

# Inicializa o agente
agent = HistoryPreferencesAgent()

@app.route('/health', methods=['GET'])
def health():
    """Verifica se o serviço está rodando"""
    return jsonify({
        "status": "healthy",
        "service": "History and Preferences Agent Test Endpoint",
        "port": 5002,
        "database": f"PostgreSQL - {agent.db_config['host']}:{agent.db_config['port']}/{agent.db_config['database']}",
        "config_loaded": agent.config is not None
    })

@app.route('/test-load-context', methods=['POST'])
def test_load_context():
    """
    Testa o carregamento de contexto do usuário
    
    Body esperado:
    {
        "username": "usuario_teste",
        "projeto": "ezpag",
        "pergunta": "Quantos pedidos tivemos hoje?"
    }
    """
    try:
        data = request.json
        
        # Valida dados obrigatórios
        if not data.get('username'):
            return jsonify({"error": "Campo 'username' é obrigatório"}), 400
        
        if not data.get('projeto'):
            return jsonify({"error": "Campo 'projeto' é obrigatório"}), 400
        
        # Cria estado simulado
        state = {
            "username": data['username'],
            "projeto": data['projeto'],
            "pergunta": data.get('pergunta', '')
        }
        
        # Executa load_context
        result_state = agent.load_context(state)
        
        return jsonify({
            "success": True,
            "username": result_state.get('username'),
            "projeto": result_state.get('projeto'),
            "has_context": result_state.get('has_user_context', False),
            "context": result_state.get('user_context', {})
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/test-save-interaction', methods=['POST'])
def test_save_interaction():
    """
    Testa o salvamento de uma interação
    
    Body esperado:
    {
        "username": "usuario_teste",
        "projeto": "ezpag",
        "pergunta": "Quantos pedidos tivemos hoje?",
        "intent_category": "quantidade"
    }
    """
    try:
        data = request.json
        
        # Valida dados obrigatórios
        if not data.get('username'):
            return jsonify({"error": "Campo 'username' é obrigatório"}), 400
        
        if not data.get('projeto'):
            return jsonify({"error": "Campo 'projeto' é obrigatório"}), 400
        
        if not data.get('pergunta'):
            return jsonify({"error": "Campo 'pergunta' é obrigatório"}), 400
        
        # Cria estado simulado
        state = {
            "username": data['username'],
            "projeto": data['projeto'],
            "pergunta": data['pergunta'],
            "intent_category": data.get('intent_category', 'unknown')
        }
        
        # Adiciona campos opcionais
        optional_fields = ['intent_reason', 'sql_query', 'response', 'execution_time']
        for field in optional_fields:
            if field in data:
                state[field] = data[field]
        
        # Executa save_interaction
        result_state = agent.save_interaction(state)
        
        return jsonify({
            "success": True,
            "interaction_saved": result_state.get('interaction_saved', False),
            "username": result_state.get('username'),
            "projeto": result_state.get('projeto')
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/user-history/<username>/<projeto>', methods=['GET'])
def get_user_history(username: str, projeto: str):
    """
    Obtém histórico de interações do usuário
    
    Query params opcionais:
    - limit: número máximo de itens (default: 10)
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        
        history = agent._get_recent_history(username, projeto, limit)
        
        return jsonify({
            "success": True,
            "username": username,
            "projeto": projeto,
            "history_count": len(history),
            "history": history
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/user-preferences/<username>/<projeto>', methods=['GET'])
def get_user_preferences(username: str, projeto: str):
    """Obtém preferências do usuário"""
    try:
        preferences = agent.get_preferences(username, projeto)
        
        return jsonify({
            "success": True,
            "username": username,
            "projeto": projeto,
            "preferences_count": len(preferences),
            "preferences": preferences
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/user-preferences/<username>/<projeto>', methods=['POST'])
def update_user_preferences(username: str, projeto: str):
    """
    Atualiza preferências do usuário
    
    Body esperado:
    {
        "category": "visualization",
        "preferences": {
            "chart_type": "bar",
            "color_scheme": "corporate"
        },
        "confidence": 1.0
    }
    """
    try:
        data = request.json
        
        if not data.get('category'):
            return jsonify({"error": "Campo 'category' é obrigatório"}), 400
        
        if not data.get('preferences'):
            return jsonify({"error": "Campo 'preferences' é obrigatório"}), 400
        
        success = agent.update_preferences(
            username=username,
            projeto=projeto,
            category=data['category'],
            preferences=data['preferences'],
            confidence=data.get('confidence', 1.0)
        )
        
        return jsonify({
            "success": success,
            "username": username,
            "projeto": projeto,
            "category": data['category']
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/user-patterns/<username>/<projeto>', methods=['GET'])
def get_user_patterns(username: str, projeto: str):
    """Obtém padrões identificados do usuário"""
    try:
        patterns = agent._get_user_patterns(username, projeto)
        
        return jsonify({
            "success": True,
            "username": username,
            "projeto": projeto,
            "patterns_count": len(patterns),
            "patterns": patterns
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/module-logs/<username>/<projeto>', methods=['GET'])
def get_module_logs(username: str, projeto: str):
    """
    Obtém logs de execução dos módulos
    
    Query params opcionais:
    - module_name: filtra por módulo específico
    - limit: número máximo de logs (default: 50)
    """
    try:
        module_name = request.args.get('module_name', None)
        limit = request.args.get('limit', 50, type=int)
        
        logs = agent.get_module_logs(username, projeto, module_name, limit)
        
        return jsonify({
            "success": True,
            "username": username,
            "projeto": projeto,
            "module_name": module_name,
            "logs_count": len(logs),
            "logs": logs
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/module-logs', methods=['POST'])
def log_module_execution():
    """
    Registra execução de um módulo
    
    Body esperado:
    {
        "module_name": "intent_validator",
        "state": {"username": "joao", "projeto": "ezpag"},
        "module_input": {"pergunta": "..."},
        "module_output": {"intent_valid": true},
        "execution_time": 0.5,
        "success": true,
        "error_message": null
    }
    """
    try:
        data = request.json
        
        if not data.get('module_name'):
            return jsonify({"error": "Campo 'module_name' é obrigatório"}), 400
        
        success = agent.log_module_execution(
            module_name=data['module_name'],
            state=data.get('state', {}),
            module_input=data.get('module_input', {}),
            module_output=data.get('module_output', {}),
            execution_time=data.get('execution_time', 0.0),
            success=data.get('success', True),
            error_message=data.get('error_message')
        )
        
        return jsonify({
            "success": success,
            "module_name": data['module_name']
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/examples', methods=['GET'])
def examples():
    """Retorna exemplos de uso da API"""
    return jsonify({
        "service": "History and Preferences Agent Test Endpoint",
        "port": 5002,
        "examples": {
            "1_load_context": {
                "description": "Carregar contexto do usuário",
                "method": "POST",
                "endpoint": "/test-load-context",
                "body": {
                    "username": "joao_silva",
                    "projeto": "ezpag",
                    "pergunta": "Quantos pedidos tivemos hoje?"
                }
            },
            "2_save_interaction": {
                "description": "Salvar uma interação",
                "method": "POST",
                "endpoint": "/test-save-interaction",
                "body": {
                    "username": "joao_silva",
                    "projeto": "ezpag",
                    "pergunta": "Quantos pedidos tivemos hoje?",
                    "intent_category": "quantidade",
                    "intent_reason": "Pergunta sobre contagem de pedidos"
                }
            },
            "3_get_history": {
                "description": "Obter histórico do usuário",
                "method": "GET",
                "endpoint": "/user-history/joao_silva/ezpag?limit=10"
            },
            "4_get_preferences": {
                "description": "Obter preferências do usuário",
                "method": "GET",
                "endpoint": "/user-preferences/joao_silva/ezpag"
            },
            "5_update_preferences": {
                "description": "Atualizar preferências do usuário",
                "method": "POST",
                "endpoint": "/user-preferences/joao_silva/ezpag",
                "body": {
                    "category": "visualization",
                    "preferences": {
                        "chart_type": "bar",
                        "color_scheme": "corporate"
                    },
                    "confidence": 1.0
                }
            },
            "6_get_patterns": {
                "description": "Obter padrões identificados",
                "method": "GET",
                "endpoint": "/user-patterns/joao_silva/ezpag"
            },
            "7_view_database": {
                "description": "Ver todos os dados do banco (debug)",
                "method": "GET",
                "endpoint": "/debug/view-database"
            }
        }
    })

@app.route('/debug/view-database', methods=['GET'])
def view_database():
    """
    Endpoint de debug para visualizar todo o conteúdo do banco de dados
    """
    try:
        import sqlite3
        
        conn = sqlite3.connect(agent.db_path)
        conn.row_factory = sqlite3.Row  # Para retornar dicts
        cursor = conn.cursor()
        
        result = {
            "database_path": agent.db_path,
            "tables": {}
        }
        
        # Lista todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Para cada tabela, pega todos os dados
        for table in tables:
            cursor.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT 50")
            rows = cursor.fetchall()
            
            # Converte para lista de dicts
            result["tables"][table] = {
                "count": len(rows),
                "rows": [dict(row) for row in rows]
            }
        
        conn.close()
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🧠 HISTORY AND PREFERENCES AGENT - TEST ENDPOINT")
    print("="*80)
    print(f"Servidor rodando em: http://localhost:5002")
    print(f"Health check: http://localhost:5002/health")
    print(f"Exemplos: http://localhost:5002/examples")
    print(f"Debug Database: http://localhost:5002/debug/view-database")
    print("="*80 + "\n")
    
    app.run(host='0.0.0.0', port=5002, debug=True)
