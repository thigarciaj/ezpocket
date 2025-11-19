#!/usr/bin/env python3
"""
Worker para Athena Executor Agent
"""

import sys
import os
from pathlib import Path

# Adicionar paths
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

from agents.graph_orchestrator.graph_orchestrator import ModuleWorker
from agents.athena_executor_agent.athena_executor import AthenaExecutorAgent
from typing import Dict, Any

class AthenaExecutorWorker(ModuleWorker):
    """Worker para o módulo athena_executor"""
    
    def __init__(self):
        super().__init__('athena_executor')
        self.agent = AthenaExecutorAgent()
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa execução de query no Athena
        
        Input esperado (de SQL Validator OU Auto Correction):
            - query_validated: str (query final a executar)
            - query_corrected: str (se veio do auto_correction)
            - username: str
            - projeto: str
            - pergunta: str
            
        Output:
            - success: bool
            - query_executed: str
            - execution_time_seconds: float
            - row_count: int
            - column_count: int
            - columns: list
            - results_preview: list (primeiras 100 linhas)
            - data_size_mb: float
            - database: str
            - region: str
            - error: str ou None
        """
        
        # Determinar qual query executar
        # Prioridade: query_corrected (do auto_correction) > query_validated (do sql_validator)
        query_sql = data.get('query_corrected') or data.get('query_validated') or data.get('query_sql', '')
        username = data.get('username', 'unknown')
        projeto = data.get('projeto', 'default')
        
        # Detectar de onde veio (sql_validator ou auto_correction)
        came_from_correction = 'query_corrected' in data
        came_from_validator = 'query_validated' in data and not came_from_correction
        
        print(f"[ATHENA_EXECUTOR] 🚀 Executando query no Athena...")
        print(f"[ATHENA_EXECUTOR]    Username: {username}")
        print(f"[ATHENA_EXECUTOR]    Projeto: {projeto}")
        print(f"[ATHENA_EXECUTOR]    Origem: {'AutoCorrection' if came_from_correction else 'SQLValidator'}")
        
        # Executar query
        result = self.agent.execute(
            query_sql=query_sql,
            username=username,
            projeto=projeto
        )
        
        print(f"[ATHENA_EXECUTOR] ✅ Execução concluída")
        print(f"[ATHENA_EXECUTOR]    Success: {result['success']}")
        print(f"[ATHENA_EXECUTOR]    Rows: {result['row_count']}")
        
        # Adicionar campos necessários para history
        output = {
            **result,
            'previous_module': 'athena_executor',
            'pergunta': data.get('pergunta', ''),
            'username': username,
            'projeto': projeto,
            'intent_category': data.get('intent_category'),
            'plan': data.get('plan'),
            # Parent IDs para rastreabilidade
            'parent_auto_correction_id': data.get('parent_id') if came_from_correction else None,
            'parent_sql_validator_id': data.get('parent_id') if came_from_validator else data.get('parent_sql_validator_id'),
            'parent_analysis_orchestrator_id': data.get('parent_analysis_orchestrator_id'),
            'parent_plan_confirm_id': data.get('parent_plan_confirm_id'),
            'parent_plan_builder_id': data.get('parent_plan_builder_id'),
            'parent_intent_validator_id': data.get('parent_intent_validator_id'),
            # Próximo módulo: history_preferences (salvar athena_executor)
            '_next_modules': ['history_preferences']
        }
        
        print(f"[ATHENA_EXECUTOR] 🔀 Próximo módulo: history_preferences")
        
        return output


if __name__ == '__main__':
    worker = AthenaExecutorWorker()
    worker.start()
