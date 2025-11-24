// Detecta automaticamente o host (usa o host atual da página)
const WEBSOCKET_URL = window.location.origin.replace(/:\d+/, ':5008');

let socket = null;
let currentJobId = null;
let waitingForConfirmation = false;
let waitingForFeedback = false;
let currentRating = 0;
let feedbackData = null;

function formatMarkdownResponse(text) {
    // Converter Markdown para HTML bonito
    let html = text;
    
    // Títulos ## → <h2>
    html = html.replace(/^## (.*?)$/gm, '<h2 class="response-title">$1</h2>');
    
    // Negrito **texto** → <strong>
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Listas - X. texto → <li>
    html = html.replace(/^\d+\.\s+(.*?)$/gm, '<li>$1</li>');
    html = html.replace(/^-\s+(.*?)$/gm, '<li>$1</li>');
    
    // Envolver <li> consecutivos em <ol> ou <ul>
    html = html.replace(/(<li>.*?<\/li>\s*)+/gs, (match) => {
        return `<ul class="response-list">${match}</ul>`;
    });
    
    // Quebras de linha duplas → <br><br>
    html = html.replace(/\n\n/g, '<br><br>');
    
    // Quebras de linha simples → <br>
    html = html.replace(/\n/g, '<br>');
    
    return html;
}

function addMessage(text, type = 'assistant') {
    const chatBox = document.getElementById('chatBox');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;
    msgDiv.innerHTML = text;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
    return msgDiv;
}

function setStatus(text) {
    const statusDiv = document.getElementById('status');
    if (text) {
        statusDiv.innerHTML = `<div class="typing-indicator"><span></span><span></span><span></span></div> ${text}`;
    } else {
        statusDiv.textContent = '';
    }
}

function setConnectionStatus(connected) {
    const statusEl = document.getElementById('connectionStatus');
    if (connected) {
        statusEl.textContent = '🟢 Conectado';
    } else {
        statusEl.textContent = '🔴 Desconectado';
    }
}

function enableInput() {
    document.getElementById('btnEnviar').disabled = false;
    document.getElementById('pergunta').disabled = false;
}

function disableInput() {
    document.getElementById('btnEnviar').disabled = true;
    document.getElementById('pergunta').disabled = true;
}

function getUserConfig() {
    return {
        username: document.getElementById('username').value.trim() || 'test_user',
        projeto: document.getElementById('projeto').value.trim() || 'test_project'
    };
}

function flushRedis() {
    if (!socket) {
        addMessage('❌ WebSocket não conectado', 'error');
        return;
    }
    
    const config = getUserConfig();
    
    if (!confirm(`Tem certeza que deseja REMOVER TUDO para:\nUsuário: ${config.username}\nProjeto: ${config.projeto}\n\nIsso vai limpar: jobs ativos, jobs finalizados, cache, sessões e todos os dados no Redis.`)) {
        return;
    }
    
    addMessage(`🗑️ Removendo todos os dados do usuário/projeto do Redis...`, 'system');
    
    socket.emit('flush_redis', {
        username: config.username,
        projeto: config.projeto
    });
}

function showConfirmation(planData) {
    waitingForConfirmation = true;
    
    // Modo development: mostrar plano completo
    if (FRONTEND_MODE === 'development') {
        const msgDiv = addMessage('', 'confirmation');
        msgDiv.innerHTML = `
            <strong>📋 PLANO CRIADO</strong>
            <div style="margin-top: 10px;">
                <strong>Plano:</strong><br>
                ${planData.plan}
            </div>
            <div style="margin-top: 10px;">
                <strong>Passos:</strong><br>
                ${planData.plan_steps.map((step, i) => `${i+1}. ${step}`).join('<br>')}
            </div>
        `;
    }
    
    // Fazer pergunta no chat (sempre, em ambos os modos)
    addMessage('🤔 Deseja prosseguir com este plano? (s/n)', 'assistant');
    enableInput();
    document.getElementById('pergunta').placeholder = 'Digite s para SIM ou n para NÃO...';
    document.getElementById('pergunta').focus();
}

function showFeedback(data) {
    console.log('============================================================');
    console.log('📊 showFeedback CHAMADO!');
    console.log('Data recebida:', data);
    console.log('Response text length:', data.response_text ? data.response_text.length : 0);
    console.log('============================================================');
    
    waitingForFeedback = 'rating';
    feedbackData = data;
    
    // Converter Markdown para HTML formatado
    const formattedResponse = formatMarkdownResponse(data.response_text);
    
    // Mostrar a resposta formatada
    const msgDiv = addMessage('', 'assistant');
    msgDiv.innerHTML = `<div class="response-container">${formattedResponse}</div>`;
    
    // Fazer pergunta de rating
    setTimeout(() => {
        addMessage('⭐ Rating (1-5):', 'assistant');
        addMessage('  1 = Péssima\n  2 = Ruim\n  3 = Regular\n  4 = Boa\n  5 = Excelente', 'assistant');
        addMessage('Digite o rating (1-5):', 'assistant');
        enableInput();
        document.getElementById('pergunta').placeholder = 'Digite um número de 1 a 5...';
        document.getElementById('pergunta').focus();
        console.log('✅ Tela de feedback exibida, aguardando input do usuário');
    }, 100);
}

function showUserProposedPlan(data) {
    waitingForConfirmation = false;
    waitingForFeedback = false;
    
    // Estado especial para sugestão
    window.waitingForUserSuggestion = true;
    
    // Mostrar mensagem apenas em modo development
    if (FRONTEND_MODE !== 'production') {
        addMessage('❌ O plano anterior foi rejeitado', 'system');
        addMessage(`📝 Pergunta original: ${data.pergunta}`, 'assistant');
    }
    
    setTimeout(() => {
        addMessage('💬 O que você quer que a IA faça?', 'assistant');
        enableInput();
        document.getElementById('pergunta').placeholder = 'Digite sua sugestão...';
        document.getElementById('pergunta').focus();
    }, 100);
}

function initWebSocket() {
    console.log('Conectando ao WebSocket:', WEBSOCKET_URL);
    socket = io(WEBSOCKET_URL, {
        transports: ['websocket', 'polling']
    });

    socket.on('connect', () => {
        console.log('WebSocket conectado!');
        setConnectionStatus(true);
        if (FRONTEND_MODE !== 'production') {
            addMessage('✅ Conectado ao servidor', 'system');
        }
        enableInput();
    });

    socket.on('disconnect', () => {
        console.log('WebSocket desconectado');
        setConnectionStatus(false);
        if (FRONTEND_MODE !== 'production') {
            addMessage('🔴 Desconectado do servidor', 'system');
        }
        disableInput();
    });

    socket.on('connected', (data) => {
        console.log('Mensagem do servidor:', data.message);
        // Não mostrar mensagem de conexão no chat em modo production
    });

    socket.on('job_started', (data) => {
        console.log('Job iniciado:', data);
        currentJobId = data.job_id;
        
        // No modo production, não mostrar detalhes técnicos
        if (FRONTEND_MODE === 'production') {
            setStatus('Processando sua pergunta...');
        } else {
            addMessage(`🚀 Job iniciado: ${data.job_id.substring(0, 8)}...`, 'system');
            addMessage(`📋 Módulo inicial: ${data.module}`, 'system');
            addMessage(`🔀 Fluxo esperado: ${data.expected_flow}`, 'system');
            setStatus('Processando...');
        }
    });

    socket.on('module_update', (data) => {
        console.log('Atualização do módulo:', data);
        
        // Módulos que NÃO devem ser exibidos no modo production
        const hiddenModulesInProduction = [
            'intent_validator',
            'history_preferences', 
            'plan_builder',
            'plan_refiner',
            'plan_confirm',
            'user_proposed_plan',
            'analysis_orchestrator',
            'sql_validator',
            'athena_executor',
            'python_runtime',
            'response_composer'
        ];
        
        if (FRONTEND_MODE === 'production' && hiddenModulesInProduction.includes(data.module)) {
            // No modo production, apenas atualizar a barra de status
            const emoji = getModuleEmoji(data.module);
            setStatus(`${emoji} Processando: ${getModuleFriendlyName(data.module)}...`);
            return; // Não exibir no chat
        }
        
        // Modo development ou módulos sempre visíveis
        const emoji = getModuleEmoji(data.module);
        addMessage(`${emoji} ${data.module.toUpperCase()}\n\n${data.message}`, 'assistant');
    });

    socket.on('status_update', (data) => {
        console.log('Atualização de status:', data);
        // No modo production, não sobrescrever o status de módulo
        if (FRONTEND_MODE === 'development') {
            setStatus(`Status: ${data.status} ${data.branches_count > 0 ? `(${data.branches_count} branches)` : ''}`);
        }
    });

    socket.on('need_input', (data) => {
        console.log('============================================================');
        console.log('🔔 EVENTO need_input RECEBIDO!');
        console.log('Tipo:', data.type);
        console.log('Data:', data);
        console.log('============================================================');
        setStatus('');
        
        if (data.type === 'plan_confirmation') {
            console.log('→ Chamando showConfirmation()');
            showConfirmation(data.data);
        } else if (data.type === 'user_feedback') {
            console.log('→ Chamando showFeedback()');
            showFeedback(data.data);
        } else if (data.type === 'user_proposed_plan') {
            console.log('→ Chamando showUserProposedPlan()');
            showUserProposedPlan(data.data);
        } else {
            console.error('⚠️ Tipo de input desconhecido:', data.type);
        }
    });

    socket.on('input_received', (data) => {
        console.log('Input recebido:', data);
        if (FRONTEND_MODE !== 'production') {
            addMessage(`✓ ${data.message}`, 'system');
            if (data.next_module) {
                setStatus(`Próximo módulo: ${data.next_module}`);
            }
        }
    });

    socket.on('job_completed', (data) => {
        console.log('Job completado:', data);
        if (FRONTEND_MODE !== 'production') {
            const statusEmoji = data.status === 'completed' ? '✅' : '❌';
            addMessage(`${statusEmoji} JOB ${data.status.toUpperCase()}`, 'system');
            addMessage(`📊 Total de etapas: ${data.execution_chain_length}`, 'system');
        }
        setStatus('');
        currentJobId = null;
        enableInput();
    });

    socket.on('error', (data) => {
        console.error('Erro do servidor:', data);
        addMessage(`❌ Erro: ${data.message}`, 'error');
        setStatus('');
        enableInput();
    });

    socket.on('redis_flushed', (data) => {
        console.log('Redis flushed:', data);
        addMessage(`✅ Limpeza completa realizada!`, 'system');
        
        if (data.total_deleted > 0 || data.sessions_closed > 0) {
            if (data.keys_deleted > 0) {
                addMessage(`🗑️ ${data.keys_deleted} chave(s) de interação`, 'system');
            }
            if (data.jobs_deleted > 0) {
                addMessage(`🗑️ ${data.jobs_deleted} job(s)`, 'system');
            }
            if (data.sessions_closed > 0) {
                addMessage(`🔌 ${data.sessions_closed} sessão(ões) encerrada(s)`, 'system');
            }
            addMessage(`📊 Total: ${data.total_deleted} item(s) deletado(s)`, 'system');
            
            // Resetar estado do frontend
            currentJobId = null;
            waitingForConfirmation = false;
            waitingForFeedback = false;
            window.waitingForUserSuggestion = false;
            enableInput();
            setStatus('');
        } else {
            addMessage(`ℹ️ Nenhum item encontrado para remover`, 'system');
        }
    });

    socket.on('jobs_cleaned', (data) => {
        console.log('Jobs cleaned:', data);
        addMessage(`✅ Histórico limpo com sucesso!`, 'system');
        
        if (data.jobs_deleted > 0) {
            addMessage(`🗑️ ${data.jobs_deleted} job(s) completado(s) removido(s)`, 'system');
        }
        if (data.jobs_kept > 0) {
            addMessage(`📌 ${data.jobs_kept} job(s) ativo(s) mantido(s)`, 'system');
        }
        if (data.jobs_deleted === 0) {
            addMessage(`ℹ️ Nenhum job completado encontrado`, 'system');
        }
    });
}

function getModuleEmoji(module) {
    const emojis = {
        'intent_validator': '🛡️',
        'plan_builder': '📋',
        'plan_confirm': '✅',
        'history_preferences': '🧠',
        'router': '🔀',
        'generator': '⚙️',
        'sql_validator': '🔍',
        'auto_correction': '🔧',
        'athena_executor': '⚡',
        'python_runtime': '🐍',
        'response_composer': '🎨',
        'user_feedback': '📊'
    };
    return emojis[module] || '📦';
}

function getModuleFriendlyName(module) {
    const names = {
        'intent_validator': 'Validando intenção',
        'plan_builder': 'Criando plano',
        'plan_confirm': 'Aguardando confirmação',
        'history_preferences': 'Carregando histórico',
        'analysis_orchestrator': 'Analisando dados',
        'sql_validator': 'Validando consulta',
        'auto_correction': 'Corrigindo consulta',
        'athena_executor': 'Executando consulta',
        'python_runtime': 'Processando resultados',
        'response_composer': 'Gerando resposta',
        'user_feedback': 'Aguardando feedback'
    };
    return names[module] || module.replace(/_/g, ' ');
}

function enviarPergunta() {
    const input = document.getElementById('pergunta');
    const texto = input.value.trim();
    
    if (!texto || !socket) return;
    
    // Resetar placeholder
    input.placeholder = 'Digite sua pergunta...';
    
    // Adiciona texto do usuário
    addMessage(texto, 'user');
    input.value = '';
    
    // Verificar se está aguardando sugestão do usuário
    if (window.waitingForUserSuggestion) {
        window.waitingForUserSuggestion = false;
        disableInput();
        setStatus('Enviando sugestão...');
        
        socket.emit('send_input', {
            job_id: currentJobId,
            input_type: 'user_proposed_plan',
            input_value: texto
        });
        addMessage('📤 Sugestão enviada', 'system');
        return;
    }
    
    // Verificar se está aguardando confirmação
    if (waitingForConfirmation) {
        const resposta = texto.toLowerCase().trim();
        console.log('[DEBUG] Resposta recebida:', resposta);
        console.log('[DEBUG] Tipo:', typeof resposta);
        
        if (resposta === 's' || resposta === 'sim' || resposta === 'y' || resposta === 'yes') {
            console.log('[DEBUG] Plano APROVADO - enviando true');
            waitingForConfirmation = false;
            disableInput();
            setStatus('Enviando confirmação...');
            
            socket.emit('send_input', {
                job_id: currentJobId,
                input_type: 'plan_confirmation',
                input_value: true
            });
            if (FRONTEND_MODE !== 'production') {
                addMessage('✅ Plano aprovado', 'system');
            }
            return;
        } else if (resposta === 'n' || resposta === 'nao' || resposta === 'não' || resposta === 'no') {
            console.log('[DEBUG] Plano REJEITADO - enviando false');
            waitingForConfirmation = false;
            disableInput();
            setStatus('Enviando rejeição...');
            
            socket.emit('send_input', {
                job_id: currentJobId,
                input_type: 'plan_confirmation',
                input_value: false
            });
            if (FRONTEND_MODE !== 'production') {
                addMessage('❌ Plano rejeitado', 'system');
            }
            return;
        } else {
            addMessage('❌ Resposta inválida. Digite "s" ou "n"', 'system');
            enableInput();
            return;
        }
    }
    
    // Verificar se está aguardando rating
    if (waitingForFeedback === 'rating') {
        const rating = parseInt(texto);
        if (isNaN(rating) || rating < 1 || rating > 5) {
            addMessage('❌ Rating inválido. Digite um número de 1 a 5', 'system');
            enableInput();
            return;
        }
        
        currentRating = rating;
        waitingForFeedback = 'comment';
        
        // Enviar rating
        socket.emit('send_input', {
            job_id: currentJobId,
            input_type: 'user_feedback_rating',
            input_value: rating
        });
        
        // Pedir comentário
        setTimeout(() => {
            addMessage('💭 Comentário (Enter para pular):', 'assistant');
            enableInput();
            input.placeholder = 'Digite seu comentário ou pressione Enter...';
            input.focus();
        }, 100);
        return;
    }
    
    // Verificar se está aguardando comentário
    if (waitingForFeedback === 'comment') {
        waitingForFeedback = false;
        disableInput();
        setStatus('Enviando feedback...');
        
        socket.emit('send_input', {
            job_id: currentJobId,
            input_type: 'user_feedback_comment',
            input_value: texto
        });
        
        addMessage(`✅ Feedback enviado: ${currentRating} estrelas`, 'system');
        return;
    }
    
    // Nova pergunta normal
    disableInput();
    setStatus('Enviando pergunta...');
    
    const config = getUserConfig();
    
    socket.emit('start_job', {
        pergunta: texto,
        username: config.username,
        projeto: config.projeto,
        module: 'intent_validator'
    });
}

// Enter para enviar
document.getElementById('pergunta').addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !document.getElementById('btnEnviar').disabled) {
        enviarPergunta();
    }
});

// Inicializar WebSocket quando a página carregar
window.addEventListener('load', () => {
    initWebSocket();
});
