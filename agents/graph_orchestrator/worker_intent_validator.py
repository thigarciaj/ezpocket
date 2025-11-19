"""
Worker: Intent Validator
Processa fila do intent_validator
"""

import sys
import os
from pathlib import Path

# Adicionar paths
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

from agents.graph_orchestrator.graph_orchestrator import ModuleWorker
from agents.intent_validator_agent.intent_validator import IntentValidatorAgent
from typing import Dict, Any

class IntentValidatorWorker(ModuleWorker):
    """Worker que processa jobs do Intent Validator"""
    
    def __init__(self):
        super().__init__('intent_validator')
        self.agent = IntentValidatorAgent()
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa validação de intenção
        
        Input esperado:
            - pergunta: str
            - username: str (opcional)
            - projeto: str (opcional)
            
        Output:
            - intent_valid: bool
            - intent_category: str
            - reason: str
            - execution_time: float
            - model_used: str
        """
        
        pergunta = data.get('pergunta')
        username = data.get('username', 'unknown')
        projeto = data.get('projeto', 'default')
        
        # Validar input
        if not pergunta:
            raise ValueError("Campo 'pergunta' é obrigatório")
        
        # Criar state para o agente (ele espera um dict)
        state = {
            'pergunta': pergunta,
            'username': username,
            'projeto': projeto
        }
        
        # Processar com o agente
        result = self.agent.validate(state)
        
        # Debug: ver o que o agente retornou
        print(f"   🔍 Debug - Result do agente:")
        print(f"      intent_valid: {result.get('intent_valid')}")
        print(f"      intent_category: {result.get('intent_category')}")
        print(f"      intent_reason: {result.get('intent_reason')}")
        print(f"      is_special_case: {result.get('is_special_case')}")
        print(f"      security_violation: {result.get('security_violation')}")
        print(f"      tokens_used: {result.get('tokens_used')}")
        
        # Verificar se houve erro
        if not result.get('intent_valid') and 'error' in result:
            raise Exception(f"Intent Validator falhou: {result.get('error')}")
        
        # Retornar TODOS os campos do result, mas PRESERVAR username/projeto originais
        output = {
            'pergunta': pergunta,
            'username': username,  # MANTER ORIGINAL
            'projeto': projeto,    # MANTER ORIGINAL
            'previous_module': 'intent_validator',
        }
        # Adicionar campos do result (exceto username/projeto para não sobrescrever)
        for key, value in result.items():
            if key not in ['username', 'projeto', 'pergunta']:
                output[key] = value
        
        return output

if __name__ == '__main__':
    worker = IntentValidatorWorker()
    worker.start()
