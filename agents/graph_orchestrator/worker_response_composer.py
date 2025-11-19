#!/usr/bin/env python3
"""
Worker para Response Composer Agent
Recebe análise do Python Runtime e formata resposta bonita para o usuário
"""

import sys
import os
import time
from pathlib import Path

# Adicionar paths
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

from agents.graph_orchestrator.graph_orchestrator import ModuleWorker
from agents.response_composer_agent.response_composer import ResponseComposerAgent
from typing import Dict, Any

class ResponseComposerWorker(ModuleWorker):
    """Worker para o módulo response_composer"""
    
    def __init__(self):
        super().__init__('response_composer')
        self.agent = ResponseComposerAgent()
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa formatação da resposta
        
        Input esperado (de Python Runtime):
            - pergunta: str
            - username: str
            - projeto: str
            - analysis_summary: str
            - statistics: dict
            - insights: list
            - recommendations: list
            - visualizations: list
            - row_count: int
            - parent_python_runtime_id: int (será buscado pelo history)
            - todos os parent_ids necessários
            
        Output:
            - response_text: str (resposta formatada em Markdown)
            - response_summary: str
            - key_numbers: list
            - formatting_style: str
            - user_friendly_score: float
            - _next_modules: ['history_preferences']
        """
        
        # Extrair dados do input
        pergunta = data.get('pergunta', '')
        username = data.get('username', 'unknown')
        projeto = data.get('projeto', 'default')
        
        print(f"[RESPONSE_COMPOSER] 🎨 Formatando resposta para o usuário...")
        print(f"[RESPONSE_COMPOSER]    Username: {username}")
        print(f"[RESPONSE_COMPOSER]    Projeto: {projeto}")
        print(f"[RESPONSE_COMPOSER]    Pergunta: {pergunta}")
        
        # Medir tempo de execução
        start_time = time.time()
        
        # Executar composição - passar data completo como state
        result = self.agent.execute(data)
        
        execution_time = time.time() - start_time
        
        print(f"[RESPONSE_COMPOSER] ✅ Resposta formatada com sucesso!")
        print(f"[RESPONSE_COMPOSER]    Tamanho da resposta: {len(result.get('response_text', ''))} caracteres")
        print(f"[RESPONSE_COMPOSER]    User-friendly score: {result.get('user_friendly_score', 0)}")
        print(f"[RESPONSE_COMPOSER]    Tempo de execução: {execution_time:.2f}s")
        
        # Preparar output - History vai buscar todos os parent_ids
        output = {
            'previous_module': 'response_composer',
            'pergunta': pergunta,
            'username': username,
            'projeto': projeto,
            # Repassar TODOS os parent_ids recebidos
            'parent_python_runtime_id': data.get('parent_python_runtime_id'),
            'parent_athena_executor_id': data.get('parent_athena_executor_id'),
            'parent_auto_correction_id': data.get('parent_auto_correction_id'),
            'parent_sql_validator_id': data.get('parent_sql_validator_id'),
            'parent_analysis_orchestrator_id': data.get('parent_analysis_orchestrator_id'),
            'parent_plan_confirm_id': data.get('parent_plan_confirm_id'),
            'parent_plan_builder_id': data.get('parent_plan_builder_id'),
            'parent_intent_validator_id': data.get('parent_intent_validator_id'),
            # Resultados da composição
            **result,
            # Tempo de execução
            'execution_time': execution_time,
            # Próximo módulo: history_preferences (salvar response_composer primeiro)
            '_next_modules': ['history_preferences']
        }
        
        print(f"[RESPONSE_COMPOSER] 🔀 Enviando resposta formatada para: history_preferences")
        print(f"[RESPONSE_COMPOSER] 📝 History vai salvar e depois chamar user_feedback")
        
        return output


if __name__ == '__main__':
    worker = ResponseComposerWorker()
    worker.start()
