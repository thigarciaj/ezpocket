"""
History and Preferences Agent - NÓ de Context Manager/Memory
Gerencia histórico de interações e preferências do usuário no LangGraph
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv


class HistoryPreferencesAgent:
    """
    Agente responsável por gerenciar histórico de interações e preferências do usuário.
    Fornece contexto personalizado para melhorar as respostas do sistema.
    """
    
    def __init__(self):
        """Inicializa o agente e carrega configurações"""
        print("\n" + "="*80)
        print("🧠 HISTORY AND PREFERENCES AGENT - CONTEXT MANAGER/MEMORY")
        print("="*80)
        
        # Carrega .env
        env_path = Path(__file__).parent.parent.parent / ".env"
        load_dotenv(env_path)
        
        # Configurações PostgreSQL
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5546'),
            'database': os.getenv('POSTGRES_DB', 'ezpocket_logs'),
            'user': os.getenv('POSTGRES_USER', 'ezpocket_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'ezpocket_pass_2025')
        }
        
        # Carrega config.json
        self.config = self._load_config()
        print("✅ Configurações carregadas de config.json")
        
        # Inicializa tabelas
        self._init_database()
        print(f"✅ PostgreSQL conectado: {self.db_config['host']}:{self.db_config['port']}")
        print("="*80 + "\n")
    
    def _load_config(self) -> Dict:
        """Carrega configurações do config.json"""
        config_path = Path(__file__).parent / "config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_connection(self):
        """Cria conexão com PostgreSQL"""
        return psycopg2.connect(**self.db_config)
    
    def _get_intent_validator_id_by_context(self, username, projeto, pergunta):
        """Busca o intent_validator_log_id mais recente para o mesmo contexto"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        print(f"  🔍 Buscando intent_validator_logs recente: user={username}, projeto={projeto}")
        
        cursor.execute("""
            SELECT id FROM intent_validator_logs 
            WHERE username = %s 
              AND projeto = %s 
              AND pergunta = %s
            ORDER BY horario DESC 
            LIMIT 1
        """, (username, projeto, pergunta))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            print(f"  ✅ Encontrado intent_validator_id: {result[0]}")
        else:
            print(f"  ❌ Nenhum intent_validator_logs encontrado")
        
        return result[0] if result else None
    
    def _get_plan_builder_id_by_context(self, username, projeto, pergunta):
        """Busca o plan_builder_log_id mais recente para o mesmo contexto"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        print(f"  🔍 Buscando plan_builder_logs recente: user={username}, projeto={projeto}")
        
        cursor.execute("""
            SELECT id FROM plan_builder_logs 
            WHERE username = %s 
              AND projeto = %s 
              AND pergunta = %s
            ORDER BY horario DESC 
            LIMIT 1
        """, (username, projeto, pergunta))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            print(f"  ✅ Encontrado plan_builder_id: {result[0]}")
        else:
            print(f"  ❌ Nenhum plan_builder_logs encontrado")
        
        return result[0] if result else None
    
    def _get_plan_confirm_id_by_context(self, username, projeto, pergunta):
        """Busca o plan_confirm_log_id mais recente para o mesmo contexto"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        print(f"  🔍 Buscando plan_confirm_logs recente: user={username}, projeto={projeto}")
        
        cursor.execute("""
            SELECT id FROM plan_confirm_logs 
            WHERE username = %s 
              AND projeto = %s 
              AND pergunta = %s
            ORDER BY horario DESC 
            LIMIT 1
        """, (username, projeto, pergunta))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            print(f"  ✅ Encontrado plan_confirm_id: {result[0]}")
        else:
            print(f"  ❌ Nenhum plan_confirm_logs encontrado")
        
        return result[0] if result else None
    
    def _get_user_proposed_plan_id_by_context(self, username, projeto, pergunta):
        """Busca o user_proposed_plan_log_id mais recente para o mesmo contexto"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        print(f"  🔍 Buscando user_proposed_plan_logs recente: user={username}, projeto={projeto}")
        
        cursor.execute("""
            SELECT id FROM user_proposed_plan_logs 
            WHERE username = %s 
              AND projeto = %s 
              AND pergunta = %s
            ORDER BY horario DESC 
            LIMIT 1
        """, (username, projeto, pergunta))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            print(f"  ✅ Encontrado user_proposed_plan_id: {result[0]}")
        else:
            print(f"  ⚠️  Nenhum user_proposed_plan_logs encontrado (pode não ter havido rejeição)")
        
        return result[0] if result else None
    
    def _init_database(self):
        """Inicializa tabelas do banco de dados PostgreSQL"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Tabela history_preferences_logs já existe no init-db.sql
        # Apenas garantir que existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history_preferences_logs (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                projeto VARCHAR(100) NOT NULL,
                horario TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                contexto_carregado BOOLEAN,
                num_interacoes_recentes INTEGER,
                num_preferencias INTEGER,
                num_padroes INTEGER,
                metadata JSONB
            )
        ''')
        
        # Índices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hp_user_proj ON history_preferences_logs(username, projeto)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hp_horario ON history_preferences_logs(horario)')
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def load_context(self, state: Dict) -> Dict:
        """
        Carrega contexto do usuário (histórico e preferências)
        
        Args:
            state: Estado do grafo LangGraph
            
        Returns:
            Estado atualizado com contexto do usuário
        """
        print("\n" + "="*80)
        print("🧠 HISTORY AND PREFERENCES AGENT - LOAD CONTEXT")
        print("="*80)
        
        username = state.get("username", "unknown")
        projeto = state.get("projeto", "default")
        
        print("\n📥 INPUTS:")
        print(f"  • Username: {username}")
        print(f"  • Projeto: {projeto}")
        
        print("\n⚙️  PROCESSAMENTO:")
        
        # 1. Carregar histórico recente
        print("  ✓ Carregando histórico recente...")
        recent_history = self._get_recent_history(username, projeto)
        print(f"    → {len(recent_history)} interações encontradas")
        
        # 2. Carregar preferências
        print("  ✓ Carregando preferências do usuário...")
        preferences = self._get_user_preferences(username, projeto)
        print(f"    → {len(preferences)} preferências carregadas")
        
        # 3. Identificar padrões
        print("  ✓ Identificando padrões de uso...")
        patterns = self._get_user_patterns(username, projeto)
        print(f"    → {len(patterns)} padrões identificados")
        
        # 4. Construir contexto
        print("  ✓ Construindo contexto personalizado...")
        context = {
            "recent_history": recent_history,
            "preferences": preferences,
            "patterns": patterns,
            "has_context": len(recent_history) > 0 or len(preferences) > 0
        }
        
        print("\n📤 OUTPUT:")
        print(f"  • Has Context: {context['has_context']}")
        print(f"  • History Items: {len(recent_history)}")
        print(f"  • Preferences: {len(preferences)}")
        print(f"  • Patterns: {len(patterns)}")
        print("="*80 + "\n")
        
        # Atualiza estado
        state["user_context"] = context
        state["has_user_context"] = context["has_context"]
        
        return state
    
    def save_interaction(self, state: Dict) -> Dict:
        """
        Salva interação atual no histórico
        
        Args:
            state: Estado do grafo LangGraph
            
        Returns:
            Estado atualizado
        """
        print("\n" + "="*80)
        print("🧠 HISTORY AND PREFERENCES AGENT - SAVE INTERACTION")
        print("="*80)
        
        username = state.get("username", "unknown")
        projeto = state.get("projeto", "default")
        pergunta = state.get("pergunta", "")
        
        # Identifica qual nó anterior executou
        previous_module = state.get("previous_module", "intent_validator")
        
        print("\n📥 INPUTS:")
        print(f"  • Username: {username}")
        print(f"  • Projeto: {projeto}")
        print(f"  • Pergunta: {pergunta}")
        print(f"  • Módulo anterior: {previous_module}")
        
        print("\n🔍 DEBUG - Dados do state:")
        print(f"  • intent_valid: {state.get('intent_valid')}")
        print(f"  • intent_category: {state.get('intent_category')}")
        print(f"  • intent_reason: {state.get('intent_reason')}")
        print(f"  • is_special_case: {state.get('is_special_case')}")
        print(f"  • security_violation: {state.get('security_violation')}")
        print(f"  • tokens_used: {state.get('tokens_used')}")
        
        print("\n⚙️  PROCESSAMENTO:")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Salva na tabela correspondente ao módulo
            if previous_module == "intent_validator":
                print(f"  ✓ Salvando em intent_validator_logs")
                
                # Preparar dados completos com valores não-null
                is_special = state.get('is_special_case')
                security_viol = state.get('security_violation')
                
                # Garantir que booleanos nunca sejam None
                is_special_case = is_special if is_special is not None else False
                security_violation = security_viol if security_viol is not None else False
                
                # Preparar metadata com dados reais do processamento
                metadata = {
                    'raw_response': state.get('raw_response'),
                    'confidence': state.get('confidence'),
                    'processing_steps': state.get('processing_steps'),
                    'gpt_full_response': state.get('gpt_full_response'),
                    'validation_timestamp': state.get('validation_timestamp'),
                    'all_state_keys': list(state.keys())  # Debug
                }
                
                # Remover campos None do metadata
                metadata = {k: v for k, v in metadata.items() if v is not None}
                
                # DEBUG: Mostrar EXATAMENTE o que vai ser inserido
                print(f"\n  🔍 DEBUG - Valores que serão inseridos:")
                print(f"     username: '{username}'")
                print(f"     projeto: '{projeto}'")
                print(f"     intent_valid: {state.get('intent_valid', False)}")
                print(f"     intent_reason: '{state.get('intent_reason', '')}'")
                print(f"     is_special_case: {is_special_case}")
                print(f"     security_violation: {security_violation}")
                print(f"     security_reason: {state.get('security_reason')}")
                print(f"     tokens_used: {state.get('tokens_used')}")
                print(f"     metadata keys: {list(metadata.keys())}\n")
                
                cursor.execute("""
                    INSERT INTO intent_validator_logs (
                        execution_sequence,
                        username, projeto, pergunta,
                        intent_valid, intent_category, intent_reason,
                        is_special_case, special_type,
                        security_violation, security_reason, forbidden_keywords,
                        input_length, language_detected,
                        execution_time, model_used, tokens_used,
                        success, error_message, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    1,  # Intent validator é sempre o primeiro (sequence 1)
                    username, 
                    projeto, 
                    pergunta,
                    state.get('intent_valid', False),
                    state.get('intent_category', 'unknown'),
                    state.get('intent_reason', ''),
                    is_special_case,  # Garantido não-None
                    state.get('special_type'),
                    security_violation,  # Garantido não-None
                    state.get('security_reason'),
                    state.get('forbidden_keywords', []),
                    len(pergunta),
                    state.get('language_detected', 'pt'),
                    state.get('execution_time', 0.0),
                    state.get('model_used', 'gpt-4o'),
                    state.get('tokens_used'),
                    not bool(state.get('error_message')),
                    state.get('error_message'),
                    json.dumps(metadata, ensure_ascii=False) if metadata else None
                ))
                log_id = cursor.fetchone()[0]
            
            elif previous_module == "plan_builder":
                print(f"  ✓ Salvando em plan_builder_logs")
                
                # Buscar parent_intent_validator_id do banco usando username + projeto + pergunta
                parent_intent_validator_id = self._get_intent_validator_id_by_context(
                    username, projeto, pergunta
                )
                print(f"  🔍 DEBUG - intent_validator_id encontrado: {parent_intent_validator_id}")
                
                # Preparar metadata com dados reais do processamento
                metadata = {
                    'gpt_model': state.get('model_used'),
                    'prompt_length': state.get('prompt_length'),
                    'response_length': state.get('response_length'),
                    'steps_count': len(state.get('plan_steps', [])),
                    'data_sources_count': len(state.get('data_sources', [])),
                    'complexity_level': state.get('estimated_complexity'),
                    'output_format': state.get('output_format'),
                    'all_state_keys': list(state.keys())  # Debug - igual ao intent_validator
                }
                
                # Remover campos None do metadata
                metadata = {k: v for k, v in metadata.items() if v is not None}
                
                cursor.execute("""
                    INSERT INTO plan_builder_logs (
                        execution_sequence, parent_intent_validator_id,
                        username, projeto, pergunta, intent_category,
                        plan, plan_steps, estimated_complexity,
                        data_sources, output_format,
                        execution_time, model_used, tokens_used,
                        success, error_message, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    2,  # Plan builder é sequence 2 (depois do intent)
                    parent_intent_validator_id,  # FK buscado do banco pelo parent_job_id
                    username, projeto, pergunta,
                    state.get('intent_category', 'unknown'),
                    state.get('plan', ''),
                    state.get('plan_steps', []),
                    state.get('estimated_complexity', 'média'),
                    state.get('data_sources', []),
                    state.get('output_format', 'texto'),
                    state.get('execution_time', 0.0),
                    state.get('model_used', 'gpt-4o'),
                    state.get('tokens_used'),
                    not bool(state.get('error_message')),
                    state.get('error_message'),
                    json.dumps(metadata, ensure_ascii=False) if metadata else None
                ))
                log_id = cursor.fetchone()[0]
            
            elif previous_module == "plan_confirm":
                print(f"  ✓ Salvando em plan_confirm_logs")
                
                # Buscar parent_plan_builder_id e parent_intent_validator_id do banco
                parent_plan_builder_id = self._get_plan_builder_id_by_context(
                    username, projeto, pergunta
                )
                parent_intent_validator_id = self._get_intent_validator_id_by_context(
                    username, projeto, pergunta
                )
                
                print(f"  🔍 DEBUG - plan_builder_id encontrado: {parent_plan_builder_id}")
                print(f"  🔍 DEBUG - intent_validator_id encontrado: {parent_intent_validator_id}")
                
                # Preparar metadata
                metadata = {
                    'confirmation_timestamp': state.get('confirmation_time'),
                    'timeout_occurred': state.get('timeout_occurred', False),
                    'response_time': state.get('response_time'),
                    'all_state_keys': list(state.keys())
                }
                metadata = {k: v for k, v in metadata.items() if v is not None}
                
                cursor.execute("""
                    INSERT INTO plan_confirm_logs (
                        execution_sequence, parent_plan_builder_id, parent_intent_validator_id,
                        username, projeto, pergunta,
                        plan, plan_steps, estimated_complexity,
                        confirmed, confirmation_method, confirmation_time,
                        user_feedback, plan_accepted,
                        execution_time, success, error_message, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    3,  # Plan confirm é sequence 3 (depois do plan_builder)
                    parent_plan_builder_id,
                    parent_intent_validator_id,
                    username, projeto, pergunta,
                    state.get('plan', ''),
                    state.get('plan_steps', []),
                    state.get('estimated_complexity', 'média'),
                    state.get('confirmed', False),
                    state.get('confirmation_method', 'interactive'),
                    state.get('confirmation_time'),
                    state.get('user_feedback'),
                    state.get('plan_accepted', False),
                    state.get('execution_time', 0.0),
                    not bool(state.get('error_message')),
                    state.get('error_message'),
                    json.dumps(metadata, ensure_ascii=False) if metadata else None
                ))
                log_id = cursor.fetchone()[0]
            
            elif previous_module == "user_proposed_plan":
                print(f"  ✓ Salvando em user_proposed_plan_logs")
                
                # Buscar parent_plan_confirm_id, parent_plan_builder_id e parent_intent_validator_id do banco
                parent_plan_confirm_id = self._get_plan_confirm_id_by_context(
                    username, projeto, pergunta
                )
                parent_plan_builder_id = self._get_plan_builder_id_by_context(
                    username, projeto, pergunta
                )
                parent_intent_validator_id = self._get_intent_validator_id_by_context(
                    username, projeto, pergunta
                )
                
                print(f"  🔍 DEBUG - plan_confirm_id encontrado: {parent_plan_confirm_id}")
                print(f"  🔍 DEBUG - plan_builder_id encontrado: {parent_plan_builder_id}")
                print(f"  🔍 DEBUG - intent_validator_id encontrado: {parent_intent_validator_id}")
                
                # Preparar metadata
                metadata = {
                    'received_timestamp': state.get('received_at'),
                    'timeout_occurred': state.get('timeout_occurred', False),
                    'response_time': state.get('wait_time'),
                    'user_input_raw': state.get('user_proposed_plan'),
                    'all_state_keys': list(state.keys())
                }
                metadata = {k: v for k, v in metadata.items() if v is not None}
                
                cursor.execute("""
                    INSERT INTO user_proposed_plan_logs (
                        execution_sequence, parent_plan_confirm_id, parent_plan_builder_id, parent_intent_validator_id,
                        username, projeto, pergunta,
                        rejected_plan, user_proposed_plan, plan_received,
                        received_at, input_method,
                        input_length, is_refinement, iteration_count,
                        execution_time, wait_time,
                        success, error_message, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    4,  # User proposed plan é sequence 4 (depois do plan_confirm)
                    parent_plan_confirm_id,
                    parent_plan_builder_id,
                    parent_intent_validator_id,
                    username, projeto, pergunta,
                    state.get('plan', ''),  # O plano que foi rejeitado
                    state.get('user_proposed_plan', ''),
                    state.get('plan_received', False),
                    state.get('received_at'),
                    state.get('input_method', 'interactive'),
                    len(state.get('user_proposed_plan', '')),
                    True,  # is_refinement - sempre True pois vem de rejeição
                    state.get('iteration_count', 1),
                    state.get('execution_time', 0.0),
                    state.get('wait_time', 0.0),
                    not bool(state.get('error_message')),
                    state.get('error_message'),
                    json.dumps(metadata, ensure_ascii=False) if metadata else None
                ))
                log_id = cursor.fetchone()[0]
            
            elif previous_module == "analysis_orchestrator":
                print(f"  ✓ Salvando em analysis_orchestrator_logs")
                
                # Buscar parent IDs do banco
                parent_plan_confirm_id = self._get_plan_confirm_id_by_context(
                    username, projeto, pergunta
                )
                parent_plan_builder_id = self._get_plan_builder_id_by_context(
                    username, projeto, pergunta
                )
                parent_intent_validator_id = self._get_intent_validator_id_by_context(
                    username, projeto, pergunta
                )
                
                # Buscar parent_user_proposed_plan_id se existir (caso tenha havido rejeição)
                parent_user_proposed_plan_id = self._get_user_proposed_plan_id_by_context(
                    username, projeto, pergunta
                )
                
                # Buscar parent_plan_refiner_id se existir (caso tenha havido refinamento)
                parent_plan_refiner_id = None
                try:
                    cursor.execute("""
                        SELECT id FROM plan_refiner_logs
                        WHERE username = %s AND projeto = %s
                        ORDER BY horario DESC
                        LIMIT 1
                    """, (username, projeto))
                    result = cursor.fetchone()
                    if result:
                        parent_plan_refiner_id = result[0]
                        print(f"  ✅ Encontrado plan_refiner_id: {parent_plan_refiner_id}")
                except Exception as e:
                    print(f"  ⚠️  Erro ao buscar plan_refiner_id: {e}")
                
                print(f"  🔍 DEBUG - plan_confirm_id encontrado: {parent_plan_confirm_id}")
                print(f"  🔍 DEBUG - plan_builder_id encontrado: {parent_plan_builder_id}")
                print(f"  🔍 DEBUG - intent_validator_id encontrado: {parent_intent_validator_id}")
                print(f"  🔍 DEBUG - user_proposed_plan_id encontrado: {parent_user_proposed_plan_id}")
                print(f"  🔍 DEBUG - plan_refiner_id encontrado: {parent_plan_refiner_id}")
                
                # Preparar metadata
                metadata = {
                    'generation_timestamp': datetime.now().isoformat(),
                    'query_length': len(state.get('query_sql', '')),
                    'columns_count': len(state.get('columns_used', [])),
                    'filters_count': len(state.get('filters_applied', [])),
                    'security_checks': state.get('security_violations', []),
                    'optimization_applied': bool(state.get('optimization_notes')),
                    'all_state_keys': list(state.keys())
                }
                metadata = {k: v for k, v in metadata.items() if v is not None}
                
                # Determinar query_complexity baseado nos dados
                query_sql = state.get('query_sql', '')
                query_complexity = 'baixa'
                
                # Verifica complexidade pela query
                if 'JOIN' in query_sql.upper() or 'SUBQUERY' in query_sql.upper() or query_sql.count('SELECT') > 1:
                    query_complexity = 'alta'
                elif any(agg in query_sql.upper() for agg in ['SUM(', 'COUNT(', 'AVG(', 'GROUP BY']) or len(state.get('filters_applied', [])) > 2:
                    query_complexity = 'média'
                
                # Determinar error_type se houver erro
                error_type = None
                if state.get('error'):
                    if 'security' in state.get('error', '').lower():
                        error_type = 'security'
                    elif 'syntax' in state.get('error', '').lower():
                        error_type = 'syntax'
                    elif 'timeout' in state.get('error', '').lower():
                        error_type = 'timeout'
                    else:
                        error_type = 'api_error'
                
                # Buscar intent_category e confirmed do plan_confirm
                intent_category = None
                plan_confirmed = True  # Se chegou aqui foi porque confirmou
                
                try:
                    cursor.execute("""
                        SELECT intent_category FROM intent_validator_logs 
                        WHERE username = %s AND projeto = %s AND pergunta = %s
                        ORDER BY horario DESC LIMIT 1
                    """, (username, projeto, pergunta))
                    result = cursor.fetchone()
                    if result:
                        intent_category = result[0]
                except Exception as e:
                    print(f"  ⚠️  Erro ao buscar intent_category: {e}")
                
                # Determinar has_aggregation analisando a query SQL
                query_sql = state.get('query_sql', '')
                has_aggregation = any(keyword in query_sql.upper() for keyword in ['SUM(', 'COUNT(', 'AVG(', 'MAX(', 'MIN(', 'GROUP BY'])
                
                cursor.execute("""
                    INSERT INTO analysis_orchestrator_logs (
                        execution_sequence, parent_plan_confirm_id, parent_plan_builder_id, 
                        parent_intent_validator_id, parent_user_proposed_plan_id, parent_plan_refiner_id,
                        username, projeto, pergunta,
                        plan, intent_category, plan_confirmed,
                        query_sql, query_explanation, columns_used, filters_applied,
                        security_validated, security_violations, 
                        forbidden_columns_detected, forbidden_operations_detected,
                        optimization_notes, query_complexity, has_aggregation,
                        execution_time, model_used,
                        success, error_message, error_type, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    5,  # Analysis orchestrator é sequence 5 (depois do plan_confirm)
                    parent_plan_confirm_id,
                    parent_plan_builder_id,
                    parent_intent_validator_id,
                    parent_user_proposed_plan_id,
                    parent_plan_refiner_id,
                    username, projeto, pergunta,
                    state.get('plan', ''),
                    intent_category,
                    plan_confirmed,
                    query_sql,
                    state.get('query_explanation', ''),
                    state.get('columns_used', []),
                    state.get('filters_applied', []),
                    state.get('security_validated', False),
                    state.get('security_violations', []),
                    state.get('forbidden_columns_detected', []),
                    state.get('forbidden_operations_detected', []),
                    state.get('optimization_notes', ''),
                    query_complexity,
                    has_aggregation,
                    state.get('execution_time', 0.0),
                    state.get('model_used', 'gpt-4o'),
                    not bool(state.get('error')),
                    state.get('error'),
                    error_type,
                    json.dumps(metadata, ensure_ascii=False) if metadata else None
                ))
                log_id = cursor.fetchone()[0]
            
            elif previous_module == "sql_validator":
                print(f"  ✓ Salvando em sql_validator_logs")
                
                # Buscar parent IDs do banco
                parent_analysis_orchestrator_id = None
                try:
                    cursor.execute("""
                        SELECT id FROM analysis_orchestrator_logs
                        WHERE username = %s AND projeto = %s AND pergunta = %s
                        ORDER BY horario DESC LIMIT 1
                    """, (username, projeto, pergunta))
                    result = cursor.fetchone()
                    if result:
                        parent_analysis_orchestrator_id = result[0]
                        print(f"  ✅ Encontrado analysis_orchestrator_id: {parent_analysis_orchestrator_id}")
                except Exception as e:
                    print(f"  ⚠️  Erro ao buscar analysis_orchestrator_id: {e}")
                
                parent_plan_confirm_id = self._get_plan_confirm_id_by_context(
                    username, projeto, pergunta
                )
                parent_plan_builder_id = self._get_plan_builder_id_by_context(
                    username, projeto, pergunta
                )
                parent_intent_validator_id = self._get_intent_validator_id_by_context(
                    username, projeto, pergunta
                )
                
                print(f"  🔍 DEBUG - analysis_orchestrator_id: {parent_analysis_orchestrator_id}")
                print(f"  🔍 DEBUG - plan_confirm_id: {parent_plan_confirm_id}")
                print(f"  🔍 DEBUG - plan_builder_id: {parent_plan_builder_id}")
                print(f"  🔍 DEBUG - intent_validator_id: {parent_intent_validator_id}")
                
                # Preparar metadata
                metadata = {
                    'validation_timestamp': datetime.now().isoformat(),
                    'security_checks_performed': len(state.get('security_issues', [])),
                    'warnings_count': len(state.get('warnings', [])),
                    'suggestions_count': len(state.get('optimization_suggestions', [])),
                    'all_state_keys': list(state.keys())
                }
                metadata = {k: v for k, v in metadata.items() if v is not None}
                
                cursor.execute("""
                    INSERT INTO sql_validator_logs (
                        execution_sequence, parent_analysis_orchestrator_id, parent_plan_confirm_id,
                        parent_plan_builder_id, parent_intent_validator_id,
                        username, projeto, pergunta,
                        query_sql, valid, syntax_valid, athena_compatible,
                        security_issues, warnings, optimization_suggestions,
                        estimated_scan_size_gb, estimated_cost_usd, estimated_execution_time_seconds,
                        risk_level, execution_time, model_used, tokens_used,
                        success, error_message, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    6,  # SQL Validator é sequence 6 (depois do analysis_orchestrator)
                    parent_analysis_orchestrator_id,
                    parent_plan_confirm_id,
                    parent_plan_builder_id,
                    parent_intent_validator_id,
                    username, projeto, pergunta,
                    state.get('query_validated', state.get('query_sql', '')),
                    state.get('valid', False),
                    state.get('syntax_valid', False),
                    state.get('athena_compatible', False),
                    json.dumps(state.get('security_issues', []), ensure_ascii=False),
                    json.dumps(state.get('warnings', []), ensure_ascii=False),
                    json.dumps(state.get('optimization_suggestions', []), ensure_ascii=False),
                    state.get('estimated_scan_size_gb', 0),
                    state.get('estimated_cost_usd', 0),
                    state.get('estimated_execution_time_seconds', 0),
                    state.get('risk_level', 'unknown'),
                    state.get('execution_time', 0.0),
                    state.get('model_used', 'gpt-4o'),
                    state.get('tokens_used', 0),
                    not bool(state.get('error')),
                    state.get('error'),
                    json.dumps(metadata, ensure_ascii=False) if metadata else None
                ))
                log_id = cursor.fetchone()[0]
            
            elif previous_module == "auto_correction":
                print(f"  ✓ Salvando em auto_correction_logs")
                
                # Buscar parent IDs do banco
                parent_sql_validator_id = None
                try:
                    cursor.execute("""
                        SELECT id FROM sql_validator_logs
                        WHERE username = %s AND projeto = %s AND pergunta = %s
                        ORDER BY horario DESC LIMIT 1
                    """, (username, projeto, pergunta))
                    result = cursor.fetchone()
                    if result:
                        parent_sql_validator_id = result[0]
                        print(f"  ✅ Encontrado sql_validator_id: {parent_sql_validator_id}")
                except Exception as e:
                    print(f"  ⚠️  Erro ao buscar sql_validator_id: {e}")
                
                parent_analysis_orchestrator_id = None
                try:
                    cursor.execute("""
                        SELECT id FROM analysis_orchestrator_logs
                        WHERE username = %s AND projeto = %s AND pergunta = %s
                        ORDER BY horario DESC LIMIT 1
                    """, (username, projeto, pergunta))
                    result = cursor.fetchone()
                    if result:
                        parent_analysis_orchestrator_id = result[0]
                except Exception as e:
                    print(f"  ⚠️  Erro ao buscar analysis_orchestrator_id: {e}")
                
                parent_plan_confirm_id = self._get_plan_confirm_id_by_context(
                    username, projeto, pergunta
                )
                parent_plan_builder_id = self._get_plan_builder_id_by_context(
                    username, projeto, pergunta
                )
                parent_intent_validator_id = self._get_intent_validator_id_by_context(
                    username, projeto, pergunta
                )
                
                # Preparar metadata
                metadata = {
                    'correction_timestamp': datetime.now().isoformat(),
                    'validation_issues_count': len(state.get('validation_issues', [])),
                    'all_state_keys': list(state.keys())
                }
                metadata = {k: v for k, v in metadata.items() if v is not None}
                
                cursor.execute("""
                    INSERT INTO auto_correction_logs (
                        execution_sequence, parent_sql_validator_id, parent_analysis_orchestrator_id,
                        parent_plan_confirm_id, parent_plan_builder_id, parent_intent_validator_id,
                        username, projeto, pergunta,
                        query_original, validation_issues, success,
                        query_corrected, corrections_applied, corrections_count,
                        correction_explanation, changes_summary, confidence,
                        execution_time, model_used, tokens_used,
                        error_message, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    7,  # Auto Correction é sequence 7 (depois do sql_validator)
                    parent_sql_validator_id,
                    parent_analysis_orchestrator_id,
                    parent_plan_confirm_id,
                    parent_plan_builder_id,
                    parent_intent_validator_id,
                    username, projeto, pergunta,
                    state.get('query_original', ''),
                    json.dumps(state.get('validation_issues', []), ensure_ascii=False),
                    state.get('success', False),
                    state.get('query_corrected', ''),
                    json.dumps(state.get('corrections_applied', []), ensure_ascii=False),
                    state.get('corrections_count', 0),
                    state.get('correction_explanation', ''),
                    state.get('changes_summary', ''),
                    state.get('confidence', 0.0),
                    state.get('execution_time', 0.0),
                    state.get('model_used', 'gpt-4o'),
                    state.get('tokens_used', 0),
                    state.get('error'),
                    json.dumps(metadata, ensure_ascii=False) if metadata else None
                ))
                log_id = cursor.fetchone()[0]
            
            elif previous_module == "athena_executor":
                print(f"  ✓ Salvando em athena_executor_logs")
                
                cursor.execute("""
                    INSERT INTO athena_executor_logs (
                        execution_sequence,
                        parent_sql_validator_id,
                        parent_auto_correction_id,
                        parent_analysis_orchestrator_id,
                        parent_plan_confirm_id,
                        parent_plan_builder_id,
                        parent_intent_validator_id,
                        query_executed,
                        success,
                        row_count,
                        column_count,
                        columns,
                        results_preview,
                        results_full,
                        results_message,
                        data_size_mb,
                        database,
                        region,
                        error,
                        error_type,
                        execution_time_seconds,
                        username,
                        projeto
                    ) VALUES (
                        8, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id
                """, (
                    state.get('parent_sql_validator_id'),
                    state.get('parent_auto_correction_id'),
                    state.get('parent_analysis_orchestrator_id'),
                    state.get('parent_plan_confirm_id'),
                    state.get('parent_plan_builder_id'),
                    state.get('parent_intent_validator_id'),
                    state.get('query_executed', ''),
                    state.get('success', False),
                    state.get('row_count', 0),
                    state.get('column_count', 0),
                    json.dumps(state.get('columns', []), ensure_ascii=False),
                    json.dumps(state.get('results_preview', []), ensure_ascii=False),
                    json.dumps(state.get('results_full', []), ensure_ascii=False),
                    state.get('results_message', ''),
                    state.get('data_size_mb', 0),
                    state.get('database', 'receivables_db'),
                    state.get('region', 'us-east-1'),
                    state.get('error'),
                    state.get('error_type'),
                    state.get('execution_time_seconds', 0.0),
                    username,
                    projeto
                ))
                log_id = cursor.fetchone()[0]
            
            elif previous_module == "router":
                print(f"  ✓ Salvando em router_logs")
                
                cursor.execute("""
                    INSERT INTO router_logs (
                        username, projeto, route, route_reason,
                        query_type, requires_aggregation, requires_join,
                        complexity_level, success
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    username, projeto,
                    state.get('route', 'unknown'),
                    state.get('route_reason', ''),
                    state.get('query_type', ''),
                    state.get('requires_aggregation', False),
                    state.get('requires_join', False),
                    state.get('complexity_level', 'medium'),
                    True
                ))
                log_id = cursor.fetchone()[0]
            
            elif previous_module == "generator":
                print(f"  ✓ Salvando em generator_logs")
                
                cursor.execute("""
                    INSERT INTO generator_logs (
                        username, projeto, pergunta, sql_query,
                        query_type, tables_used, success
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    username, projeto, pergunta,
                    state.get('sql_query', ''),
                    state.get('query_type', ''),
                    state.get('tables_used', []),
                    True
                ))
                log_id = cursor.fetchone()[0]
            
            elif previous_module == "responder":
                print(f"  ✓ Salvando em responder_logs")
                
                cursor.execute("""
                    INSERT INTO responder_logs (
                        username, projeto, pergunta, resposta,
                        response_type, success
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    username, projeto, pergunta,
                    state.get('resposta', ''),
                    state.get('response_type', 'text'),
                    True
                ))
                log_id = cursor.fetchone()[0]
            
            elif previous_module == "plan_refiner":
                print(f"  ✓ Salvando em plan_refiner_logs")
                
                # DEBUG: Ver todos os campos disponíveis
                print(f"  🔍 DEBUG - Campos do state:")
                print(f"     refined_plan: {len(state.get('refined_plan', ''))} chars")
                print(f"     original_plan: {len(state.get('original_plan', ''))} chars")
                print(f"     user_suggestion: {state.get('user_suggestion', 'N/A')[:50]}...")
                print(f"     intent_category: {state.get('intent_category')}")
                print(f"     parent_plan_builder_id: {state.get('parent_plan_builder_id')}")
                print(f"     parent_user_proposed_plan_id: {state.get('parent_user_proposed_plan_id')}")
                print(f"     parent_intent_validator_id: {state.get('parent_intent_validator_id')}")
                
                # Calcular métricas
                original_plan = state.get('original_plan', '')
                refined_plan = state.get('refined_plan', '')
                changes_applied = state.get('changes_applied', [])
                user_suggestions_incorporated = state.get('user_suggestions_incorporated', [])
                improvements_made = state.get('improvements_made', [])
                
                # Buscar parent_user_proposed_plan_id do último log
                parent_user_proposed_plan_id = state.get('parent_user_proposed_plan_id')
                if not parent_user_proposed_plan_id:
                    # Buscar no banco o último log de user_proposed_plan para este user/projeto
                    cursor.execute("""
                        SELECT id FROM user_proposed_plan_logs
                        WHERE username = %s AND projeto = %s
                        ORDER BY horario DESC
                        LIMIT 1
                    """, (username, projeto))
                    result = cursor.fetchone()
                    if result:
                        parent_user_proposed_plan_id = result[0]
                        print(f"  🔍 parent_user_proposed_plan_id obtido do banco: {parent_user_proposed_plan_id}")
                
                # Buscar parent_plan_builder_id se não vier no state
                parent_plan_builder_id = state.get('parent_plan_builder_id')
                if not parent_plan_builder_id:
                    cursor.execute("""
                        SELECT id FROM plan_builder_logs
                        WHERE username = %s AND projeto = %s
                        ORDER BY horario DESC
                        LIMIT 1
                    """, (username, projeto))
                    result = cursor.fetchone()
                    if result:
                        parent_plan_builder_id = result[0]
                        print(f"  🔍 parent_plan_builder_id obtido do banco: {parent_plan_builder_id}")
                
                # Buscar parent_intent_validator_id se não vier no state
                parent_intent_validator_id = state.get('parent_intent_validator_id')
                if not parent_intent_validator_id:
                    cursor.execute("""
                        SELECT id FROM intent_validator_logs
                        WHERE username = %s AND projeto = %s
                        ORDER BY horario DESC
                        LIMIT 1
                    """, (username, projeto))
                    result = cursor.fetchone()
                    if result:
                        parent_intent_validator_id = result[0]
                        print(f"  🔍 parent_intent_validator_id obtido do banco: {parent_intent_validator_id}")
                
                # Construir metadata
                metadata = {
                    'model_used': state.get('model_used', 'gpt-4o'),
                    'temperature': state.get('temperature', 0.3),
                    'execution_time': state.get('execution_time', 0.0),
                    'num_changes': len(changes_applied),
                    'num_suggestions': len(user_suggestions_incorporated),
                    'num_improvements': len(improvements_made),
                    'original_length': len(original_plan),
                    'refined_length': len(refined_plan)
                }
                
                cursor.execute("""
                    INSERT INTO plan_refiner_logs (
                        username, projeto, horario,
                        pergunta, original_plan, user_suggestion, intent_category,
                        refined_plan, refinement_summary,
                        changes_applied, user_suggestions_incorporated,
                        improvements_made, validation_notes,
                        parent_intent_validator_id, parent_plan_builder_id, parent_user_proposed_plan_id,
                        model_used, temperature,
                        original_plan_length, refined_plan_length,
                        num_changes_applied, num_suggestions_incorporated,
                        execution_time, success, error_message, metadata
                    ) VALUES (
                        %s, %s, CURRENT_TIMESTAMP,
                        %s, %s, %s, %s,
                        %s, %s,
                        %s, %s,
                        %s, %s,
                        %s, %s, %s,
                        %s, %s,
                        %s, %s,
                        %s, %s,
                        %s, %s, %s, %s
                    )
                    RETURNING id
                """, (
                    username,
                    projeto,
                    pergunta,
                    original_plan,
                    state.get('user_suggestion', ''),
                    state.get('intent_category', 'unknown'),
                    refined_plan,
                    state.get('refinement_summary', ''),
                    json.dumps(changes_applied, ensure_ascii=False),
                    json.dumps(user_suggestions_incorporated, ensure_ascii=False),
                    json.dumps(improvements_made, ensure_ascii=False),
                    json.dumps({'notes': state.get('validation_notes', '')}, ensure_ascii=False),  # JSONB - converter string para objeto
                    parent_intent_validator_id,  # Usar variável local (buscada do banco)
                    parent_plan_builder_id,  # Usar variável local (buscada do banco)
                    parent_user_proposed_plan_id,  # Usar variável local (buscada do banco)
                    state.get('model_used', 'gpt-4o'),
                    state.get('temperature', 0.3),
                    len(original_plan),
                    len(refined_plan),
                    len(changes_applied),
                    len(user_suggestions_incorporated),
                    state.get('execution_time', 0.0),
                    not bool(state.get('error')),
                    state.get('error'),
                    json.dumps(metadata, ensure_ascii=False)
                ))
                log_id = cursor.fetchone()[0]
                print(f"  ✅ plan_refiner_logs salvo com ID: {log_id}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"  ✓ Dados salvos com sucesso! (ID: {log_id})")
            
            print("\n📤 OUTPUT:")
            print(f"  • Tabela: {previous_module}_logs")
            print(f"  • ID: {log_id}")
            print("="*80 + "\n")
            
            state["interaction_saved"] = True
            state["log_id"] = str(log_id)
            
        except Exception as e:
            print(f"\n❌ ERRO ao salvar interação:")
            print(f"  • Erro: {str(e)}")
            print("="*80 + "\n")
            state["interaction_saved"] = False
        
        return state
    
    def log_module_execution(self, module_name: str, state: Dict, 
                            module_input: Dict, module_output: Dict,
                            execution_time: float = 0.0, 
                            success: bool = True, error_message: str = None) -> bool:
        """
        Registra execução de um módulo específico para análise detalhada
        
        Args:
            module_name: Nome do módulo (intent_validator, router, generator, responder)
            state: Estado atual do grafo
            module_input: Input recebido pelo módulo
            module_output: Output gerado pelo módulo
            execution_time: Tempo de execução em segundos
            success: Se execução foi bem-sucedida
            error_message: Mensagem de erro (se houver)
            
        Returns:
            True se log salvo com sucesso
        """
        try:
            username = state.get("username", "unknown")
            projeto = state.get("projeto", "default")
            
            # Pega ID da última interação (se houver)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id FROM interaction_history 
                WHERE username = ? AND projeto = ?
                ORDER BY timestamp DESC LIMIT 1
            ''', (username, projeto))
            
            row = cursor.fetchone()
            interaction_id = row[0] if row else None
            
            # Insere log do módulo
            cursor.execute('''
                INSERT INTO module_logs 
                (interaction_id, username, projeto, module_name, module_input, 
                 module_output, execution_time, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                interaction_id,
                username,
                projeto,
                module_name,
                json.dumps(module_input, ensure_ascii=False),
                json.dumps(module_output, ensure_ascii=False),
                execution_time,
                success,
                error_message
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Erro ao salvar log do módulo {module_name}: {e}")
            return False
    
    def get_module_logs(self, username: str, projeto: str, 
                       module_name: Optional[str] = None,
                       limit: int = 50) -> List[Dict]:
        """
        Obtém logs de execução dos módulos
        
        Args:
            username: Nome do usuário
            projeto: Nome do projeto
            module_name: Nome do módulo específico (opcional)
            limit: Número máximo de logs
            
        Returns:
            Lista de logs dos módulos
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if module_name:
            cursor.execute('''
                SELECT module_name, module_input, module_output, execution_time,
                       success, error_message, timestamp
                FROM module_logs
                WHERE username = ? AND projeto = ? AND module_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (username, projeto, module_name, limit))
        else:
            cursor.execute('''
                SELECT module_name, module_input, module_output, execution_time,
                       success, error_message, timestamp
                FROM module_logs
                WHERE username = ? AND projeto = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (username, projeto, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        logs = []
        for row in rows:
            logs.append({
                "module_name": row[0],
                "module_input": json.loads(row[1]) if row[1] else {},
                "module_output": json.loads(row[2]) if row[2] else {},
                "execution_time": row[3],
                "success": bool(row[4]),
                "error_message": row[5],
                "timestamp": row[6]
            })
        
        return logs
    
    def get_preferences(self, username: str, projeto: str) -> Dict:
        """
        Obtém preferências do usuário
        
        Args:
            username: Nome do usuário
            projeto: Nome do projeto
            
        Returns:
            Dicionário com preferências
        """
        return self._get_user_preferences(username, projeto)
    
    def update_preferences(self, username: str, projeto: str, 
                          category: str, preferences: Dict[str, Any],
                          confidence: float = 1.0) -> bool:
        """
        Atualiza preferências do usuário
        
        Args:
            username: Nome do usuário
            projeto: Nome do projeto
            category: Categoria da preferência
            preferences: Dicionário com preferências
            confidence: Confiança na preferência (0.0 a 1.0)
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for key, value in preferences.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO user_preferences 
                    (username, projeto, preference_category, preference_key, 
                     preference_value, confidence, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (username, projeto, category, key, json.dumps(value), confidence))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Erro ao atualizar preferências: {e}")
            return False
    
    # ===== MÉTODOS PRIVADOS =====
    
    def _get_recent_history(self, username: str, projeto: str, 
                           limit: Optional[int] = None) -> List[Dict]:
        """Obtém histórico recente do usuário - TODO: Implementar query PostgreSQL"""
        # Por enquanto retorna vazio - histórico será construído ao longo do tempo
        return []
    
    def _get_user_preferences(self, username: str, projeto: str) -> Dict:
        """Obtém preferências do usuário - TODO: Implementar query PostgreSQL"""
        # Por enquanto retorna vazio - preferências serão aprendidas ao longo do tempo
        return {}
    
    def _get_user_patterns(self, username: str, projeto: str) -> Dict:
        """Obtém padrões identificados do usuário - TODO: Implementar query PostgreSQL"""
        # Por enquanto retorna vazio - padrões serão identificados ao longo do tempo
        return {}
    
    def _map_category_to_interaction(self, category: str) -> str:
        """Mapeia categoria de intent para tipo de interação"""
        mapping = {
            "quantidade": "query",
            "conhecimentos_gerais": "faq",
            "analise_estatistica": "analysis",
            "fora_escopo": "other"
        }
        return mapping.get(category, "other")
    
    def _extract_metadata(self, state: Dict) -> Dict:
        """
        Extrai metadata relevante de TODOS os módulos do grafo
        
        Captura informações de:
        - IntentValidator (NÓ 0): intent_category, intent_reason, intent_valid
        - HistoryPreferences (NÓ 1): has_user_context, context_size
        - Router (NÓ 2): route, is_special_case, special_type, faq_match
        - Generator (NÓ 3): sql_query, source
        - Responder (NÓ 4): resposta_final, execution_time, erro
        """
        metadata = {}
        
        # === NÓ 0: INTENT VALIDATOR ===
        intent_fields = ["intent_category", "intent_reason", "intent_valid"]
        for field in intent_fields:
            if field in state:
                metadata[field] = state[field]
        
        # === NÓ 1: HISTORY/PREFERENCES ===
        if "has_user_context" in state:
            metadata["had_context"] = state["has_user_context"]
            if state.get("user_context"):
                context = state["user_context"]
                metadata["context_history_count"] = len(context.get("recent_history", []))
                metadata["context_preferences_count"] = len(context.get("preferences", {}))
                metadata["context_patterns_count"] = len(context.get("patterns", {}))
        
        # === NÓ 2: ROUTER ===
        router_fields = ["route", "is_special_case", "special_type", "tipo"]
        for field in router_fields:
            if field in state:
                metadata[field] = state[field]
        
        # FAQ match (se houver)
        if "faq_match" in state and state["faq_match"]:
            metadata["faq_match_similarity"] = state["faq_match"].get("similarity")
            metadata["faq_match_question"] = state["faq_match"].get("pergunta_similar")
        
        # === NÓ 3: GENERATOR ===
        generator_fields = ["sql_query", "source"]
        for field in generator_fields:
            if field in state:
                metadata[field] = state[field]
        
        # === NÓ 4: RESPONDER ===
        responder_fields = ["resposta_final", "execution_time", "erro"]
        for field in responder_fields:
            if field in state:
                metadata[field] = state[field]
        
        # Query executada (pode vir de diferentes fontes)
        if "query" in state:
            metadata["query_executed"] = state["query"]
        
        return metadata
    
    def _auto_learn_preferences(self, username: str, projeto: str, state: Dict):
        """Aprende preferências automaticamente baseado em padrões"""
        # Obtém histórico para análise de padrões
        history = self._get_recent_history(username, projeto, limit=20)
        
        min_interactions = self.config["learning_rules"]["min_interactions_for_pattern"]
        
        if len(history) < min_interactions:
            print(f"    → Histórico insuficiente ({len(history)}/{min_interactions})")
            return
        
        # Analisa padrões e atualiza preferências com baixa confiança
        # (para não sobrescrever preferências explícitas)
        
        # Exemplo: detectar preferência por tipo de análise
        analysis_types = [h.get("metadata", {}).get("analysis_type") 
                         for h in history if h.get("interaction_type") == "analysis"]
        
        if analysis_types:
            most_common = max(set(analysis_types), key=analysis_types.count)
            frequency = analysis_types.count(most_common) / len(analysis_types)
            
            if frequency >= self.config["learning_rules"]["confidence_threshold"]:
                self.update_preferences(
                    username, projeto, "analysis",
                    {"preferred_type": most_common},
                    confidence=frequency
                )
                print(f"    → Preferência aprendida: analysis.preferred_type = {most_common} (confiança: {frequency:.2f})")
    
    def _save_module_logs(self, interaction_id: int, state: Dict):
        """
        Salva logs detalhados de cada módulo que executou nesta interação
        
        Args:
            interaction_id: ID da interação na tabela interaction_history
            state: Estado final do grafo com dados de todos os módulos
        """
        username = state.get("username", "unknown")
        projeto = state.get("projeto", "default")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        modules_config = self.config["module_tracking"]["modules"]
        logs_saved = 0
        
        # Percorre cada módulo configurado
        for module_name, module_config in modules_config.items():
            # Extrai campos rastreados deste módulo
            module_data = {}
            has_data = False
            
            for field in module_config["tracked_fields"]:
                if field in state:
                    module_data[field] = state[field]
                    has_data = True
            
            # Se encontrou dados deste módulo, salva log
            if has_data:
                try:
                    cursor.execute('''
                        INSERT INTO module_logs 
                        (interaction_id, username, projeto, module_name, 
                         module_input, module_output, execution_time, success)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        interaction_id,
                        username,
                        projeto,
                        module_name,
                        json.dumps({"state_snapshot": "partial"}, ensure_ascii=False),
                        json.dumps(module_data, ensure_ascii=False),
                        state.get(f"{module_name}_execution_time", 0.0),
                        not state.get("erro", False)
                    ))
                    logs_saved += 1
                except Exception as e:
                    print(f"    ⚠ Erro ao salvar log do módulo {module_name}: {e}")
        
        conn.commit()
        conn.close()
        
        if logs_saved > 0:
            print(f"    → {logs_saved} logs modulares salvos")
