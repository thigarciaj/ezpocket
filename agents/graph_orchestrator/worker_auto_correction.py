#!/usr/bin/env python3
"""
Worker para Auto Correction Agent
"""

import sys
import os
from pathlib import Path

# Adicionar paths
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

from agents.graph_orchestrator.graph_orchestrator import ModuleWorker
from agents.auto_correction_agent.auto_correction import AutoCorrectionAgent
from typing import Dict, Any

class AutoCorrectionWorker(ModuleWorker):
    """Worker para o módulo auto_correction"""
    
    def __init__(self):
        super().__init__('auto_correction')
        self.agent = AutoCorrectionAgent()
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa correção de query SQL inválida
        
        Input esperado:
            - query_validated: str (query inválida do SQL Validator)
            - security_issues: list (problemas encontrados)
            - warnings: list
            - username: str
            - projeto: str
            - pergunta: str
            
        Output:
            - success: bool
            - query_original: str
            - query_corrected: str
            - corrections_applied: list
            - corrections_count: int
            - correction_explanation: str
        """
        
        query_original = data.get('query_validated', data.get('query_sql', ''))
        username = data.get('username', 'unknown')
        projeto = data.get('projeto', 'default')
        
        # Combinar issues de validação
        validation_issues = []
        validation_issues.extend(data.get('security_issues', []))
        validation_issues.extend(data.get('warnings', []))
        
        # Adicionar erro se houver
        if data.get('error'):
            validation_issues.append(data.get('error'))
        
        print(f"[AUTO_CORRECTION] 🔧 Corrigindo query SQL...")
        print(f"[AUTO_CORRECTION]    Username: {username}")
        print(f"[AUTO_CORRECTION]    Projeto: {projeto}")
        print(f"[AUTO_CORRECTION]    Issues: {len(validation_issues)}")
        
        # Corrigir query
        result = self.agent.correct(
            query_original=query_original,
            validation_issues=validation_issues,
            username=username,
            projeto=projeto
        )
        
        print(f"[AUTO_CORRECTION] ✅ Correção concluída")
        print(f"[AUTO_CORRECTION]    Success: {result['success']}")
        print(f"[AUTO_CORRECTION]    Corrections: {result['corrections_count']}")
        
        # Adicionar campos necessários para history
        output = {
            **result,
            'previous_module': 'auto_correction',
            'pergunta': data.get('pergunta', ''),
            'username': username,
            'projeto': projeto,
            'intent_category': data.get('intent_category'),
            'plan': data.get('plan'),
            # Parent IDs para rastreabilidade
            'parent_sql_validator_id': data.get('parent_id'),  # SQL Validator é o parent direto
            'parent_analysis_orchestrator_id': data.get('parent_analysis_orchestrator_id'),
            'parent_plan_confirm_id': data.get('parent_plan_confirm_id'),
            'parent_plan_builder_id': data.get('parent_plan_builder_id'),
            'parent_intent_validator_id': data.get('parent_intent_validator_id'),
            # Próximos módulos: athena_executor + history (paralelo)
            '_next_modules': ['athena_executor', 'history_preferences']
        }
        
        print(f"[AUTO_CORRECTION] 🔀 Próximos módulos: athena_executor + history")
        
        return output


if __name__ == '__main__':
    worker = AutoCorrectionWorker()
    worker.start()
