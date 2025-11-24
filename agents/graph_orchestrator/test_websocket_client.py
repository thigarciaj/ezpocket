#!/usr/bin/env python3
"""
Script de teste simples para verificar o WebSocket endpoint
"""

import socketio
import time

# Criar cliente Socket.IO
sio = socketio.Client()

# Event handlers
@sio.on('connect')
def on_connect():
    print('✅ Conectado ao servidor!')

@sio.on('disconnect')
def on_disconnect():
    print('🔴 Desconectado do servidor')

@sio.on('connected')
def on_connected(data):
    print(f'📡 Servidor diz: {data["message"]}')

@sio.on('job_started')
def on_job_started(data):
    print(f'\n🚀 Job iniciado!')
    print(f'   Job ID: {data["job_id"]}')
    print(f'   Módulo: {data["module"]}')
    print(f'   Fluxo: {data["expected_flow"]}\n')

@sio.on('module_update')
def on_module_update(data):
    print(f'\n📦 {data["module"].upper()}')
    print(f'   {data["message"][:100]}...\n')

@sio.on('status_update')
def on_status_update(data):
    print(f'📊 Status: {data["status"]}')

@sio.on('need_input')
def on_need_input(data):
    print(f'\n⏸️  Input necessário: {data["type"]}')
    
    if data["type"] == "plan_confirmation":
        print('   Aprovando plano automaticamente...')
        sio.emit('send_input', {
            'job_id': current_job_id,
            'input_type': 'plan_confirmation',
            'input_value': True
        })

@sio.on('job_completed')
def on_job_completed(data):
    print(f'\n✅ JOB COMPLETADO!')
    print(f'   Status: {data["status"]}')
    print(f'   Etapas: {data["execution_chain_length"]}\n')
    sio.disconnect()

@sio.on('error')
def on_error(data):
    print(f'\n❌ ERRO: {data["message"]}\n')
    sio.disconnect()

# Variável global para job_id
current_job_id = None

def test_websocket():
    """Testa conexão WebSocket com uma pergunta"""
    global current_job_id
    
    try:
        # Conectar ao servidor
        print('🔄 Conectando ao servidor WebSocket...')
        sio.connect('http://localhost:5008')
        
        # Aguardar conexão
        time.sleep(1)
        
        # Enviar pergunta de teste
        print('📨 Enviando pergunta de teste...')
        sio.emit('start_job', {
            'pergunta': 'Quantos pedidos temos hoje?',
            'username': 'test_user',
            'projeto': 'test_project'
        })
        
        # Aguardar processamento (máximo 60 segundos)
        print('⏳ Aguardando processamento...\n')
        sio.wait()
        
    except Exception as e:
        print(f'❌ Erro: {str(e)}')
    finally:
        if sio.connected:
            sio.disconnect()

if __name__ == '__main__':
    test_websocket()
