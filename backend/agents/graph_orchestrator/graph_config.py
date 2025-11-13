"""
GRAPH_CONFIG - Configuração Central do Grafo
============================================
Defina aqui as conexões entre módulos.
O output de um módulo vira input do próximo.
"""

# =====================================================
# CONFIGURAÇÃO DAS CONEXÕES DO GRAFO
# =====================================================

GRAPH_CONNECTIONS = {
    # Intent Validator → History Preferences
    "intent_validator": {
        "connected_to": ["history_preferences"],
        "description": "Intent Validator deposita dados no History Preferences"
    },
    
    # History Preferences → (adicione conexões futuras aqui)
    "history_preferences": {
        "connected_to": [],  # Por enquanto não conecta com ninguém
        "description": "History Preferences armazena contexto"
    },
    
    # Router → (quando implementar)
    "router": {
        "connected_to": [],
        "description": "Router direciona para Generator"
    },
    
    # Generator → (quando implementar)
    "generator": {
        "connected_to": [],
        "description": "Generator cria SQL e passa para Responder"
    },
    
    # Responder → (quando implementar)
    "responder": {
        "connected_to": [],
        "description": "Responder é o nó final"
    }
}

# =====================================================
# MAPEAMENTO DE MÓDULOS PARA SUAS FUNÇÕES
# =====================================================

MODULE_PROCESSORS = {
    "intent_validator": {
        "function": "validate_intent",
        "input_fields": ["username", "projeto", "pergunta"],
        "output_fields": [
            "intent_valid",
            "intent_category",
            "intent_reason",
            "is_special_case",
            "security_violation",
            "execution_time"
        ]
    },
    
    "history_preferences": {
        "function": "load_context",
        "input_fields": [
            "username",
            "projeto",
            "pergunta",
            "intent_category",  # Recebe do intent_validator
            "intent_valid"       # Recebe do intent_validator
        ],
        "output_fields": [
            "user_preferences",
            "user_patterns",
            "interaction_count",
            "context_summary",
            "relevant_history_found",
            "execution_time"
        ]
    },
    
    "router": {
        "function": "route_query",
        "input_fields": [
            "pergunta",
            "intent_category",
            "context_summary"
        ],
        "output_fields": [
            "route",
            "route_reason",
            "confidence_score",
            "query_type"
        ]
    },
    
    "generator": {
        "function": "generate_sql",
        "input_fields": [
            "pergunta",
            "route",
            "query_type"
        ],
        "output_fields": [
            "sql_query",
            "query_valid",
            "tables_used",
            "rows_returned"
        ]
    },
    
    "responder": {
        "function": "generate_response",
        "input_fields": [
            "pergunta",
            "sql_query",
            "query_results"
        ],
        "output_fields": [
            "resposta",
            "resposta_format",
            "charts_generated"
        ]
    }
}

# =====================================================
# URLS DOS SERVIÇOS
# =====================================================

SERVICE_URLS = {
    "intent_validator": "http://localhost:5001",
    "history_preferences": "http://localhost:5002",
    "router": "http://localhost:5005",
    "generator": "http://localhost:5006",
    "responder": "http://localhost:5007"
}
