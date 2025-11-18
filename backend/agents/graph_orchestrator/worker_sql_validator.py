#!/usr/bin/env python3
"""
Worker para SQL Validator Agent
"""

import sys
import os
from pathlib import Path

# Adicionar paths
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

from agents.graph_orchestrator.graph_orchestrator import ModuleWorker
from agents.sql_validator_agent.sql_validator import SQLValidatorAgent
from typing import Dict, Any

class SQLValidatorWorker(ModuleWorker):
    """Worker para o módulo sql_validator"""
    
    def __init__(self):
        super().__init__('sql_validator')
        self.agent = SQLValidatorAgent()
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa validação de query SQL
        
        Input esperado:
            - query_sql: str (da analysis_orchestrator)
            - username: str
            - projeto: str
            - estimated_complexity: str
            - pergunta: str
            
        Output:
            - valid: bool
            - query_validated: str
            - syntax_valid: bool
            - athena_compatible: bool
            - security_issues: list
            - warnings: list
            - optimization_suggestions: list
            - estimated_scan_size_gb: float
            - estimated_cost_usd: float
            - estimated_execution_time_seconds: float
            - risk_level: str
        """
        
        query_sql = data.get('query_sql', '')
        username = data.get('username', 'unknown')
        projeto = data.get('projeto', 'default')
        estimated_complexity = data.get('estimated_complexity', 'média')
        
        print(f"[SQL_VALIDATOR] 🔍 Validando query SQL...")
        print(f"[SQL_VALIDATOR]    Username: {username}")
        print(f"[SQL_VALIDATOR]    Projeto: {projeto}")
        print(f"[SQL_VALIDATOR]    Complexidade: {estimated_complexity}")
        
        # Validar query
        result = self.agent.validate(
            query_sql=query_sql,
            username=username,
            projeto=projeto,
            estimated_complexity=estimated_complexity
        )
        
        print(f"[SQL_VALIDATOR] ✅ Validação concluída")
        print(f"[SQL_VALIDATOR]    Valid: {result['valid']}")
        print(f"[SQL_VALIDATOR]    Risk Level: {result['risk_level']}")
        print(f"[SQL_VALIDATOR]    Cost: ${result['estimated_cost_usd']} USD")
        
        # Adicionar campos necessários para history
        output = {
            **result,
            'previous_module': 'sql_validator',
            'pergunta': data.get('pergunta', ''),
            'username': username,
            'projeto': projeto,
            'intent_category': data.get('intent_category'),
            'plan': data.get('plan'),
            # Parent IDs para rastreabilidade
            'parent_analysis_orchestrator_id': data.get('parent_id'),
            'parent_plan_confirm_id': data.get('parent_plan_confirm_id'),
            'parent_plan_builder_id': data.get('parent_plan_builder_id'),
            'parent_intent_validator_id': data.get('parent_intent_validator_id'),
            # Próximos módulos: 2x history_preferences (salvar analysis_orchestrator + sql_validator)
            # IMPORTANTE: Primeiro history salva analysis_orchestrator, segundo salva sql_validator
            '_next_modules': ['history_preferences'],
            # Guardar dados do analysis_orchestrator para o history salvar primeiro
            'analysis_orchestrator_data': {
                'previous_module': 'analysis_orchestrator',
                'query_sql': data.get('query_sql', ''),
                'query_explanation': data.get('query_explanation', ''),
                'columns_used': data.get('columns_used', []),
                'filters_applied': data.get('filters_applied', []),
                'security_validated': data.get('security_validated', False),
                'optimization_notes': data.get('optimization_notes', ''),
                'execution_time': data.get('execution_time'),
                'error': data.get('error'),
                'pergunta': data.get('pergunta'),
                'username': username,
                'projeto': projeto,
                'intent_category': data.get('intent_category'),
                'plan': data.get('plan', ''),
                'plan_confirmed': data.get('plan_confirmed', False),
                'intent_valid': data.get('intent_valid'),
                'plan_steps': data.get('plan_steps', []),
                'estimated_complexity': data.get('estimated_complexity', 'média')
            }
        }
        
        print(f"[SQL_VALIDATOR] 🔀 Próximo módulo: history_preferences")
        print(f"[SQL_VALIDATOR] 📝 History vai salvar: analysis_orchestrator + sql_validator")
        
        return output


if __name__ == '__main__':
    worker = SQLValidatorWorker()
    worker.start()
