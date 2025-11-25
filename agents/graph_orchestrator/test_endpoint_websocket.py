"""
Endpoint de teste para o Graph Orchestrator com suporte a WebSocket
Permite testar o orquestrador com comunicação em tempo real
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import sys
import os
from dotenv import load_dotenv
import json
import threading
import time
from datetime import datetime

# Carrega variáveis de ambiente do .env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config', '.env')
load_dotenv(dotenv_path)

# Adiciona o caminho do backend ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.graph_orchestrator.graph_orchestrator import GraphOrchestrator
from agents.graph_orchestrator.graph_config import EXPECTED_FLOW

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Inicializa SocketIO com configurações para permitir CORS
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=True)

# Inicializa o orquestrador
orchestrator = GraphOrchestrator()

# Armazena sessões ativas (job_id -> sid)
active_sessions = {}
# Armazena inputs pendentes (job_id -> waiting_for)
pending_inputs = {}


def monitor_job(job_id: str, sid: str):
    """
    Thread que monitora o status do job e envia atualizações via WebSocket
    Monitora também as chaves do Redis para inputs do usuário
    """
    print(f"[MONITOR] Iniciando monitoramento do job {job_id[:8]}... para sid {sid}")
    last_chain_length = 0
    last_status = None
    confirmation_checked = False
    feedback_checked = False  # Flag para evitar loop infinito
    user_plan_checked = False  # Flag para user_proposed_plan
    username = None
    projeto = None
    
    while True:
        try:
            # Buscar status do job com branches
            status = orchestrator.get_job_with_branches(job_id)
            
            if not status:
                print(f"[MONITOR] Job {job_id[:8]}... não encontrado (pode ter sido deletado via flush)")
                # Apenas encerrar o monitor silenciosamente
                break
            
            # Extrair username e projeto
            if not username:
                username = status.get('username', 'test_user')
                projeto = status.get('projeto', 'test_project')
            
            current_status = status.get('consolidated_status', status.get('status'))
            execution_chain = status.get('execution_chain', [])
            
            # Enviar novas etapas da execution_chain
            if len(execution_chain) > last_chain_length:
                new_steps = execution_chain[last_chain_length:]
                for step in new_steps:
                    module = step.get('module', 'unknown')
                    output = step.get('output', {})
                    success = step.get('success', False)
                    
                    # Formatar mensagem baseada no módulo
                    message = format_module_output(module, output, success)
                    
                    socketio.emit('module_update', {
                        'module': module,
                        'message': message,
                        'output': output,
                        'success': success,
                        'timestamp': step.get('timestamp')
                    }, room=sid)
                
                last_chain_length = len(execution_chain)
            
            # Atualizar status
            if current_status != last_status:
                socketio.emit('status_update', {
                    'status': current_status,
                    'branches_count': status.get('branches_count', 0)
                }, room=sid)
                last_status = current_status
            
            # MONITORAR CHAVES DO REDIS (igual ao modo interativo)
            if username and projeto:
                # Verificar plan_confirm (pode acontecer múltiplas vezes após refinamentos)
                if not confirmation_checked:
                    pending_key = f"plan_confirm:pending:{username}:{projeto}"
                    exists = orchestrator.redis_client.exists(pending_key)
                    print(f"[MONITOR] 🔍 Verificando chave Redis: {pending_key} (existe: {exists})")
                    
                    if exists:
                        plan_data = orchestrator.redis_client.hgetall(pending_key)
                        print(f"[MONITOR] ✅ Plan confirm detectado via Redis: {pending_key}")
                        print(f"[MONITOR] 📤 Emitindo module_update de plan_confirm com show_buttons=true para sid {sid}")
                        print(f"[MONITOR] 📋 Plan data: {plan_data.get('plan', '')[:100]}...")
                        
                        # Montar mensagem formatada do plano
                        plan_text = plan_data.get('plan', '')
                        plan_steps_raw = plan_data.get('plan_steps', '[]')
                        
                        # Tentar parsear JSON se for string
                        try:
                            plan_steps = json.loads(plan_steps_raw) if isinstance(plan_steps_raw, str) else plan_steps_raw
                        except:
                            plan_steps = []
                        
                        plan_message = f"📋 **Plano de Análise**\n\n{plan_text}\n\n**Passos:**\n"
                        for i, step in enumerate(plan_steps, 1):
                            plan_message += f"{i}. {step}\n"
                        
                        socketio.emit('module_update', {
                            'module': 'plan_confirm',
                            'message': plan_message,
                            'output': {
                                'plan': plan_text,
                                'plan_steps': plan_steps
                            },
                            'success': True,
                            'timestamp': datetime.utcnow().isoformat(),
                            'show_buttons': True  # Flag para mostrar botões de confirmação
                        }, room=sid)
                        pending_inputs[job_id] = 'plan_confirmation'
                        confirmation_checked = True
                        print(f"[MONITOR] ✅ confirmation_checked=True (aguardando resposta do usuário)")
                
                # Verificar user_feedback (só uma vez por job)
                # Emitir evento para usuário digitar nota de 1 a 5
                feedback_key = f"user_feedback:pending:{username}:{projeto}"
                if not feedback_checked:
                    exists = orchestrator.redis_client.exists(feedback_key)
                    if exists:
                        feedback_data = orchestrator.redis_client.hgetall(feedback_key)
                        print(f"\n{'='*80}")
                        print(f"[MONITOR] 📊 USER FEEDBACK DETECTADO!")
                        print(f"[MONITOR] Key: {feedback_key}")
                        print(f"[MONITOR] Pergunta: {feedback_data.get('pergunta', '')}")
                        print(f"[MONITOR] 📤 Emitindo module_update para pedir nota ao usuário")
                        print(f"{'='*80}\n")
                        
                        # Emitir evento pedindo nota
                        socketio.emit('module_update', {
                            'module': 'user_feedback',
                            'message': 'Resposta gerada com sucesso!',
                            'output': {},
                            'success': True,
                            'timestamp': datetime.utcnow().isoformat(),
                            'show_rating': True  # Flag para pedir nota
                        }, room=sid)
                        
                        pending_inputs[job_id] = 'user_feedback'
                        feedback_checked = True
                        print(f"[MONITOR] ✅ feedback_checked=True (aguardando nota do usuário)")
                
                # Verificar user_proposed_plan (quando usuário rejeita o plano)
                # Pode acontecer múltiplas vezes (loop de refinamento)
                if not user_plan_checked:
                    user_plan_key = f"user_proposed_plan:pending:{username}:{projeto}"
                    if orchestrator.redis_client.exists(user_plan_key):
                        user_plan_data = orchestrator.redis_client.hgetall(user_plan_key)
                        print(f"[MONITOR] User proposed plan detectado via Redis")
                        print(f"[MONITOR] Usuário pode propor plano alternativo")
                        
                        socketio.emit('need_input', {
                            'type': 'user_proposed_plan',
                            'data': {
                                'pergunta': user_plan_data.get('pergunta', ''),
                                'rejected_plan': user_plan_data.get('rejected_plan', '')
                            }
                        }, room=sid)
                        pending_inputs[job_id] = 'user_proposed_plan'
                        user_plan_checked = True
                        # Resetar confirmation_checked para permitir nova confirmação do plano refinado
                        confirmation_checked = False
                        print(f"[MONITOR] Flags resetadas: confirmation_checked=False para permitir re-confirmação")
                
                # Se user_plan_checked e a chave não existe mais, resetar para permitir novo ciclo
                elif user_plan_checked:
                    user_plan_key = f"user_proposed_plan:pending:{username}:{projeto}"
                    if not orchestrator.redis_client.exists(user_plan_key):
                        # Worker processou, resetar flag para permitir nova rejeição
                        user_plan_checked = False
                        print(f"[MONITOR] user_plan_checked resetado - pronto para novo ciclo")
            
            # Verificar se completou
            if current_status in ['completed', 'failed', 'partial_failure']:
                socketio.emit('job_completed', {
                    'status': current_status,
                    'job_id': job_id,
                    'execution_chain_length': len(execution_chain)
                }, room=sid)
                print(f"[MONITOR] Job {job_id[:8]}... completado com status: {current_status}")
                break
            
            time.sleep(1)  # Poll a cada 1 segundo
            
        except Exception as e:
            print(f"[MONITOR] Erro no monitoramento: {str(e)}")
            import traceback
            traceback.print_exc()
            socketio.emit('error', {
                'message': f'Erro no monitoramento: {str(e)}'
            }, room=sid)
            
            # Agendar limpeza automática do job
            def cleanup_job():
                try:
                    cleanup_timeout = int(os.getenv('JOB_CLEANUP_TIMEOUT', 300))
                    time.sleep(cleanup_timeout)
                    if orchestrator.redis_client.exists(f"job:{job_id}"):
                        orchestrator.redis_client.delete(f"job:{job_id}")
                        print(f"[CLEANUP] 🗑️ Job {job_id[:8]}... deletado automaticamente após {cleanup_timeout}s")
                except Exception as e:
                    print(f"[CLEANUP] ⚠️ Erro ao limpar job {job_id[:8]}...: {e}")
            
            import threading
            cleanup_thread = threading.Thread(target=cleanup_job, daemon=True)
            cleanup_thread.start()
            
            break
    
    # Limpar sessão
    if job_id in active_sessions:
        del active_sessions[job_id]
    if job_id in pending_inputs:
        del pending_inputs[job_id]


def format_module_output(module: str, output: dict, success: bool) -> str:
    """Formata a saída do módulo para exibição"""
    
    # DEBUG: Ver o que está chegando
    print(f"\n[FORMAT_MODULE_OUTPUT] DEBUG:")
    print(f"  Module: {module}")
    print(f"  Success: {success}")
    print(f"  Output keys: {list(output.keys())}")
    print(f"  Output (primeiras 500 chars): {str(output)[:500]}\n")
    
    if not success:
        return f"❌ Erro no módulo {module}: {output.get('error', 'Erro desconhecido')}"
    
    if module == 'intent_validator':
        valid = output.get('intent_valid', False)
        category = output.get('intent_category', 'N/A')
        reason = output.get('intent_reason', 'N/A')
        
        if valid:
            return f"✅ Intent válida\n📂 Categoria: {category}\n💬 {reason}"
        else:
            return f"❌ Intent inválida\n💬 {reason}"
    
    elif module == 'plan_builder':
        plan = output.get('plan', 'N/A')
        steps = output.get('plan_steps', [])
        steps_text = '\n'.join([f"  {i+1}. {step}" for i, step in enumerate(steps)])
        
        return f"📋 Plano criado:\n{plan}\n\n📊 Passos:\n{steps_text}"
    
    elif module == 'plan_refiner':
        # Mostrar plano refinado da mesma forma que plan_builder
        refined_plan = output.get('refined_plan', output.get('plan', 'N/A'))
        refined_steps = output.get('refined_plan_steps', output.get('plan_steps', []))
        steps_text = '\n'.join([f"  {i+1}. {step}" for i, step in enumerate(refined_steps)])
        
        return f"🔄 **Plano Refinado:**\n{refined_plan}\n\n📊 Passos:\n{steps_text}"
    
    elif module == 'plan_confirm':
        # O worker retorna 'confirmed' e 'plan_accepted'
        confirmed = output.get('confirmed', False)
        plan_accepted = output.get('plan_accepted', False)
        approved = confirmed or plan_accepted
        
        if approved:
            return "✅ Plano aprovado pelo usuário"
        else:
            return "❌ Plano rejeitado pelo usuário"
    
    elif module == 'sql_validator':
        # DEBUG: Ver campos específicos
        print(f"[SQL_VALIDATOR FORMAT] valid={output.get('valid')}")
        print(f"[SQL_VALIDATOR FORMAT] sql_valid={output.get('sql_valid')}")
        print(f"[SQL_VALIDATOR FORMAT] query_sql={output.get('query_sql', 'N/A')[:100]}")
        print(f"[SQL_VALIDATOR FORMAT] sql_query={output.get('sql_query', 'N/A')[:100]}")
        
        # Aceitar 'valid' ou 'sql_valid'
        valid = output.get('valid', output.get('sql_valid', False))
        if valid:
            sql_query = output.get('query_sql', output.get('sql_query', ''))
            return f"✅ SQL válido\n```sql\n{sql_query}\n```"
        else:
            errors = output.get('errors', [])
            error_msg = output.get('error', '')
            validation_errors = output.get('validation_errors', [])
            
            result = "❌ SQL inválido\n\nErros:\n"
            
            if errors:
                result += '\n'.join([f"  • {err}" for err in errors])
            elif validation_errors:
                result += '\n'.join([f"  • {err}" for err in validation_errors])
            elif error_msg:
                result += f"  • {error_msg}"
            else:
                result += "  • Erro desconhecido (verifique os logs)"
            
            # Mostrar SQL que causou erro se disponível
            sql_query = output.get('query_sql', output.get('sql_query', ''))
            if sql_query:
                result += f"\n\n📝 SQL:\n```sql\n{sql_query}\n```"
            
            return result
    
    elif module == 'athena_executor':
        # DEBUG: Ver campos específicos
        print(f"[ATHENA_EXECUTOR FORMAT] rows_returned={output.get('rows_returned')}")
        print(f"[ATHENA_EXECUTOR FORMAT] row_count={output.get('row_count')}")
        print(f"[ATHENA_EXECUTOR FORMAT] data={output.get('data', [])[:2]}")
        print(f"[ATHENA_EXECUTOR FORMAT] results={output.get('results', [])[:2]}")
        print(f"[ATHENA_EXECUTOR FORMAT] execution_time={output.get('execution_time')}")
        
        # Aceitar 'row_count' ou 'rows_returned'
        rows = output.get('row_count', output.get('rows_returned', 0))
        # Aceitar 'results' ou 'data'
        data = output.get('results', output.get('data', []))
        execution_time = output.get('execution_time', 0)
        
        result = f"⚡ Query executada com sucesso\n📊 {rows} linha(s) retornada(s)\n⏱️ Tempo: {execution_time:.2f}s"
        
        # Mostrar dados se houver
        if data and len(data) > 0:
            result += "\n\n📋 Resultado:\n"
            # Mostrar até 5 linhas
            for i, row in enumerate(data[:5]):
                result += f"  {i+1}. {row}\n"
            if len(data) > 5:
                result += f"  ... e mais {len(data) - 5} linha(s)"
        elif rows == 0:
            result += "\n\nℹ️ Nenhum resultado encontrado"
        
        return result
    
    elif module == 'response_composer':
        # DEBUG: Ver campos específicos
        print(f"[RESPONSE_COMPOSER FORMAT] response_text exists: {('response_text' in output)}")
        print(f"[RESPONSE_COMPOSER FORMAT] response_text length: {len(output.get('response_text', ''))}")
        print(f"[RESPONSE_COMPOSER FORMAT] response_text preview: {output.get('response_text', '')[:200]}")
        
        response = output.get('response_text', '')
        if not response:
            return "⚠️ Resposta vazia gerada pelo response_composer"
        # Retornar response_text puro, já vem formatado do agente
        return response
    
    elif module == 'user_feedback':
        rating = output.get('rating', 0)
        comment = output.get('comment', '')
        return f"📊 Feedback recebido: {rating} ⭐\n💬 {comment if comment else 'Sem comentário'}"
    
    elif module == 'analysis_orchestrator':
        query_sql = output.get('query_sql', '')
        explanation = output.get('query_explanation', '')
        
        result = "⚙️ Query SQL gerada:\n\n"
        if query_sql:
            result += f"```sql\n{query_sql}\n```\n\n"
        if explanation:
            result += f"📝 Explicação:\n{explanation}"
        
        return result
    
    else:
        # Formato genérico
        return f"✅ {module} executado com sucesso"


# Função removida - agora o monitoramento é feito via Redis keys


@app.route('/')
def index():
    """Serve o frontend WebSocket"""
    frontend_mode = os.getenv('FRONTEND_MODE', 'production')
    return render_template('dashboard.html', frontend_mode=frontend_mode)


@app.route('/test-orchestrator/health', methods=['GET'])
def health():
    """Verifica se o serviço está rodando"""
    from agents.graph_orchestrator.graph_orchestrator import REDIS_CONFIG
    
    try:
        redis_status = "connected" if orchestrator.redis_client.ping() else "disconnected"
    except:
        redis_status = "error"
    
    return jsonify({
        "status": "healthy",
        "service": "Graph Orchestrator WebSocket Endpoint",
        "version": "2.0.0",
        "port": int(os.getenv('GRAPH_ORCHESTRATOR_PORT', 5008)),
        "websocket": "enabled",
        "redis_status": redis_status,
        "redis_host": REDIS_CONFIG['host'],
        "redis_port": REDIS_CONFIG['port']
    })


# =====================================================
# WEBSOCKET EVENTS
# =====================================================

@socketio.on('connect')
def handle_connect():
    """Cliente conectado via WebSocket"""
    print(f"[WS] Cliente conectado: {request.sid}")
    emit('connected', {'message': 'Conectado ao Graph Orchestrator'})


@socketio.on('disconnect')
def handle_disconnect():
    """Cliente desconectado"""
    print(f"[WS] Cliente desconectado: {request.sid}")


@socketio.on('start_job')
def handle_start_job(data):
    """Inicia um novo job e começa monitoramento"""
    try:
        pergunta = data.get('pergunta', '')
        username = data.get('username', 'test_user')
        projeto = data.get('projeto', 'test_project')
        module = data.get('module', 'intent_validator')
        
        if not pergunta:
            emit('error', {'message': 'Campo "pergunta" é obrigatório'})
            return
        
        print(f"\n{'='*80}")
        print(f"[WS] Novo job iniciado")
        print(f"[WS] Módulo: {module}")
        print(f"[WS] Pergunta: {pergunta}")
        print(f"[WS] Username: {username}")
        print(f"[WS] Projeto: {projeto}")
        print(f"[WS] SID: {request.sid}")
        print(f"{'='*80}\n")
        
        # Submete o job
        job_id = orchestrator.submit_job(
            start_module=module,
            username=username,
            projeto=projeto,
            initial_data={"pergunta": pergunta}
        )
        
        # Associar job_id com sid
        active_sessions[job_id] = request.sid
        
        # Entrar na room do job
        join_room(request.sid)
        
        # Enviar confirmação
        emit('job_started', {
            'job_id': job_id,
            'pergunta': pergunta,
            'module': module,
            'expected_flow': EXPECTED_FLOW.get(module, f"{module} (flow não definido)")
        })
        
        # Iniciar thread de monitoramento
        monitor_thread = threading.Thread(
            target=monitor_job,
            args=(job_id, request.sid),
            daemon=True
        )
        monitor_thread.start()
        
    except Exception as e:
        print(f"[WS] Erro ao iniciar job: {str(e)}")
        emit('error', {
            'message': f'Erro ao iniciar job: {str(e)}',
            'type': type(e).__name__
        })


@socketio.on('send_input')
def handle_send_input(data):
    """Recebe input do usuário e salva no Redis (igual ao modo interativo)"""
    try:
        job_id = data.get('job_id')
        input_type = data.get('input_type')
        input_value = data.get('input_value')
        
        if not job_id or not input_type:
            emit('error', {'message': 'job_id e input_type são obrigatórios'})
            return
        
        print(f"[WS] Input recebido: job={job_id[:8]}..., type={input_type}, value={input_value}")
        
        # Buscar job para pegar username e projeto
        job_data_json = orchestrator.redis_client.get(f"job:{job_id}")
        if not job_data_json:
            emit('error', {'message': 'Job não encontrado'})
            return
        
        job_data = json.loads(job_data_json)
        username = job_data.get('username', 'test_user')
        projeto = job_data.get('projeto', 'test_project')
        
        # Salvar no Redis usando as mesmas chaves do modo interativo
        if input_type == 'plan_confirmation':
            # Salvar resposta do plano (worker espera string 'true' ou 'false')
            response_key = f"plan_confirm:response:{username}:{projeto}"
            # IMPORTANTE: salvar apenas a string 'true' ou 'false' (não JSON)
            # Corrigir: comparar string explicitamente, não usar truthy/falsy
            if isinstance(input_value, str):
                value_to_save = input_value.lower()  # 'true' ou 'false' já vem como string
            else:
                value_to_save = 'true' if input_value else 'false'
            
            orchestrator.redis_client.set(response_key, value_to_save, ex=60)
            
            print(f"[WS] ========== DEBUG PLAN CONFIRMATION ==========")
            print(f"[WS] input_value recebido: {input_value} (tipo: {type(input_value)})")
            print(f"[WS] value_to_save: {value_to_save}")
            print(f"[WS] Chave Redis: {response_key}")
            print(f"[WS] ===============================================")
            
            # NÃO deletar pending - o worker faz isso
            
            emit('input_received', {
                'message': 'Confirmação recebida',
                'approved': value_to_save
            })
        
        elif input_type == 'user_feedback':
            # Receber rating completo (usado no dashboard WebSocket)
            feedback_response_key = f"user_feedback:response:{username}:{projeto}"
            orchestrator.redis_client.set(feedback_response_key, input_value, ex=60)
            
            print(f"[WS] ========== DEBUG USER FEEDBACK ==========")
            print(f"[WS] input_value: {input_value}")
            print(f"[WS] Chave Redis: {feedback_response_key}")
            print(f"[WS] =============================================")
            
            emit('input_received', {
                'message': 'Avaliação recebida'
            })
            
        elif input_type == 'user_feedback_rating':
            # Salvar rating temporariamente
            temp_key = f"user_feedback:temp_rating:{username}:{projeto}"
            orchestrator.redis_client.set(temp_key, input_value, ex=60)
            emit('input_received', {'message': 'Rating recebido, aguardando comentário'})
            
        elif input_type == 'user_feedback_comment':
            # Buscar rating salvo
            temp_key = f"user_feedback:temp_rating:{username}:{projeto}"
            rating = orchestrator.redis_client.get(temp_key)
            if not rating:
                rating = '5'  # Default
            
            # Salvar resposta completa
            feedback_response_key = f"user_feedback:response:{username}:{projeto}"
            feedback_response = {
                'rating': int(rating),
                'comment': input_value
            }
            orchestrator.redis_client.set(feedback_response_key, json.dumps(feedback_response), ex=60)
            
            # Remover pending e temp
            feedback_key = f"user_feedback:pending:{username}:{projeto}"
            orchestrator.redis_client.delete(feedback_key)
            orchestrator.redis_client.delete(temp_key)
            
            emit('input_received', {
                'message': 'Feedback recebido com sucesso'
            })
        
        elif input_type == 'user_proposed_plan':
            # Salvar sugestão do usuário
            user_plan_response_key = f"user_proposed_plan:response:{username}:{projeto}"
            orchestrator.redis_client.set(user_plan_response_key, input_value, ex=300)
            
            print(f"[WS] Sugestão do usuário salva: {user_plan_response_key}")
            print(f"[WS] Plan Refiner vai processar e retornar para Plan Confirm")
            
            # NÃO deletar pending - o worker faz isso
            
            # IMPORTANTE: Resetar flags para permitir nova confirmação do plano refinado
            # O monitor_job já reseta confirmation_checked quando detecta user_proposed_plan
            # Mas precisamos resetar user_plan_checked aqui para permitir múltiplas rejeições
            for active_job_id, sid in active_sessions.items():
                job = json.loads(orchestrator.redis_client.get(f"job:{active_job_id}") or '{}')
                if job.get('username') == username and job.get('projeto') == projeto:
                    # Flags serão resetadas na próxima iteração do monitor
                    print(f"[WS] Flags de controle serão resetadas para permitir nova confirmação")
                    break
            
            emit('input_received', {
                'message': 'Sugestão registrada e será processada pelo Plan Refiner'
            })
        
        # Remover de pending_inputs
        if job_id in pending_inputs:
            del pending_inputs[job_id]
        
    except Exception as e:
        print(f"[WS] Erro ao processar input: {str(e)}")
        import traceback
        traceback.print_exc()
        emit('error', {
            'message': f'Erro ao processar input: {str(e)}',
            'type': type(e).__name__
        })


@socketio.on('flush_redis')
def handle_flush_redis(data):
    """Remove TODOS os dados do usuário/projeto do Redis: jobs (ativos+completados), cache, sessões, interações"""
    try:
        username = data.get('username', 'test_user')
        projeto = data.get('projeto', 'test_project')
        
        print(f"\n{'='*80}")
        print(f"[WS] 🗑️ REMOVER TUDO DO REDIS - LIMPEZA TOTAL")
        print(f"[WS] Usuário: {username}")
        print(f"[WS] Projeto: {projeto}")
        print(f"{'='*80}\n")
        
        # 1. Deletar chaves de interação específicas
        patterns = [
            f"plan_confirm:pending:{username}:{projeto}",
            f"plan_confirm:response:{username}:{projeto}",
            f"user_feedback:pending:{username}:{projeto}",
            f"user_feedback:response:{username}:{projeto}",
            f"user_feedback:temp_rating:{username}:{projeto}",
            f"user_proposed_plan:pending:{username}:{projeto}",
            f"user_proposed_plan:response:{username}:{projeto}"
        ]
        
        deleted_count = 0
        for pattern in patterns:
            if orchestrator.redis_client.exists(pattern):
                orchestrator.redis_client.delete(pattern)
                deleted_count += 1
                print(f"[WS] 🗑️ Deletado: {pattern}")
        
        # 2. Buscar e deletar TODOS os jobs do usuário/projeto (ativos + completados)
        print(f"\n[WS] 🔍 Buscando TODOS os jobs de {username}/{projeto}...")
        all_job_keys = orchestrator.redis_client.keys("job:*")
        jobs_deleted = 0
        sessions_closed = 0
        
        for job_key in all_job_keys:
            try:
                job_data = orchestrator.redis_client.get(job_key)
                if job_data:
                    job_obj = json.loads(job_data)
                    if job_obj.get('username') == username and job_obj.get('projeto') == projeto:
                        job_id = job_key.decode('utf-8') if isinstance(job_key, bytes) else job_key
                        job_id = job_id.replace('job:', '')
                        
                        # Remover sessão ativa se existir
                        if job_id in active_sessions:
                            del active_sessions[job_id]
                            sessions_closed += 1
                            print(f"[WS] 🔌 Sessão fechada: {job_id[:8]}...")
                        
                        if job_id in pending_inputs:
                            del pending_inputs[job_id]
                        
                        # Deletar job do Redis (independente do status)
                        orchestrator.redis_client.delete(job_key)
                        jobs_deleted += 1
                        status = job_obj.get('consolidated_status', job_obj.get('status', 'unknown'))
                        print(f"[WS] 🗑️ Job [{status}] deletado: {job_id[:8]}...")
            except Exception as e:
                print(f"[WS] ⚠️ Erro ao processar {job_key}: {e}")
        
        # 3. Deletar TODAS as filas (queues) dos módulos
        print(f"\n[WS] 🔍 Removendo filas (queues) dos módulos...")
        queue_patterns = [
            "queue:intent_validator",
            "queue:plan_builder", 
            "queue:plan_confirm",
            "queue:history_preferences",
            "queue:analysis_orchestrator",
            "queue:plan_refiner",
            "queue:sql_validator",
            "queue:auto_correction",
            "queue:athena_executor",
            "queue:python_runtime",
            "queue:response_composer",
            "queue:user_feedback",
            "queue:user_proposed_plan"
        ]
        
        queues_deleted = 0
        for queue_name in queue_patterns:
            # Limpar toda a fila
            queue_length = orchestrator.redis_client.llen(queue_name)
            if queue_length > 0:
                orchestrator.redis_client.delete(queue_name)
                queues_deleted += 1
                print(f"[WS] 🗑️ Fila deletada: {queue_name} ({queue_length} items)")
        
        total_deleted = deleted_count + jobs_deleted + queues_deleted
        print(f"\n[WS] ✅ LIMPEZA TOTAL CONCLUÍDA:")
        print(f"     - Chaves de interação: {deleted_count}")
        print(f"     - Jobs (todos): {jobs_deleted}")
        print(f"     - Filas (queues): {queues_deleted}")
        print(f"     - Sessões fechadas: {sessions_closed}")
        print(f"     - Total removido: {total_deleted}\n")
        
        emit('redis_flushed', {
            'message': 'Todos os dados removidos do Redis (jobs, filas, cache, sessões)',
            'keys_deleted': deleted_count,
            'jobs_deleted': jobs_deleted,
            'queues_deleted': queues_deleted,
            'sessions_closed': sessions_closed,
            'total_deleted': total_deleted,
            'username': username,
            'projeto': projeto
        })
        
    except Exception as e:
        print(f"[WS] ❌ Erro ao fazer limpeza total do Redis: {str(e)}")
        import traceback
        traceback.print_exc()
        emit('error', {
            'message': f'Erro ao remover dados: {str(e)}',
            'type': type(e).__name__
        })


if __name__ == '__main__':
    from agents.graph_orchestrator.graph_orchestrator import REDIS_CONFIG
    
    print("=" * 80)
    print("🔄 GRAPH ORCHESTRATOR WEBSOCKET ENDPOINT")
    print("=" * 80)
    print(f"Porta: {os.getenv('GRAPH_ORCHESTRATOR_PORT', 5008)}")
    print(f"Redis: {REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}")
    print("\nWebSocket Events:")
    print("  connect              - Conexão estabelecida")
    print("  start_job            - Iniciar novo job")
    print("  send_input           - Enviar input do usuário")
    print("  flush_redis          - Limpar cache Redis")
    print("  disconnect           - Desconectar")
    print("\nHTTP Endpoints:")
    print("  GET  /                              - Frontend HTML")
    print("  GET  /test-orchestrator/health      - Status do serviço")
    print("=" * 80)
    
    port = int(os.getenv('GRAPH_ORCHESTRATOR_PORT', 5008))
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)
