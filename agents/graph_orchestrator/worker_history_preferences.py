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
            - intent_category: str
            - intent_valid: bool
            - intent_reason: str
            - is_special_case: bool
            - security_violation: bool
            - tokens_used: int
            - ... (todos os campos do módulo anterior)
            
        Output:
            - context: Dict com histórico e preferências
            - execution_time: float
        """
        
        print(f"   🔍 Debug - Data recebido no worker:")
        print(f"      username: {data.get('username')}")
        print(f"      projeto: {data.get('projeto')}")
        print(f"      intent_valid: {data.get('intent_valid')}")
        print(f"      intent_reason: {data.get('intent_reason')}")
        print(f"      is_special_case: {data.get('is_special_case')}")
        print(f"      security_violation: {data.get('security_violation')}")
        print(f"      tokens_used: {data.get('tokens_used')}")
        
        # IMPORTANTE: Usar TODO o data como state, não criar um novo!
        # Isso mantém TODOS os campos do módulo anterior
        state = dict(data)  # Copia tudo
        
        # Carregar contexto
        result_state = self.agent.load_context(state)
        
        # Salvar interação no PostgreSQL (passa o state completo)
        save_state = self.agent.save_interaction(result_state)
        
        # IMPORTANTE: Retornar TODOS os dados do módulo anterior + info do history
        # Isso permite que o próximo módulo (plan_confirm) tenha acesso a tudo
        output = dict(data)  # Mantém TODOS os campos
        output.update({
            'context_loaded': result_state.get('has_user_context', False),
            'interaction_saved': save_state.get('interaction_saved', False),
            'interaction_id': save_state.get('interaction_id'),
            'log_id': save_state.get('log_id'),
            'execution_time': 0.1,  # TODO: medir tempo real
        })
        
        return output

if __name__ == '__main__':
    worker = HistoryPreferencesWorker()
    worker.start()
