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
        print(f"✅ Intent Validator Agent carregado")
    
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
        
        # Verificar se houve erro
        if not result.get('intent_valid') and 'error' in result:
            raise Exception(f"Intent Validator falhou: {result.get('error')}")
        
        return {
            'intent_valid': result.get('intent_valid', False),
            'intent_category': result.get('intent_category', 'unknown'),
            'reason': result.get('reason', result.get('intent_reason', 'Sem razão fornecida')),
            'is_special_case': result.get('is_special_case', False),
            'security_violation': result.get('security_violation', False),
            'execution_time': result.get('execution_time', 0),
            'model_used': result.get('model_used', 'gpt-4o'),
            'tokens_used': result.get('tokens_used'),
            # Manter pergunta para próximo módulo
            'pergunta': pergunta
        }

if __name__ == '__main__':
    worker = IntentValidatorWorker()
    worker.start()
