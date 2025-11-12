import sys
import os
from dotenv import load_dotenv

# Carrega variáveis do .env da pasta config
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, make_response
from flask_cors import CORS
from ezinho_assistant import EzinhoAssistant
from database import authenticate_user, save_chat_message, get_chat_history, log_user_logout
from projetos import ProjetosManager
import uuid
from datetime import datetime, timedelta
import time

# Timestamp da inicialização do servidor para invalidar sessões antigas
SERVER_START_TIME = time.time()

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = str(uuid.uuid4()) + '_' + str(datetime.now().timestamp())

# Inicializa o assistente Ezinho
ezinho_assistant = EzinhoAssistant()

# Pega o timeout do .env (se não achar deixa 10min)
SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT_SECONDS', 600))

# Configurações extremamente restritivas para sessões
app.config['SESSION_COOKIE_SECURE'] = False  # Para desenvolvimento (HTTP)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_NAME'] = 'ezpocket_session'
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=SESSION_TIMEOUT)
app.config['SESSION_COOKIE_MAX_AGE'] = None  # Sessão apenas (não persistente)

# Força sessões não-permanentes
app.permanent_session_lifetime = timedelta(seconds=SESSION_TIMEOUT)

CORS(app)

# Inicializa o gerenciador de projetos
projetos_manager = ProjetosManager()

@app.before_request
def before_request():
    """Executa antes de cada requisição"""
    print(f"[DEBUG] Before request - URL: {request.url}")
    print(f"[DEBUG] Before request - Session: {dict(session)}")

    # Força uso de um único endereço para evitar problemas de cookies
    if request.host == 'localhost:8000' and request.endpoint not in ['static']:
        return redirect(request.url.replace('localhost', '127.0.0.1'))

    # Invalida sessões criadas antes da inicialização do servidor
    if 'server_start_time' in session:
        try:
            session_server_time = float(session['server_start_time'])
            if session_server_time != SERVER_START_TIME:
                print(f"[DEBUG] Sessão de servidor anterior detectada - invalidando")
                session.clear()
        except:
            print(f"[DEBUG] Erro ao verificar timestamp do servidor - limpando sessão")
            session.clear()

    # Para debug: força logout em qualquer rota que não seja login
    if request.endpoint not in ['login', 'force_logout'] and request.method == 'GET':
        if 'debug_force_logout' in request.args:
            session.clear()
            print("[DEBUG] Force logout via parameter")

