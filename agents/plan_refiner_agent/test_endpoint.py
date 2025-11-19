#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test endpoint for PlanRefinerAgent
Provides a Flask server to test plan refinement functionality
Port: 5013
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

from agents.plan_refiner_agent.plan_refiner import PlanRefinerAgent

app = Flask(__name__)
CORS(app)

# Initialize agent
refiner_agent = PlanRefinerAgent()

@app.route('/test-plan-refiner', methods=['POST'])
def test_plan_refiner():
    """
    Test endpoint for plan refinement
    
    Expected JSON body:
    {
        "pergunta": "Qual o valor total de vendas?",
        "original_plan": "Para responder...",
        "user_suggestion": "Inclua filtro por data",
        "intent_category": "analise_vendas"
    }
    """
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['pergunta', 'original_plan', 'user_suggestion', 'intent_category']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Campo obrigatório ausente: {field}'
                }), 400
        
        # Call refine_plan
        result = refiner_agent.refine_plan(
            pergunta=data['pergunta'],
            original_plan=data['original_plan'],
            user_suggestion=data['user_suggestion'],
            intent_category=data['intent_category']
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
    return jsonify({'status': 'healthy', 'agent': 'PlanRefinerAgent'}), 200

if __name__ == '__main__':
    print("🚀 Starting PlanRefinerAgent Test Server on port 5013...")
    print("📍 Endpoints:")
    print("   POST /test-plan-refiner - Test plan refinement")
    print("   GET  /health - Health check")
    print("\n💡 Aguardando requisições...")
    
    port = int(os.getenv('PLAN_REFINER_PORT', 5013))
    app.run(host='0.0.0.0', port=port, debug=True)
