import sqlite3
import hashlib
import datetime
import os

# Usa caminho absoluto para garantir que sempre encontre o banco
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FOLDER = os.path.join(BASE_DIR, "database")
MAIN_DB = os.path.join(DB_FOLDER, "ezpocket.db")

def ensure_db_folder():
    """Garante que a pasta database existe"""
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)

def hash_password(password):
    """Cria hash da senha para segurança"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_main_database():
    """Inicializa o banco principal com tabela de usuários"""
    ensure_db_folder()
    conn = sqlite3.connect(MAIN_DB)
    cursor = conn.cursor()
    
    # Tabela de usuários
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

def create_user(username, password):
    """Cria um novo usuário (apenas para administradores)"""
    try:
        conn = sqlite3.connect(MAIN_DB)
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
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

def authenticate_user(username, password):
    """Autentica usuário e retorna informações"""
    try:
        conn = sqlite3.connect(MAIN_DB)
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
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

def init_user_chat_database(username):
    """Inicializa banco de histórico de chat para um usuário específico (username)"""
    ensure_db_folder()
    user_db = os.path.join(DB_FOLDER, f"chat_history_{username}.db")
    
    conn = sqlite3.connect(user_db)
    cursor = conn.cursor()
    
    # Tabela de histórico de conversas
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
    
## Função duplicada removida. Usar apenas init_user_chat_database(username)

def save_chat_message(username, pergunta, resposta, who, query_sql=None, session_id=None):
    """Salva uma mensagem no histórico do usuário"""
    try:
        user_db = os.path.join(DB_FOLDER, f"chat_history_{str(username)}.db")
        
        # Garante que o banco do usuário existe
        init_user_chat_database(username)
        
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

def get_chat_history(username, limit=50):
    """Recupera histórico de chat do usuário"""
    try:
        user_db = os.path.join(DB_FOLDER, f"chat_history_{str(username)}.db")
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

def list_users():
    """Lista todos os usuários (para administradores)"""
    try:
        conn = sqlite3.connect(MAIN_DB)
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

def toggle_user_status(username):
    """Ativa/desativa um usuário"""
    try:
        conn = sqlite3.connect(MAIN_DB)
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

def log_user_logout(user_id, logout_type="manual"):
    """Registra o logout do usuário no banco"""
    try:
        conn = sqlite3.connect(MAIN_DB)
        cursor = conn.cursor()
        
        # Atualiza último logout
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

# Inicializa o banco principal ao importar
init_main_database()