def login_required(f):
    """Decorator para rotas que requerem login"""
    def decorated_function(*args, **kwargs):
        print(f"[DEBUG] Verificando sessão para rota {f.__name__}")
        print(f"[DEBUG] Session keys: {list(session.keys())}")
        print(f"[DEBUG] user_id in session: {'user_id' in session}")
        print(f"[DEBUG] session_id in session: {'session_id' in session}")

        # Verificação mais rigorosa
        if not session or 'user_id' not in session or 'session_id' not in session:
            print(f"[DEBUG] Sessão inválida - redirecionando para login")
            # Limpa qualquer sessão parcial
            session.clear()

            if request.method == 'POST':
                return jsonify({'success': False, 'redirect': True}), 401

            return redirect(url_for('login'))
        
        # Verifica se a sessão tem o timestamp do servidor atual
        if 'server_start_time' not in session or session['server_start_time'] != SERVER_START_TIME:
            print(f"[DEBUG] Sessão de servidor anterior - redirecionando para login")
            session.clear()
            return redirect(url_for('login'))
        
        print(f"[DEBUG] Sessão válida - user_id: {session.get('user_id')}")
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    print(f"[DEBUG] Login route - method: {request.method}")
    print(f"[DEBUG] Current session: {dict(session)}")
    
    if request.method == 'POST':
        print("[DEBUG] Processing POST login")
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        print(f"[DEBUG] Login attempt for user: {username}")
        
        if not username or not password:
            print("[DEBUG] Login failed: missing credentials")
            return jsonify({'success': False, 'message': 'Usuário e senha são obrigatórios'})
        
        success, result = authenticate_user(username, password)
        
        if success:
            print("[DEBUG] Authentication successful")
            # Limpa qualquer sessão anterior completamente
            session.clear()
            
            # FORÇA sessão não-permanente com configuração explícita
            session.permanent = True
            session['user_id'] = result['id']
            session['username'] = result['username']
            session['session_id'] = str(uuid.uuid4())
            session['login_time'] = datetime.now().isoformat()
            session['server_start_time'] = SERVER_START_TIME  # Timestamp do servidor
            #session['_permanent'] = True  # Força explicitamente
            
            print(f"[DEBUG] Login successful - session permanent: {session.permanent}")
            print(f"[DEBUG] Login successful - _permanent: {session.get('_permanent', 'not set')}")
            print(f"[DEBUG] Login successful - server_start_time: {session.get('server_start_time')}")
            print(f"[DEBUG] Login successful - session: {dict(session)}")
            return jsonify({'success': True, 'message': 'Login realizado com sucesso'})
        else:
            print(f"[DEBUG] Login failed: {result}")
            return jsonify({'success': False, 'message': result})
    
    # Se já está logado, redireciona para o chat
    if 'user_id' in session:
        print("[DEBUG] User already logged in, redirecting to index")
        return redirect(url_for('index'))
    
    # Verifica qual tema usar baseado no .env
    frontend_theme = os.getenv('FRONTEND_THEME', 'classic')
    print(f"[DEBUG] Using frontend theme: {frontend_theme}")
    
    if frontend_theme == 'modern':
        template_name = 'index_modern.html'
    else:
        template_name = 'login.html'
    
    print(f"[DEBUG] Showing login form with template: {template_name}")
    return render_template(template_name)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    """
    Encerra a sessão do usuário
    Suporta tanto GET (redirecionamento normal) quanto POST (via JavaScript/sendBeacon)
    """
    print(f"[DEBUG] ===== LOGOUT ROUTE CALLED =====")
    print(f"[DEBUG] Logout route - method: {request.method}")
    print(f"[DEBUG] Logout route - headers: {dict(request.headers)}")
    print(f"[DEBUG] Current session before logout: {dict(session)}")
    
    # Registra o logout se houver usuário logado
    if 'user_id' in session:
        print(f"[DEBUG] Logging logout for user_id: {session['user_id']}")
        try:
            log_user_logout(session['user_id'], 
                           "automatic" if request.method == 'POST' else "manual")
            print(f"[DEBUG] Logout logged successfully")
        except Exception as e:
            print(f"[DEBUG] Error logging logout: {e}")
    else:
        print(f"[DEBUG] No user_id in session, skipping logout log")
    
    # Limpa a sessão
    session.clear()
    print(f"[DEBUG] Session cleared: {dict(session)}")
    
    if request.method == 'POST':
        # Para requisições POST (via JavaScript), retorna apenas status
        print(f"[DEBUG] Returning 204 No Content for POST request")
        return '', 204  # No Content
    else:
        # Para requisições GET, redireciona para login
        print(f"[DEBUG] Redirecting to login for GET request")
        return redirect(url_for('login'))

@app.route('/force-logout')
def force_logout():
    """Força logout completo para debug"""
    print("[DEBUG] Force logout called")
    session.clear()
    return redirect(url_for('login'))

@app.route('/clear-all')
def clear_all():
    """Limpa tudo e redireciona para login"""
    print("[DEBUG] Clear all called - clearing session completely")
    session.clear()
    response = redirect(url_for('login'))
    # Remove todos os cookies possíveis
    response.set_cookie('ezpocket_session', '', expires=0, path='/')
    response.set_cookie('session', '', expires=0, path='/')
    # Headers adicionais para prevenir cache
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/simulate-browser-close')
def simulate_browser_close():
    """Simula fechar e reabrir o navegador - remove todas as sessões"""
    print("[DEBUG] Simulando fechamento do navegador")
    response = make_response(redirect(url_for('login')))
    
    # Remove todos os cookies de sessão
    response.set_cookie('ezpocket_session', '', expires=0, path='/')
    response.set_cookie('session', '', expires=0, path='/')
    
    # Headers para prevenir cache
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    session.clear()
    return response

@app.route('/test-session-expiry')
def test_session_expiry():
    """Testa expiração de sessão"""
    if 'user_id' in session:
        login_time = datetime.fromisoformat(session['login_time'])
        elapsed = datetime.now() - login_time
        return jsonify({
            'logged_in': True,
            'login_time': session['login_time'],
            'elapsed_seconds': elapsed.total_seconds(),
            'expires_in': 10 - elapsed.total_seconds(),
            'session_data': dict(session)
        })
    else:
        return jsonify({'logged_in': False})

