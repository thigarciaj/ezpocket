#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test endpoint for AutoCorrectionAgent
Provides a Flask server to test SQL correction functionality
Port: 5015
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

from agents.auto_correction_agent.auto_correction import AutoCorrectionAgent

app = Flask(__name__)
CORS(app)

# Initialize agent
correction_agent = AutoCorrectionAgent()

@app.route('/test-auto-correction', methods=['POST'])
def test_auto_correction():
    """
    Test endpoint for SQL correction
    
    Expected JSON body:
    {
        "query_original": "INSERT INTO orders (id, amount) VALUES (1, 100)",
        "validation_issues": ["Operação proibida: INSERT"],
        "username": "test_user",
        "projeto": "test_project"
    }
    """
    try:
        data = request.json
        
        # Validate required fields
        if 'query_original' not in data:
            return jsonify({
                'error': 'Campo obrigatório ausente: query_original'
            }), 400
        
        if 'validation_issues' not in data:
            return jsonify({
                'error': 'Campo obrigatório ausente: validation_issues'
            }), 400
        
        # Call correct
        result = correction_agent.correct(
            query_original=data['query_original'],
            validation_issues=data['validation_issues'],
            username=data.get('username', 'test_user'),
            projeto=data.get('projeto', 'test_project'),
            schema_context=data.get('schema_context')
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
    return jsonify({'status': 'healthy', 'agent': 'AutoCorrectionAgent'}), 200

if __name__ == '__main__':
    print("🚀 Starting AutoCorrectionAgent Test Server on port 5015...")
    print("📍 Endpoints:")
    print("   POST /test-auto-correction - Test SQL correction")
    print("   GET  /health - Health check")
    print("\n💡 Aguardando requisições...")
    
    app.run(host='0.0.0.0', port=5015, debug=True)
