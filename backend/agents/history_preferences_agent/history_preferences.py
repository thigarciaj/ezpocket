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
        env_path = Path(__file__).parent.parent.parent.parent / ".env"
        load_dotenv(env_path)
        
        # Configurações PostgreSQL
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5546'),
            'database': os.getenv('POSTGRES_DB', 'ezpocket_logs'),
            'user': os.getenv('POSTGRES_USER', 'ezpocket_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'ezpocket_pass_2025')
        }
        
        # Carrega roles.json
        self.config = self._load_config()
        print("✅ Configurações carregadas de roles.json")
        
        # Inicializa tabelas
        self._init_database()
        print(f"✅ PostgreSQL conectado: {self.db_config['host']}:{self.db_config['port']}")
        print("="*80 + "\n")
    
    def _load_config(self) -> Dict:
        """Carrega configurações do roles.json"""
        config_path = Path(__file__).parent / "roles.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_connection(self):
        """Cria conexão com PostgreSQL"""
        return psycopg2.connect(**self.db_config)
    
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
        intent_category = state.get("intent_category", "unknown")
        
        print("\n📥 INPUTS:")
        print(f"  • Username: {username}")
        print(f"  • Projeto: {projeto}")
        print(f"  • Pergunta: {pergunta}")
        print(f"  • Categoria: {intent_category}")
        
        print("\n⚙️  PROCESSAMENTO:")
        
        try:
            # Determina tipo de interação baseado na categoria
            interaction_type = self._map_category_to_interaction(intent_category)
            print(f"  ✓ Tipo de interação: {interaction_type}")
            
            # Extrai metadata relevante
            metadata = self._extract_metadata(state)
            print(f"  ✓ Metadata extraída: {len(metadata)} campos")
            
            # Salva no PostgreSQL
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Adiciona pergunta no metadata
            metadata['pergunta'] = pergunta
            metadata['intent_category'] = intent_category
            metadata['interaction_type'] = interaction_type
            
            cursor.execute('''
                INSERT INTO history_preferences_logs 
                (username, projeto, contexto_carregado, num_interacoes_recentes, 
                 num_preferencias, num_padroes, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (username, projeto, True, 1, 0, 0, 
                  json.dumps(metadata, ensure_ascii=False)))
            
            # Pega ID da interação recém-criada
            interaction_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("  ✓ Interação salva com sucesso no PostgreSQL!")
            
            print("\n📤 OUTPUT:")
            print("  • Status: Interação registrada")
            print("="*80 + "\n")
            
            state["interaction_saved"] = True
            
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