@app.route('/force-new-session')
def force_new_session():
    """Força criação de nova sessão"""
    print("[DEBUG] Force new session - regenerating secret key")
    # Regenera a secret key para invalidar todas as sessões
    app.secret_key = str(uuid.uuid4()) + '_' + str(datetime.now().timestamp())
    session.clear()
    response = make_response(redirect(url_for('login')))
    response.set_cookie('ezpocket_session', '', expires=0, path='/')
    return response

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    resposta = None
    pergunta = None
    if request.method == 'POST':
        pergunta = request.form.get('pergunta', '')
        if pergunta:
            resultado = ezinho_assistant.responder(pergunta)
            resposta = resultado.get('resposta')
            
            # Salva no histórico do usuário
            save_chat_message(
                session['username'],
                pergunta,
                resposta,
                'ezpocket',
                resultado.get('query'),
                session.get('session_id')
            )
    # Busca histórico recente do usuário
    chat_history = get_chat_history(session['username'], limit=10)
    
    # Verifica qual tema usar baseado no .env
    frontend_theme = os.getenv('FRONTEND_THEME', 'classic')
    
    if frontend_theme == 'modern':
        template_name = 'dashboard_full.html'
    else:
        template_name = 'index.html'
    
    return render_template(template_name,
                         resposta=resposta,
                         pergunta=pergunta,
                         chat_history=chat_history,
                         username=session.get('username'))

@app.route('/ask', methods=['POST'])
@login_required
def ask():
    data = request.get_json()
    pergunta = data.get('pergunta', '')
    
    if not pergunta:
        return jsonify({'resposta': 'Pergunta não pode estar vazia', 'query': None})
    
    resultado = ezinho_assistant.responder(pergunta)
    resposta = resultado.get('resposta')
    query = resultado.get('query')
    
    # Salva pergunta do usuário
    save_chat_message(
        session['username'],
        pergunta,
        '',
        'usuario',
        None,
        session.get('session_id')
    )
    
    # Salva resposta do ezpocket
    save_chat_message(
        session['username'],
        '',
        resposta,
        'ezpocket',
        query,
        session.get('session_id')
    )
    
    return jsonify({'resposta': resposta, 'query': query})

@app.route('/history')
@login_required
def history():
    """Endpoint para buscar histórico de conversas"""
    limit = request.args.get('limit', 50, type=int)
    chat_history = get_chat_history(session['username'], limit=limit)
    
    # Formata o histórico para JSON
    formatted_history = []
    for msg in chat_history:
        pergunta, resposta, datetime_str, who, query_sql = msg
        formatted_history.append({
            'pergunta': pergunta,
            'resposta': resposta,
            'datetime': datetime_str,
            'who': who,
            'query_sql': query_sql
        })
    
    return jsonify({'history': formatted_history})


# ===== ROTA ESPECÍFICA PARA PROJETOS =====

@app.route('/ask-projeto', methods=['POST'])
@login_required
def ask_projeto():
    """Endpoint específico para perguntas dentro de um projeto (com contexto)"""
    data = request.get_json()
    pergunta = data.get('pergunta', '')
    projeto_id = data.get('projeto_id')
    
    print(f"\n🚀 [ASK-PROJETO] Rota chamada!")
    print(f"🆔 [ASK-PROJETO] Projeto ID: {projeto_id}")
    print(f"💭 [ASK-PROJETO] Pergunta: '{pergunta[:50]}{'...' if len(pergunta) > 50 else ''}'")
    
    if not pergunta:
        return jsonify({'resposta': 'Pergunta não pode estar vazia', 'query': None})
    
    if not projeto_id:
        return jsonify({'resposta': 'ID do projeto é obrigatório', 'query': None})
    
    # Prepara contexto do projeto
    contexto_adicional = ""
    projeto = projetos_manager.get_projeto(projeto_id)
    if projeto:
        # Verifica se houve mudança de sessão
        mudou_sessao = projetos_manager.verificar_mudanca_sessao(projeto_id)
        historico = projetos_manager.get_historico(projeto_id)
        
        if historico:
            contexto_adicional = f"\n\n[CONTEXTO DO PROJETO '{projeto['nome']}']\n"
            if projeto.get('descricao'):
                contexto_adicional += f"Descrição: {projeto['descricao']}\n"
            
            if mudou_sessao:
                # Se mudou sessão, envia conversa inteira
                contexto_adicional += "Histórico completo da conversa (nova sessão detectada):\n"
                for msg in historico:
                    contexto_adicional += f"- {msg['sender']}: {msg['message']}\n"
                print(f"🔄 [ASK-PROJETO] NOVA SESSÃO DETECTADA!")
                print(f"📤 [ASK-PROJETO] Enviando TODA A CONVERSA: {len(historico)} mensagens completas")
                print(f"🏷️  [ASK-PROJETO] Projeto: '{projeto['nome']}' (ID: {projeto_id})")
            else:
                # Se mesma sessão, envia apenas últimas 5 mensagens
                contexto_adicional += "Histórico recente da conversa:\n"
                ultimas_msgs = historico[-5:] if len(historico) > 5 else historico
                for msg in ultimas_msgs:
                    contexto_adicional += f"- {msg['sender']}: {msg['message']}\n"
                print(f"⏩ [ASK-PROJETO] MESMA SESSÃO - continuando conversa")
                print(f"📤 [ASK-PROJETO] Enviando apenas ÚLTIMAS 5 mensagens: {len(ultimas_msgs)} de {len(historico)} total")
                print(f"🏷️  [ASK-PROJETO] Projeto: '{projeto['nome']}' (ID: {projeto_id})")
            
            contexto_adicional += "[FIM DO CONTEXTO]\n"
        else:
            print(f"📝 [ASK-PROJETO] SEM HISTÓRICO - Primeira mensagem do projeto!")
            print(f"🏷️  [ASK-PROJETO] Projeto: '{projeto['nome']}' (ID: {projeto_id})")
        
        # Atualiza a sessão do projeto após processar o contexto
        projetos_manager.atualizar_sessao_projeto(projeto_id)
    
    # Faz a pergunta com contexto
    pergunta_com_contexto = contexto_adicional + pergunta if contexto_adicional else pergunta
    resultado = ezinho_assistant.responder(pergunta_com_contexto)
    resposta = resultado.get('resposta')
    query = resultado.get('query')
    
    # Salva pergunta e resposta no projeto
    projetos_manager.salvar_mensagem(projeto_id, 'usuario', pergunta, 'user')
    projetos_manager.salvar_mensagem(projeto_id, 'ezpocket', resposta, 'bot')
    
    print(f"✅ [ASK-PROJETO] Resposta enviada com sucesso!")
    print(f"💾 [ASK-PROJETO] Mensagens salvas no projeto {projeto_id}")
    print(f"📊 [ASK-PROJETO] Resposta: '{resposta[:100]}{'...' if len(resposta) > 100 else ''}'\n")
    
    return jsonify({'resposta': resposta, 'query': query})

