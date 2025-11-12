"""
Módulo de gerenciamento de autenticação e sessões
Refatorado de database.py para melhor organização
"""
import sqlite3
import hashlib
import datetime
import os

class AuthManager:
    """Gerencia autenticação de usuários e sessões"""
    
    def __init__(self, db_folder='database'):
        self.db_folder = db_folder
        self.main_db = os.path.join(db_folder, 'ezpocket.db')
        self._ensure_db_folder()
        self._init_database()
    
    def _ensure_db_folder(self):
        """Garante que a pasta database existe"""
        if not os.path.exists(self.db_folder):
            os.makedirs(self.db_folder)
    
    def _hash_password(self, password):
        """Cria hash da senha para segurança"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _init_database(self):
        """Inicializa o banco principal com tabela de usuários"""
        conn = sqlite3.connect(self.main_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, username, password):
        """Cria um novo usuário"""
        try:
            conn = sqlite3.connect(self.main_db)
            cursor = conn.cursor()
            
            password_hash = self._hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            
            conn.commit()
            conn.close()
            return True, "Usuário criado com sucesso"
        except sqlite3.IntegrityError:
            return False, "Usuário já existe"
        except Exception as e:
            return False, f"Erro ao criar usuário: {str(e)}"
    
    def authenticate_user(self, username, password):
        """Autentica usuário e retorna informações"""
        try:
            conn = sqlite3.connect(self.main_db)
            cursor = conn.cursor()
            
            password_hash = self._hash_password(password)
            cursor.execute(
                "SELECT id, username, is_active FROM users WHERE username = ? AND password_hash = ?",
                (username, password_hash)
            )
            
            user = cursor.fetchone()
            
            if user and user[2]:  # Verifica se usuário existe e está ativo
                # Atualiza último login
                cursor.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                    (user[0],)
                )
                conn.commit()
                conn.close()
                
                return True, {"id": user[0], "username": user[1]}
            else:
                conn.close()
                return False, "Usuário ou senha inválidos"
                
        except Exception as e:
            return False, f"Erro na autenticação: {str(e)}"
    
    def list_users(self):
        """Lista todos os usuários"""
        try:
            conn = sqlite3.connect(self.main_db)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, username, created_at, last_login, is_active FROM users ORDER BY username"
            )
            
            users = cursor.fetchall()
            conn.close()
            
            return users
        except Exception as e:
            print(f"Erro ao listar usuários: {str(e)}")
            return []
    
    def toggle_user_status(self, username):
        """Ativa/desativa um usuário"""
        try:
            conn = sqlite3.connect(self.main_db)
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE users SET is_active = NOT is_active WHERE username = ?",
                (username,)
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao alterar status do usuário: {str(e)}")
            return False
    
    def log_user_logout(self, user_id, logout_type="manual"):
        """Registra o logout do usuário no banco"""
        try:
            conn = sqlite3.connect(self.main_db)
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,)
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao registrar logout: {str(e)}")
            return False
