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
        
        print(f"[ATHENA_EXECUTOR] ⚡ Executando query no Athena...")
        print(f"[ATHENA_EXECUTOR]    Username: {username}")
        print(f"[ATHENA_EXECUTOR]    Projeto: {projeto}")
        print(f"[ATHENA_EXECUTOR]    Origem: {'AutoCorrection' if came_from_correction else 'SQLValidator'}")
        
        # Executar query
        result = self.agent.execute(
            query_sql=query_sql,
            username=username,
            projeto=projeto
        )
        
        # Debug: verificar tipo do result
        print(f"[ATHENA_EXECUTOR] 🔍 DEBUG: type(result) = {type(result)}")
        print(f"[ATHENA_EXECUTOR] 🔍 DEBUG: result = {result}")
        
        # GARANTIR que result seja sempre um dict
        if not isinstance(result, dict):
            print(f"[ATHENA_EXECUTOR] ⚠️  ERRO: result não é dict (tipo: {type(result)})")
            if isinstance(result, tuple):
                print(f"[ATHENA_EXECUTOR] 🔧 Convertendo tupla para dict...")
                # Se for tupla, pegar o primeiro elemento se for dict
                if len(result) > 0 and isinstance(result[0], dict):
                    result = result[0]
                else:
                    # Criar dict vazio como fallback
                    result = {
                        'success': False,
                        'error': f'Formato inválido retornado pelo agent: {type(result)}'
                    }
            else:
                # Tipo inesperado
                result = {
                    'success': False,
                    'error': f'Tipo inesperado retornado pelo agent: {type(result)}'
                }
        
        print(f"[ATHENA_EXECUTOR] ✅ Execução concluída")
        print(f"[ATHENA_EXECUTOR]    Success: {result.get('success', False)}")
        print(f"[ATHENA_EXECUTOR]    Rows: {result.get('row_count', 0)}")
        
        # Preparar parent IDs - buscar TODOS do banco pois vem em paralelo com history
        print(f"[ATHENA_EXECUTOR] 🔍 Buscando parent IDs no banco...")
        
        from agents.history_preferences_agent.history_preferences import HistoryPreferencesAgent
        history_agent = HistoryPreferencesAgent()
        conn = history_agent._get_connection()
        cursor = conn.cursor()
        pergunta = data.get('pergunta', '')
        
        parent_auto_correction_id = None
        parent_sql_validator_id = None
        parent_analysis_orchestrator_id = None
        parent_plan_confirm_id = None
        parent_plan_builder_id = None
        parent_intent_validator_id = None
        
        try:
            # Buscar auto_correction_id (SEMPRE existe no fluxo antes do athena_executor)
            cursor.execute("""
                SELECT id FROM auto_correction_logs
                WHERE username = %s AND projeto = %s AND pergunta = %s
                ORDER BY horario DESC LIMIT 1
            """, (username, projeto, pergunta))
            row = cursor.fetchone()
            if row:
                parent_auto_correction_id = row[0]
                print(f"[ATHENA_EXECUTOR]    ✓ parent_auto_correction_id: {parent_auto_correction_id}")
            
            # Buscar sql_validator_id (SEMPRE existe no fluxo antes do athena_executor)
            cursor.execute("""
                SELECT id FROM sql_validator_logs
                WHERE username = %s AND projeto = %s AND pergunta = %s
                ORDER BY horario DESC LIMIT 1
            """, (username, projeto, pergunta))
            row = cursor.fetchone()
            if row:
                parent_sql_validator_id = row[0]
                print(f"[ATHENA_EXECUTOR]    ✓ parent_sql_validator_id: {parent_sql_validator_id}")
            
            # Buscar analysis_orchestrator_id
            cursor.execute("""
            SELECT id FROM analysis_orchestrator_logs
            WHERE username = %s AND projeto = %s AND pergunta = %s
                ORDER BY horario DESC LIMIT 1
            """, (username, projeto, pergunta))
            row = cursor.fetchone()
            if row:
                parent_analysis_orchestrator_id = row[0]
                print(f"[ATHENA_EXECUTOR]    ✓ parent_analysis_orchestrator_id: {parent_analysis_orchestrator_id}")
            
            # Buscar plan_confirm_id
            cursor.execute("""
                SELECT id FROM plan_confirm_logs
                WHERE username = %s AND projeto = %s AND pergunta = %s
                ORDER BY horario DESC LIMIT 1
            """, (username, projeto, pergunta))
            row = cursor.fetchone()
            if row:
                parent_plan_confirm_id = row[0]
                print(f"[ATHENA_EXECUTOR]    ✓ parent_plan_confirm_id: {parent_plan_confirm_id}")
            
            # Buscar plan_builder_id
            cursor.execute("""
                SELECT id FROM plan_builder_logs
                WHERE username = %s AND projeto = %s AND pergunta = %s
                ORDER BY horario DESC LIMIT 1
            """, (username, projeto, pergunta))
            row = cursor.fetchone()
            if row:
                parent_plan_builder_id = row[0]
                print(f"[ATHENA_EXECUTOR]    ✓ parent_plan_builder_id: {parent_plan_builder_id}")
            
            # Buscar intent_validator_id
            cursor.execute("""
                SELECT id FROM intent_validator_logs
                WHERE username = %s AND projeto = %s AND pergunta = %s
                ORDER BY horario DESC LIMIT 1
            """, (username, projeto, pergunta))
            row = cursor.fetchone()
            if row:
                parent_intent_validator_id = row[0]
                print(f"[ATHENA_EXECUTOR]    ✓ parent_intent_validator_id: {parent_intent_validator_id}")
                
        except Exception as e:
            print(f"[ATHENA_EXECUTOR]    ⚠️  Erro ao buscar parent IDs: {e}")
        finally:
            cursor.close()
            conn.close()
        
        print(f"[ATHENA_EXECUTOR] 🔗 Parent IDs:")
        print(f"                    parent_auto_correction_id: {parent_auto_correction_id}")
        print(f"                    parent_sql_validator_id: {parent_sql_validator_id}")
        print(f"                    parent_analysis_orchestrator_id: {parent_analysis_orchestrator_id}")
        print(f"                    parent_plan_confirm_id: {parent_plan_confirm_id}")
        print(f"                    parent_plan_builder_id: {parent_plan_builder_id}")
        print(f"                    parent_intent_validator_id: {parent_intent_validator_id}")
        
        # VERIFICAÇÃO FINAL antes de criar output
        print(f"[ATHENA_EXECUTOR] 🔍 VERIFICAÇÃO FINAL PRÉ-OUTPUT:")
        print(f"[ATHENA_EXECUTOR]    type(result) = {type(result)}")
        print(f"[ATHENA_EXECUTOR]    isinstance(result, dict) = {isinstance(result, dict)}")
        print(f"[ATHENA_EXECUTOR]    result content: {result}")
        
        # Se result não for dict, criar dict vazio
        if not isinstance(result, dict):
            print(f"[ATHENA_EXECUTOR] ❌ ERRO: result não é dict! Criando dict vazio...")
            result = {
                'success': False,
                'error': f'Agent retornou tipo inválido: {type(result)}'
            }
        
        print(f"[ATHENA_EXECUTOR] 📍 LINHA 214: Iniciando criação do dict output...")
        
        # Adicionar campos necessários para history (parent_ids definidos ANTES do spread)
        try:
            output = {
            'previous_module': 'athena_executor',
            'pergunta': data.get('pergunta', ''),
            'username': username,
            'projeto': projeto,
            'intent_category': data.get('intent_category'),
            'plan': data.get('plan'),
            # Parent IDs para rastreabilidade (CRÍTICO: definir antes do spread)
            'parent_auto_correction_id': parent_auto_correction_id,
            'parent_sql_validator_id': parent_sql_validator_id,
            'parent_analysis_orchestrator_id': parent_analysis_orchestrator_id,
            'parent_plan_confirm_id': parent_plan_confirm_id,
            'parent_plan_builder_id': parent_plan_builder_id,
            'parent_intent_validator_id': parent_intent_validator_id,
                # Resultados do Athena (adiciona DEPOIS dos parent_ids para não sobrescrever)
                **result,
                # Próximos módulos: python_runtime (análise) e history_preferences (salvar athena_executor)
                '_next_modules': ['python_runtime', 'history_preferences']
            }
            print(f"[ATHENA_EXECUTOR] ✅ Dict output criado com sucesso!")
            
        except TypeError as e:
            print(f"[ATHENA_EXECUTOR] ❌ ERRO ao criar dict output: {e}")
            print(f"[ATHENA_EXECUTOR]    type(result) = {type(result)}")
            print(f"[ATHENA_EXECUTOR]    result = {result}")
            raise
        
        print(f"[ATHENA_EXECUTOR] 🔀 Próximos módulos: python_runtime, history_preferences")
        
        return output


if __name__ == '__main__':
    worker = AthenaExecutorWorker()
    worker.start()