# ===== ROTAS DE PROJETOS =====

@app.route('/projetos/criar', methods=['POST'])
def criar_projeto():
    """Cria um novo projeto"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    data = request.get_json()
    nome = data.get('nome', '').strip()
    descricao = data.get('descricao', '').strip()
    
    if not nome:
        return jsonify({'success': False, 'message': 'Nome do projeto é obrigatório'}), 400
    
    resultado = projetos_manager.criar_projeto(nome, descricao)
    
    if resultado['success']:
        return jsonify(resultado)
    else:
        return jsonify(resultado), 400

@app.route('/projetos/listar', methods=['GET'])
def listar_projetos():
    """Lista todos os projetos do usuário"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    projetos = projetos_manager.listar_projetos()
    return jsonify(projetos)

@app.route('/projetos/<int:projeto_id>', methods=['DELETE'])
def deletar_projeto(projeto_id):
    """Deleta um projeto"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    resultado = projetos_manager.deletar_projeto(projeto_id)
    
    if resultado['success']:
        return jsonify(resultado)
    else:
        return jsonify(resultado), 400

@app.route('/projetos/<int:projeto_id>/historico', methods=['GET'])
def get_historico_projeto(projeto_id):
    """Pega o histórico de mensagens do projeto"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    historico = projetos_manager.get_historico(projeto_id)
    return jsonify(historico)

@app.route('/projetos/<int:projeto_id>/mensagem', methods=['POST'])
def salvar_mensagem_projeto(projeto_id):
    """Salva uma mensagem no projeto"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    data = request.get_json()
    sender = data.get('sender')
    message = data.get('message')
    type_msg = data.get('type')
    
    if not all([sender, message, type_msg]):
        return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
    
    sucesso = projetos_manager.salvar_mensagem(projeto_id, sender, message, type_msg)
    
    if sucesso:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Erro ao salvar mensagem'}), 400

@app.route('/projetos/contexto', methods=['POST'])
def salvar_contexto_projeto():
    """Salva o contexto da IA para um projeto"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    data = request.get_json()
    projeto_id = data.get('projeto_id')
    historico = data.get('historico')
    
    if not projeto_id:
        return jsonify({'success': False, 'message': 'ID do projeto é obrigatório'}), 400
    
    # Aqui você pode implementar lógica para preparar contexto para a IA
    # Por exemplo, resumir o histórico ou extrair informações importantes
    
    sucesso = projetos_manager.salvar_contexto(projeto_id, {
        'historico': historico,
        'resumo': f'Projeto com {len(historico) if historico else 0} mensagens',
        'ultimo_acesso': datetime.now().isoformat()
    })
    
    if sucesso:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Erro ao salvar contexto'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
