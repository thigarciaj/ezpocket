"""
Worker: History Preferences
Processa fila do history_preferences
"""

import sys
import os
from pathlib import Path

# Adicionar paths
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

from agents.graph_orchestrator.graph_orchestrator import ModuleWorker
from agents.history_preferences_agent.history_preferences import HistoryPreferencesAgent
from typing import Dict, Any

class HistoryPreferencesWorker(ModuleWorker):
    """Worker que processa jobs do History Preferences"""
    
    def __init__(self):
        super().__init__('history_preferences')
        self.agent = HistoryPreferencesAgent()
        print(f"✅ History Preferences Agent carregado")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa carregamento de contexto e salvamento no PostgreSQL
        
        Input esperado (output do intent_validator):
            - username: str
            - projeto: str
            - pergunta: str
            - intent_category: str (opcional)
            - intent_valid: bool (opcional)
            
        Output:
            - context: Dict com histórico e preferências
            - execution_time: float
        """
        
        username = data.get('username', 'unknown')
        projeto = data.get('projeto', 'default')
        pergunta = data.get('pergunta', '')
        intent_category = data.get('intent_category', 'unknown')
        
        # Criar state para o agente
        state = {
            'username': username,
            'projeto': projeto,
            'pergunta': pergunta,
            'intent_category': intent_category
        }
        
        # Carregar contexto
        result_state = self.agent.load_context(state)
        
        # Salvar interação no PostgreSQL
        save_state = self.agent.save_interaction(result_state)
        
        return {
            'context_loaded': result_state.get('has_user_context', False),
            'interaction_saved': save_state.get('interaction_saved', False),
            'interaction_id': save_state.get('interaction_id'),
            'execution_time': 0.1,  # TODO: medir tempo real
            # Manter dados para próximo módulo
            'pergunta': pergunta,
            'intent_category': intent_category
        }

if __name__ == '__main__':
    worker = HistoryPreferencesWorker()
    worker.start()
