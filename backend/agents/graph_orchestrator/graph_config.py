"""
GRAPH_CONFIG - Configuração Central do Grafo
============================================
Defina aqui as conexões entre módulos.
O output de um módulo vira input do próximo.

IMPORTANTE: Este arquivo é a ÚNICA fonte de verdade para as conexões do grafo.
O graph_orchestrator.py importa diretamente daqui.
"""

# =====================================================
# CONFIGURAÇÃO DAS CONEXÕES DO GRAFO (Formato Worker)
# =====================================================
# Formato: módulo → [lista de módulos destino]
# Múltiplos destinos = execução PARALELA (branches)

GRAPH_CONNECTIONS = {
    # Intent Validator → [Plan Builder, History Preferences] (paralelo)
    "intent_validator": ["plan_builder", "history_preferences"],
    
    # Plan Builder → [Plan Confirm, History Preferences] (paralelo)
    "plan_builder": ["plan_confirm", "history_preferences"],
    
    # Plan Confirm → History Preferences (se aceito) OU [User Proposed Plan, History] (se rejeitado)
    "plan_confirm": ["history_preferences"],  # Condicional definido no orchestrator
    
    # User Proposed Plan → History Preferences (apenas registra e encerra)
    "user_proposed_plan": ["history_preferences"],
    
    # Analysis Orchestrator → History Preferences (gera query e registra)
    "analysis_orchestrator": ["history_preferences"],
    
    # History Preferences → (fim)
    "history_preferences": [],
}

# =====================================================
# CONFIGURAÇÃO DETALHADA (Para documentação e UI)
# =====================================================

GRAPH_CONNECTIONS_DETAILED = {
    # Intent Validator → [Plan Builder, History Preferences] (paralelo)
    "intent_validator": {
        "connected_to": ["plan_builder", "history_preferences"],
        "description": "Intent Validator deposita em paralelo para Plan Builder e History"
    },
    
    # Plan Builder → [Plan Confirm, History Preferences] (paralelo)
    "plan_builder": {
        "connected_to": ["plan_confirm", "history_preferences"],
        "description": "Plan Builder gera plano e deposita em paralelo para Plan Confirm e History"
    },
    
    # Plan Confirm → History Preferences (se aceito) OU [User Proposed Plan, History] (se rejeitado)
    "plan_confirm": {
        "connected_to": ["history_preferences"],  # Removido, usar apenas conditional_routes
        "conditional_routes": {
            "accepted": ["analysis_orchestrator", "history_preferences"],  # Se aceito: 2 paralelos
            "rejected": ["user_proposed_plan", "history_preferences"]  # Se rejeitado: 2 paralelos
        },
        "description": "Plan Confirm solicita confirmação. Se aceito, vai para Analysis Orchestrator e History. Se rejeitado, vai para User Proposed Plan e History"
    },
    
    # User Proposed Plan → History Preferences (recebe sugestão e apenas registra)
    "user_proposed_plan": {
        "connected_to": ["history_preferences"],
        "description": "User Proposed Plan recebe sugestão do usuário, registra no histórico e encerra"
    },
    
    # Analysis Orchestrator → History Preferences (gera query SQL e registra)
    "analysis_orchestrator": {
        "connected_to": ["history_preferences"],
        "description": "Analysis Orchestrator transforma plano em query SQL otimizada, valida segurança e registra no histórico"
    },
    
    # History Preferences → (fim)
    "history_preferences": {
        "connected_to": [],
        "description": "History Preferences salva contexto e encerra"
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
# EXPECTED FLOW (Para display no test_client)
# =====================================================

EXPECTED_FLOW = {
    "intent_validator": "intent_validator -> [plan_builder, history] -> [plan_confirm, history] -> [analysis_orchestrator, history] (aceito) OU [user_proposed, history] (rejeitado)",
    "plan_builder": "plan_builder -> [plan_confirm, history] -> conditional",
    "plan_confirm": "plan_confirm -> [analysis_orchestrator, history] (aceito - 2 paralelos) OU [user_proposed, history] (rejeitado - 2 paralelos)",
    "analysis_orchestrator": "analysis_orchestrator -> history -> FIM (gera query SQL)",
    "user_proposed_plan": "user_proposed_plan -> history -> FIM (registra sugestão)",
    "history_preferences": "history_preferences (final)",
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
    
    "analysis_orchestrator": {
        "function": "generate_query",
        "input_fields": [
            "username",
            "projeto",
            "pergunta",
            "plan",
            "plan_steps"
        ],
        "output_fields": [
            "query_sql",
            "query_explanation",
            "columns_used",
            "filters_applied",
            "security_validated",
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
