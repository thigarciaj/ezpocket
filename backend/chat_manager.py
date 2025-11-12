"""
Módulo de gerenciamento de histórico de chat
Refatorado de database.py para melhor organização
"""
import sqlite3
import os

class ChatManager:
    """Gerencia histórico de conversas dos usuários"""
    
    def __init__(self, db_folder='database'):
        self.db_folder = db_folder
        self._ensure_db_folder()
    
    def _ensure_db_folder(self):
        """Garante que a pasta database existe"""
        if not os.path.exists(self.db_folder):
            os.makedirs(self.db_folder)
    
    def _get_user_db_path(self, username):
        """Retorna o caminho do banco de chat do usuário"""
        return os.path.join(self.db_folder, f"chat_history_{username}.db")
    
    def _init_user_chat_database(self, username):
        """Inicializa banco de histórico de chat para um usuário específico"""
        user_db = self._get_user_db_path(username)
        
        conn = sqlite3.connect(user_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pergunta TEXT NOT NULL,
                resposta TEXT NOT NULL,
                datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                who TEXT NOT NULL,
                query_sql TEXT,
                session_id TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_chat_message(self, username, pergunta, resposta, who, query_sql=None, session_id=None):
        """Salva uma mensagem no histórico do usuário"""
        try:
            # Garante que o banco do usuário existe
            self._init_user_chat_database(username)
            
            user_db = self._get_user_db_path(username)
            conn = sqlite3.connect(user_db)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO chat_history (pergunta, resposta, who, query_sql, session_id) VALUES (?, ?, ?, ?, ?)",
                (pergunta, resposta, who, query_sql, session_id)
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao salvar mensagem: {str(e)}")
            return False
    
    def get_chat_history(self, username, limit=50):
        """Recupera histórico de chat do usuário"""
        try:
            user_db = self._get_user_db_path(username)
            if not os.path.exists(user_db):
                return []
            
            conn = sqlite3.connect(user_db)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT pergunta, resposta, datetime, who, query_sql FROM chat_history ORDER BY datetime DESC LIMIT ?",
                (limit,)
            )
            messages = cursor.fetchall()
            conn.close()
            return messages
        except Exception as e:
            print(f"Erro ao recuperar histórico: {str(e)}")
            return []
    
    def clear_history(self, username):
        """Limpa o histórico de chat de um usuário"""
        try:
            user_db = self._get_user_db_path(username)
            if os.path.exists(user_db):
                os.remove(user_db)
                return True
            return False
        except Exception as e:
            print(f"Erro ao limpar histórico: {str(e)}")
            return False
