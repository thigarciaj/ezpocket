import sqlite3
import os
import json
from datetime import datetime
from flask import session

class ProjetosManager:
    def __init__(self, db_folder='database/projetos'):
        self.db_folder = db_folder
        os.makedirs(db_folder, exist_ok=True)
        
    def get_user_id(self):
        """Pega o ID do usuário da sessão"""
        return session.get('user_id', 'anonymous')
    
    def get_main_db_path(self):
        """Retorna o caminho do banco principal de projetos do usuário"""
        user_id = self.get_user_id()
        return os.path.join(self.db_folder, f'user_{user_id}_projetos.db')
    
    def get_project_db_path(self, projeto_nome):
        """Retorna o caminho do banco específico do projeto"""
        user_id = self.get_user_id()
        # Sanitiza o nome do projeto para uso em arquivo
        nome_sanitizado = "".join(c for c in projeto_nome if c.isalnum() or c in (' ', '-', '_')).rstrip()
        nome_sanitizado = nome_sanitizado.replace(' ', '_')
        return os.path.join(self.db_folder, f'user_{user_id}_{nome_sanitizado}.db')
    
    def init_main_db(self):
        """Inicializa o banco principal de projetos"""
        with sqlite3.connect(self.get_main_db_path()) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS projetos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE,
                    descricao TEXT,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_ultimo_acesso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ultima_sessao TEXT
                )
            ''')
            # Adiciona a coluna ultima_sessao se não existir (migração)
            try:
                conn.execute('ALTER TABLE projetos ADD COLUMN ultima_sessao TEXT')
            except sqlite3.OperationalError:
                pass  # Coluna já existe
            conn.commit()
    
    def init_project_db(self, projeto_nome):
        """Inicializa o banco específico do projeto"""
        db_path = self.get_project_db_path(projeto_nome)
        with sqlite3.connect(db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS mensagens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    message TEXT NOT NULL,
                    type TEXT NOT NULL CHECK (type IN ('user', 'bot')),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS contexto (
                    id INTEGER PRIMARY KEY,
                    contexto_json TEXT,
                    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    def criar_projeto(self, nome, descricao=''):
        """Cria um novo projeto"""
        try:
            self.init_main_db()
            
            with sqlite3.connect(self.get_main_db_path()) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO projetos (nome, descricao) VALUES (?, ?)',
                    (nome, descricao)
                )
                projeto_id = cursor.lastrowid
                conn.commit()
            
            # Cria banco específico do projeto
            self.init_project_db(nome)
            
            return {
                'id': projeto_id,
                'nome': nome,
                'descricao': descricao,
                'success': True
            }
        except sqlite3.IntegrityError:
            return {'success': False, 'message': 'Projeto com este nome já existe'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def listar_projetos(self):
        """Lista todos os projetos do usuário"""
        self.init_main_db()
        
        with sqlite3.connect(self.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nome, descricao, data_criacao, data_ultimo_acesso, ultima_sessao
                FROM projetos 
                ORDER BY data_ultimo_acesso DESC
            ''')
            
            projetos = []
            for row in cursor.fetchall():
                projetos.append({
                    'id': row[0],
                    'nome': row[1],
                    'descricao': row[2],
                    'data_criacao': row[3],
                    'data_ultimo_acesso': row[4],
                    'ultima_sessao': row[5]
                })
            
            return projetos
    
    def deletar_projeto(self, projeto_id):
        """Deleta um projeto e seu banco de dados"""
        try:
            # Pega nome do projeto antes de deletar
            projeto = self.get_projeto(projeto_id)
            if not projeto:
                return {'success': False, 'message': 'Projeto não encontrado'}
            
            # Deleta do banco principal
            with sqlite3.connect(self.get_main_db_path()) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM projetos WHERE id = ?', (projeto_id,))
                conn.commit()
            
            # Deleta arquivo do banco específico
            db_path = self.get_project_db_path(projeto['nome'])
            if os.path.exists(db_path):
                os.remove(db_path)
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def get_projeto(self, projeto_id):
        """Pega detalhes de um projeto"""
        with sqlite3.connect(self.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, nome, descricao, ultima_sessao FROM projetos WHERE id = ?',
                (projeto_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'nome': row[1],
                    'descricao': row[2],
                    'ultima_sessao': row[3]
                }
            return None
    
    def get_session_id(self):
        """Pega o ID da sessão atual"""
        session_id = session.get('session_id', session.get('user_id', 'anonymous'))
        print(f"[DEBUG] Session ID atual: {session_id}")
        return session_id
    
    def verificar_mudanca_sessao(self, projeto_id):
        """Verifica se a sessão mudou desde o último acesso ao projeto"""
        projeto = self.get_projeto(projeto_id)
        if not projeto:
            return True  # Se projeto não existe, considera como mudança
        
        sessao_atual = self.get_session_id()
        ultima_sessao = projeto.get('ultima_sessao')
        
        print(f"[DEBUG] Verificando sessão - Atual: {sessao_atual}, Última: {ultima_sessao}")
        return ultima_sessao != sessao_atual
    
    def atualizar_sessao_projeto(self, projeto_id):
        """Atualiza a sessão do projeto"""
        sessao_atual = self.get_session_id()
        
        with sqlite3.connect(self.get_main_db_path()) as conn:
            conn.execute(
                'UPDATE projetos SET ultima_sessao = ?, data_ultimo_acesso = CURRENT_TIMESTAMP WHERE id = ?',
                (sessao_atual, projeto_id)
            )
            conn.commit()
        
        print(f"[DEBUG] Sessão do projeto {projeto_id} atualizada para: {sessao_atual}")
    
    def atualizar_ultimo_acesso(self, projeto_id):
        """Atualiza o último acesso do projeto"""
        with sqlite3.connect(self.get_main_db_path()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE projetos SET data_ultimo_acesso = CURRENT_TIMESTAMP WHERE id = ?',
                (projeto_id,)
            )
            conn.commit()
    
    def salvar_mensagem(self, projeto_id, sender, message, type_msg):
        """Salva uma mensagem no histórico do projeto"""
        print(f"[DEBUG] Salvando mensagem - Projeto ID: {projeto_id}, Sender: {sender}, Type: {type_msg}")
        
        projeto = self.get_projeto(projeto_id)
        if not projeto:
            print(f"[DEBUG] Projeto {projeto_id} não encontrado!")
            return False
        
        print(f"[DEBUG] Projeto encontrado: {projeto['nome']}")
        db_path = self.get_project_db_path(projeto['nome'])
        print(f"[DEBUG] Caminho do DB: {db_path}")
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO mensagens (sender, message, type) VALUES (?, ?, ?)',
                    (sender, message, type_msg)
                )
                conn.commit()
                print(f"[DEBUG] Mensagem salva com sucesso!")
            
            # Atualiza último acesso
            self.atualizar_ultimo_acesso(projeto_id)
            return True
        except Exception as e:
            print(f"[DEBUG] Erro ao salvar mensagem: {e}")
            return False
    
    def get_historico(self, projeto_id):
        """Pega o histórico de mensagens do projeto"""
        projeto = self.get_projeto(projeto_id)
        if not projeto:
            return []
        
        db_path = self.get_project_db_path(projeto['nome'])
        if not os.path.exists(db_path):
            return []
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sender, message, type, timestamp 
                FROM mensagens 
                ORDER BY timestamp ASC
            ''')
            
            historico = []
            for row in cursor.fetchall():
                historico.append({
                    'sender': row[0],
                    'message': row[1],
                    'type': row[2],
                    'timestamp': row[3]
                })
            
            return historico
    
    def salvar_contexto(self, projeto_id, contexto):
        """Salva contexto da IA para o projeto"""
        projeto = self.get_projeto(projeto_id)
        if not projeto:
            return False
        
        db_path = self.get_project_db_path(projeto['nome'])
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO contexto (id, contexto_json) 
                VALUES (1, ?)
            ''', (json.dumps(contexto),))
            conn.commit()
        
        return True
    
    def get_contexto(self, projeto_id):
        """Pega contexto salvo do projeto"""
        projeto = self.get_projeto(projeto_id)
        if not projeto:
            return None
        
        db_path = self.get_project_db_path(projeto['nome'])
        if not os.path.exists(db_path):
            return None
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT contexto_json FROM contexto WHERE id = 1')
            row = cursor.fetchone()
            
            if row:
                return json.loads(row[0])
            return None