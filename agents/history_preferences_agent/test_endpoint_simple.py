"""
Endpoint de teste SIMPLES para History and Preferences Agent
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
from pathlib import Path

# Adiciona backend ao path
backend_path = str(Path(__file__).parent.parent.parent)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

print("Importando HistoryPreferencesAgent...")
from agents.history_preferences_agent.history_preferences import HistoryPreferencesAgent

print("Criando Flask app...")
app = Flask(__name__)
CORS(app)

print("Inicializando agente...")
agent = HistoryPreferencesAgent()

@app.route('/health', methods=['GET'])
def health():
    """Verifica se o serviço está rodando"""
    return jsonify({
        "status": "healthy",
        "service": "History and Preferences Agent - SIMPLE",
        "port": 5002
    })

@app.route('/test-save', methods=['POST'])
def test_save():
    """Salva uma interação"""
    try:
        data = request.json
        state = {
            "username": data.get('username', 'test'),
            "projeto": data.get('projeto', 'test'),
            "pergunta": data.get('pergunta', ''),
            "intent_category": data.get('intent_category', 'unknown')
        }
        
        result = agent.save_interaction(state)
        
        return jsonify({
            "success": True,
            "saved": result.get('interaction_saved', False)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/debug/view-db', methods=['GET'])
def view_db():
    """Ver conteúdo do banco"""
    try:
        import sqlite3
        conn = sqlite3.connect(agent.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM interaction_history ORDER BY id DESC LIMIT 10")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({"success": True, "data": rows, "total": len(rows)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('HISTORY_PREFERENCES_PORT', 5002))
    print("\n" + "="*80)
    print("🧠 HISTORY PREFERENCES - SERVIDOR SIMPLES")
    print("="*80)
    print(f"Porta: {port}")
    print(f"Health: http://localhost:{port}/health")
    print("="*80 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
