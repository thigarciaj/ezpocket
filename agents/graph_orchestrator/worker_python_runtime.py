#!/usr/bin/env python3
"""
Worker para Python Runtime Agent
Recebe resultados do Athena Executor e realiza análise estatística
"""

import sys
import os
import time
from pathlib import Path

# Adicionar paths
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

from agents.graph_orchestrator.graph_orchestrator import ModuleWorker
from agents.python_runtime_agent.python_runtime import PythonRuntimeAgent
from typing import Dict, Any

class PythonRuntimeWorker(ModuleWorker):
    """Worker para o módulo python_runtime"""
    
    def __init__(self):
        super().__init__('python_runtime')
        self.agent = PythonRuntimeAgent()
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa análise estatística dos resultados
        
        Input esperado (de Athena Executor):
            - results_full: list (todos os resultados)
            - results_preview: list (primeiras 100 linhas)
            - query_executed: str
            - pergunta: str
            - username: str
            - projeto: str
            - row_count: int
            - columns: list
            - parent_athena_executor_id: int (FK para athena_executor)
            - todos os parent_ids necessários
            
        Output:
            - analysis_summary: str
            - statistics: dict
            - insights: list
            - visualizations: list
            - recommendations: list
            - analysis_type: str
            - parent_athena_executor_id: int (repassado para history)
            - _next_modules: ['history_preferences']
        """
        
        # Extrair dados do input
        results_full = data.get('results_full', [])
        results_preview = data.get('results_preview', [])
        query_executed = data.get('query_executed', '')
        pergunta = data.get('pergunta', '')
        username = data.get('username', 'unknown')
        projeto = data.get('projeto', 'default')
        row_count = data.get('row_count', 0)
        columns = data.get('columns', [])
        
        print(f"[PYTHON_RUNTIME] 🐍 Processando análise estatística Python...")
        print(f"[PYTHON_RUNTIME]    Username: {username}")
        print(f"[PYTHON_RUNTIME]    Projeto: {projeto}")
        print(f"[PYTHON_RUNTIME]    Pergunta: {pergunta}")
        print(f"[PYTHON_RUNTIME]    Rows para análise: {row_count}")
        
        # Medir tempo de execução
        start_time = time.time()
        
        # Executar análise - passar data completo como state
        result = self.agent.execute(data)
        
        execution_time = time.time() - start_time
        
        print(f"[PYTHON_RUNTIME] ✅ Análise Python concluída")
        print(f"[PYTHON_RUNTIME]    Insights gerados: {len(result.get('insights', []))}")
        print(f"[PYTHON_RUNTIME]    Recomendações: {len(result.get('recommendations', []))}")
        print(f"[PYTHON_RUNTIME]    Tempo de execução: {execution_time:.2f}s")
        
        # Preparar output - History vai buscar o parent_athena_executor_id
        output = {
            'previous_module': 'python_runtime',
            'pergunta': pergunta,
            'username': username,
            'projeto': projeto,
            # Repassar TODOS os parent_ids recebidos do athena_executor
            'parent_athena_executor_id': data.get('parent_athena_executor_id'),
            'parent_auto_correction_id': data.get('parent_auto_correction_id'),
            'parent_sql_validator_id': data.get('parent_sql_validator_id'),
            'parent_analysis_orchestrator_id': data.get('parent_analysis_orchestrator_id'),
            'parent_plan_confirm_id': data.get('parent_plan_confirm_id'),
            'parent_plan_builder_id': data.get('parent_plan_builder_id'),
            'parent_intent_validator_id': data.get('parent_intent_validator_id'),
            # Resultados da análise
            **result,
            # Tempo de execução
            'execution_time': execution_time,
            # Próximos módulos: response_composer (formatar resposta) e history_preferences (salvar python_runtime)
            '_next_modules': ['response_composer', 'history_preferences']
        }
        
        print(f"[PYTHON_RUNTIME] 🔀 Enviando análise Python para: response_composer, history_preferences")
        print(f"[PYTHON_RUNTIME] 📝 Dados incluem: statistics, insights, visualizations, recommendations")
        
        return output


if __name__ == '__main__':
    worker = PythonRuntimeWorker()
    worker.start()
