#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test endpoint for SQLValidatorAgent
Provides a Flask server to test SQL validation functionality
Port: 5014
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

from agents.sql_validator_agent.sql_validator import SQLValidatorAgent

app = Flask(__name__)
CORS(app)

# Initialize agent
validator_agent = SQLValidatorAgent()

@app.route('/test-sql-validator', methods=['POST'])
def test_sql_validator():
    """
    Test endpoint for SQL validation
    
    Expected JSON body:
    {
        "query_sql": "SELECT COUNT(*) FROM orders",
        "estimated_complexity": "baixa",
        "username": "test_user",
        "projeto": "test_project"
    }
    """
    try:
        data = request.json
        
        # Validate required fields
        if 'query_sql' not in data:
            return jsonify({
                'error': 'Campo obrigatório ausente: query_sql'
            }), 400
        
        # Call validate
        result = validator_agent.validate(
            query_sql=data['query_sql'],
            username=data.get('username', 'test_user'),
            projeto=data.get('projeto', 'test_project'),
            estimated_complexity=data.get('estimated_complexity', 'média')
        )
        
        return jsonify({
            'success': True,
            'result': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'type': type(e).__name__
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'agent': 'SQLValidatorAgent'}), 200

if __name__ == '__main__':
    print("🚀 Starting SQLValidatorAgent Test Server on port 5014...")
    print("📍 Endpoints:")
    print("   POST /test-sql-validator - Test SQL validation")
    print("   GET  /health - Health check")
    print("\n💡 Aguardando requisições...")
    
    port = int(os.getenv('SQL_VALIDATOR_PORT', 5014))
    app.run(host='0.0.0.0', port=port, debug=True)
