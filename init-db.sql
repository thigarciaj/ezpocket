-- =====================================================
-- EZPOCKET LOGS DATABASE - PostgreSQL
-- Estrutura modular navegável por timestamp
-- =====================================================

-- Extensões
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =====================================================
-- MÓDULO 1: INTENT VALIDATOR AGENT (NÓ 0)
-- =====================================================

CREATE TABLE IF NOT EXISTS intent_validator_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Rastreio de execução
    execution_sequence INTEGER,  -- Ordem de execução no fluxo
    
    -- Identificação (sempre presente)
    username VARCHAR(100) NOT NULL,
    projeto VARCHAR(100) NOT NULL,
    horario TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Input
    pergunta TEXT NOT NULL,
    
    -- Validação
    intent_valid BOOLEAN NOT NULL,
    intent_category VARCHAR(100),
    intent_reason TEXT,
    
    -- Classificação
    is_special_case BOOLEAN DEFAULT FALSE,
    special_type VARCHAR(50),
    
    -- Segurança
    security_violation BOOLEAN DEFAULT FALSE,
    security_reason TEXT,
    forbidden_keywords TEXT[],
    
    -- Contexto
    input_length INTEGER,
    language_detected VARCHAR(10),
    
    -- Performance
    execution_time REAL,
    model_used VARCHAR(50),
    tokens_used INTEGER,
    
    -- Status
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    -- Metadata adicional
    metadata JSONB
);

CREATE INDEX idx_intent_validator_username ON intent_validator_logs(username);
CREATE INDEX idx_intent_validator_projeto ON intent_validator_logs(projeto);
CREATE INDEX idx_intent_validator_horario ON intent_validator_logs(horario DESC);
CREATE INDEX idx_intent_validator_username_projeto ON intent_validator_logs(username, projeto);
CREATE INDEX idx_intent_validator_category ON intent_validator_logs(intent_category);
CREATE INDEX idx_intent_validator_valid ON intent_validator_logs(intent_valid);
CREATE INDEX idx_intent_validator_execution_sequence ON intent_validator_logs(execution_sequence);

-- =====================================================
-- MÓDULO 1.5: PLAN BUILDER AGENT (NÓ DE PLANEJAMENTO)
-- =====================================================

CREATE TABLE IF NOT EXISTS plan_builder_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Rastreio de execução
    execution_sequence INTEGER,  -- Ordem de execução no fluxo
    parent_intent_validator_id UUID REFERENCES intent_validator_logs(id),  -- FK para intent_validator
    
    -- Identificação (sempre presente)
    username VARCHAR(100) NOT NULL,
    projeto VARCHAR(100) NOT NULL,
    horario TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Input
    pergunta TEXT NOT NULL,
    intent_category VARCHAR(100),
    
    -- Plano gerado
    plan TEXT,
    plan_steps TEXT[],
    estimated_complexity VARCHAR(20),
    
    -- Análise
    data_sources TEXT[],
    output_format VARCHAR(50),
    
    -- Performance
    execution_time REAL,
    model_used VARCHAR(50),
    tokens_used INTEGER,
    
    -- Status
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    -- Metadata adicional
    metadata JSONB
);

CREATE INDEX idx_plan_builder_username ON plan_builder_logs(username);
CREATE INDEX idx_plan_builder_projeto ON plan_builder_logs(projeto);
CREATE INDEX idx_plan_builder_horario ON plan_builder_logs(horario DESC);
CREATE INDEX idx_plan_builder_username_projeto ON plan_builder_logs(username, projeto);
CREATE INDEX idx_plan_builder_complexity ON plan_builder_logs(estimated_complexity);
CREATE INDEX idx_plan_builder_parent_intent ON plan_builder_logs(parent_intent_validator_id);
CREATE INDEX idx_plan_builder_execution_sequence ON plan_builder_logs(execution_sequence);

-- =====================================================
-- MÓDULO 1.6: PLAN CONFIRM AGENT (NÓ DE CONFIRMAÇÃO)
-- =====================================================

CREATE TABLE IF NOT EXISTS plan_confirm_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Rastreio de execução
    execution_sequence INTEGER,  -- Ordem de execução no fluxo
    parent_plan_builder_id UUID REFERENCES plan_builder_logs(id),  -- FK para plan_builder
    parent_intent_validator_id UUID REFERENCES intent_validator_logs(id),  -- FK para intent_validator
    
    -- Identificação (sempre presente)
    username VARCHAR(100) NOT NULL,
    projeto VARCHAR(100) NOT NULL,
    horario TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Input
    pergunta TEXT NOT NULL,
    plan TEXT,
    plan_steps TEXT[],
    estimated_complexity VARCHAR(20),
    
    -- Confirmação
    confirmed BOOLEAN,
    confirmation_method VARCHAR(50),  -- 'interactive', 'timeout', 'auto'
    confirmation_time TIMESTAMP,
    user_feedback TEXT,
    plan_accepted BOOLEAN,
    
    -- Performance
    execution_time REAL,
    
    -- Status
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    -- Metadata adicional
    metadata JSONB
);

CREATE INDEX idx_plan_confirm_username ON plan_confirm_logs(username);
CREATE INDEX idx_plan_confirm_projeto ON plan_confirm_logs(projeto);
CREATE INDEX idx_plan_confirm_horario ON plan_confirm_logs(horario DESC);
CREATE INDEX idx_plan_confirm_username_projeto ON plan_confirm_logs(username, projeto);
CREATE INDEX idx_plan_confirm_confirmed ON plan_confirm_logs(confirmed);
CREATE INDEX idx_plan_confirm_method ON plan_confirm_logs(confirmation_method);
CREATE INDEX idx_plan_confirm_parent_plan ON plan_confirm_logs(parent_plan_builder_id);
CREATE INDEX idx_plan_confirm_parent_intent ON plan_confirm_logs(parent_intent_validator_id);
CREATE INDEX idx_plan_confirm_execution_sequence ON plan_confirm_logs(execution_sequence);

-- =====================================================
-- MÓDULO 1.7: USER PROPOSED PLAN AGENT (NÓ DE SUGESTÃO DO USUÁRIO)
-- =====================================================

CREATE TABLE IF NOT EXISTS user_proposed_plan_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Rastreio de execução
    execution_sequence INTEGER,  -- Ordem de execução no fluxo
    parent_plan_confirm_id UUID REFERENCES plan_confirm_logs(id),  -- FK para plan_confirm
    parent_plan_builder_id UUID REFERENCES plan_builder_logs(id),  -- FK para plan_builder
    parent_intent_validator_id UUID REFERENCES intent_validator_logs(id),  -- FK para intent_validator
    
    -- Identificação (sempre presente)
    username VARCHAR(100) NOT NULL,
    projeto VARCHAR(100) NOT NULL,
    horario TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Input
    pergunta TEXT NOT NULL,
    rejected_plan TEXT,  -- O plano que foi rejeitado
    
    -- Sugestão do usuário
    user_proposed_plan TEXT,
    plan_received BOOLEAN,
    received_at TIMESTAMP,
    input_method VARCHAR(50),  -- 'interactive', 'api', 'timeout'
    
    -- Contexto
    input_length INTEGER,
    is_refinement BOOLEAN DEFAULT FALSE,  -- Se é refinamento do plano anterior
    iteration_count INTEGER DEFAULT 1,  -- Número de iterações (rejeições)
    
    -- Performance
    execution_time REAL,
    wait_time REAL,  -- Tempo esperando resposta do usuário
    
    -- Status
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    -- Metadata adicional
    metadata JSONB
);

CREATE INDEX idx_user_proposed_plan_username ON user_proposed_plan_logs(username);
CREATE INDEX idx_user_proposed_plan_projeto ON user_proposed_plan_logs(projeto);
CREATE INDEX idx_user_proposed_plan_horario ON user_proposed_plan_logs(horario DESC);
CREATE INDEX idx_user_proposed_plan_username_projeto ON user_proposed_plan_logs(username, projeto);
CREATE INDEX idx_user_proposed_plan_received ON user_proposed_plan_logs(plan_received);
CREATE INDEX idx_user_proposed_plan_parent_confirm ON user_proposed_plan_logs(parent_plan_confirm_id);
CREATE INDEX idx_user_proposed_plan_parent_plan ON user_proposed_plan_logs(parent_plan_builder_id);
CREATE INDEX idx_user_proposed_plan_parent_intent ON user_proposed_plan_logs(parent_intent_validator_id);
CREATE INDEX idx_user_proposed_plan_execution_sequence ON user_proposed_plan_logs(execution_sequence);
CREATE INDEX idx_user_proposed_plan_iteration ON user_proposed_plan_logs(iteration_count);

-- =====================================================
-- MÓDULO 1.7: PLAN REFINER AGENT
-- =====================================================
CREATE TABLE IF NOT EXISTS plan_refiner_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identificação (sempre presente)
    username VARCHAR(100) NOT NULL,
    projeto VARCHAR(100) NOT NULL,
    horario TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Input do refinamento
    pergunta TEXT NOT NULL,
    original_plan TEXT NOT NULL,
    user_suggestion TEXT NOT NULL,
    intent_category VARCHAR(50),
    
    -- Output do refinamento
    refined_plan TEXT,
    refinement_summary TEXT,
    changes_applied JSONB,  -- Array de mudanças aplicadas
    user_suggestions_incorporated JSONB,  -- Array de sugestões incorporadas
    improvements_made JSONB,  -- Array de melhorias feitas
    validation_notes JSONB,  -- Array de notas de validação
    
    -- Parent IDs (para rastreabilidade)
    parent_intent_validator_id UUID,
    parent_plan_builder_id UUID,
    parent_user_proposed_plan_id UUID,
    
    -- Configuração do modelo
    model_used VARCHAR(50),
    temperature REAL,
    
    -- Métricas
    original_plan_length INTEGER,
    refined_plan_length INTEGER,
    num_changes_applied INTEGER,
    num_suggestions_incorporated INTEGER,
    execution_time REAL,
    
    -- Status
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    -- Metadata adicional
    metadata JSONB,
    
    -- Foreign Keys
    FOREIGN KEY (parent_intent_validator_id) REFERENCES intent_validator_logs(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_plan_builder_id) REFERENCES plan_builder_logs(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_user_proposed_plan_id) REFERENCES user_proposed_plan_logs(id) ON DELETE SET NULL
);

-- Índices para plan_refiner_logs
CREATE INDEX idx_plan_refiner_username ON plan_refiner_logs(username);
CREATE INDEX idx_plan_refiner_projeto ON plan_refiner_logs(projeto);
CREATE INDEX idx_plan_refiner_horario ON plan_refiner_logs(horario DESC);
CREATE INDEX idx_plan_refiner_intent_category ON plan_refiner_logs(intent_category);
CREATE INDEX idx_plan_refiner_parent_intent_validator ON plan_refiner_logs(parent_intent_validator_id);
CREATE INDEX idx_plan_refiner_parent_plan_builder ON plan_refiner_logs(parent_plan_builder_id);
CREATE INDEX idx_plan_refiner_parent_user_proposed ON plan_refiner_logs(parent_user_proposed_plan_id);
CREATE INDEX idx_plan_refiner_success ON plan_refiner_logs(success);

-- =====================================================
-- MÓDULO 1.8: ANALYSIS ORCHESTRATOR AGENT (MOTOR DE GERAÇÃO DE QUERIES)
-- =====================================================

CREATE TABLE IF NOT EXISTS analysis_orchestrator_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Rastreio de execução
    execution_sequence INTEGER,  -- Ordem de execução no fluxo
    parent_plan_confirm_id UUID REFERENCES plan_confirm_logs(id),  -- FK para plan_confirm
    parent_plan_builder_id UUID REFERENCES plan_builder_logs(id),  -- FK para plan_builder
    parent_intent_validator_id UUID REFERENCES intent_validator_logs(id),  -- FK para intent_validator
    parent_user_proposed_plan_id UUID REFERENCES user_proposed_plan_logs(id),  -- FK para user_proposed_plan (se houver)
    parent_plan_refiner_id UUID REFERENCES plan_refiner_logs(id),  -- FK para plan_refiner (se houver)
    
    -- Identificação (sempre presente)
    username VARCHAR(100) NOT NULL,
    projeto VARCHAR(100) NOT NULL,
    horario TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Input
    pergunta TEXT NOT NULL,
    plan TEXT,  -- Plano recebido do PlanBuilder
    intent_category VARCHAR(100),
    plan_confirmed BOOLEAN,  -- Se o plano foi confirmado pelo usuário
    
    -- Query SQL Gerada
    query_sql TEXT,
    query_explanation TEXT,
    columns_used TEXT[],  -- Colunas utilizadas na query
    filters_applied TEXT[],  -- Filtros aplicados
    
    -- Validação de Segurança
    security_validated BOOLEAN DEFAULT FALSE,
    security_violations TEXT[],  -- Violações de segurança detectadas
    forbidden_columns_detected TEXT[],  -- Colunas sensíveis detectadas
    forbidden_operations_detected TEXT[],  -- Operações proibidas detectadas
    
    -- Otimização
    optimization_notes TEXT,
    query_complexity VARCHAR(20),  -- 'baixa', 'média', 'alta'
    has_aggregation BOOLEAN DEFAULT FALSE,
    
    -- Performance
    execution_time REAL,
    model_used VARCHAR(50),
    
    -- Status
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    error_type VARCHAR(50),  -- 'security', 'syntax', 'semantic', 'timeout', 'api_error'
    
    -- Metadata adicional
    metadata JSONB
);

CREATE INDEX idx_analysis_orchestrator_username ON analysis_orchestrator_logs(username);
CREATE INDEX idx_analysis_orchestrator_projeto ON analysis_orchestrator_logs(projeto);
CREATE INDEX idx_analysis_orchestrator_horario ON analysis_orchestrator_logs(horario DESC);
CREATE INDEX idx_analysis_orchestrator_username_projeto ON analysis_orchestrator_logs(username, projeto);
CREATE INDEX idx_analysis_orchestrator_security ON analysis_orchestrator_logs(security_validated);
CREATE INDEX idx_analysis_orchestrator_success ON analysis_orchestrator_logs(success);
CREATE INDEX idx_analysis_orchestrator_complexity ON analysis_orchestrator_logs(query_complexity);
CREATE INDEX idx_analysis_orchestrator_parent_confirm ON analysis_orchestrator_logs(parent_plan_confirm_id);
CREATE INDEX idx_analysis_orchestrator_parent_plan ON analysis_orchestrator_logs(parent_plan_builder_id);
CREATE INDEX idx_analysis_orchestrator_parent_intent ON analysis_orchestrator_logs(parent_intent_validator_id);
CREATE INDEX idx_analysis_orchestrator_parent_user_proposed ON analysis_orchestrator_logs(parent_user_proposed_plan_id);
CREATE INDEX idx_analysis_orchestrator_parent_refiner ON analysis_orchestrator_logs(parent_plan_refiner_id);
CREATE INDEX idx_analysis_orchestrator_execution_sequence ON analysis_orchestrator_logs(execution_sequence);
CREATE INDEX idx_analysis_orchestrator_category ON analysis_orchestrator_logs(intent_category);

-- =====================================================
-- MÓDULO 1.8: SQL VALIDATOR AGENT (NÓ DE VALIDAÇÃO)
-- =====================================================

CREATE TABLE IF NOT EXISTS sql_validator_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Rastreio de execução
    execution_sequence INTEGER,  -- Ordem de execução no fluxo
    parent_analysis_orchestrator_id UUID REFERENCES analysis_orchestrator_logs(id),  -- FK para analysis_orchestrator
    parent_plan_confirm_id UUID REFERENCES plan_confirm_logs(id),  -- FK para plan_confirm
    parent_plan_builder_id UUID REFERENCES plan_builder_logs(id),  -- FK para plan_builder
    parent_intent_validator_id UUID REFERENCES intent_validator_logs(id),  -- FK para intent_validator
    
    -- Identificação (sempre presente)
    username VARCHAR(100) NOT NULL,
    projeto VARCHAR(100) NOT NULL,
    horario TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Input
    pergunta TEXT NOT NULL,
    query_sql TEXT NOT NULL,  -- Query SQL a ser validada
    
    -- Resultado da Validação
    valid BOOLEAN NOT NULL,  -- Se a query passou na validação
    syntax_valid BOOLEAN,  -- Sintaxe SQL correta
    athena_compatible BOOLEAN,  -- Compatível com AWS Athena (Presto)
    
    -- Problemas Encontrados
    security_issues JSONB,  -- Lista de problemas de segurança
    warnings JSONB,  -- Lista de avisos
    optimization_suggestions JSONB,  -- Sugestões de otimização
    
    -- Estimativas AWS Athena
    estimated_scan_size_gb NUMERIC(10,2),  -- Tamanho estimado de scan em GB
    estimated_cost_usd NUMERIC(10,6),  -- Custo estimado em USD ($5/TB)
    estimated_execution_time_seconds NUMERIC(10,2),  -- Tempo estimado de execução
    
    -- Análise de Risco
    risk_level VARCHAR(50),  -- 'low', 'medium', 'high'
    
    -- Performance da Validação
    execution_time REAL,  -- Tempo de execução do agente
    model_used VARCHAR(50),  -- Modelo usado (gpt-4o)
    tokens_used INTEGER,  -- Tokens consumidos
    
    -- Status
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    -- Metadata adicional
    metadata JSONB
);

CREATE INDEX idx_sql_validator_username ON sql_validator_logs(username);
CREATE INDEX idx_sql_validator_projeto ON sql_validator_logs(projeto);
CREATE INDEX idx_sql_validator_horario ON sql_validator_logs(horario DESC);
CREATE INDEX idx_sql_validator_username_projeto ON sql_validator_logs(username, projeto);
CREATE INDEX idx_sql_validator_valid ON sql_validator_logs(valid);
CREATE INDEX idx_sql_validator_risk_level ON sql_validator_logs(risk_level);
CREATE INDEX idx_sql_validator_cost ON sql_validator_logs(estimated_cost_usd);
CREATE INDEX idx_sql_validator_parent_analysis ON sql_validator_logs(parent_analysis_orchestrator_id);
CREATE INDEX idx_sql_validator_parent_confirm ON sql_validator_logs(parent_plan_confirm_id);
CREATE INDEX idx_sql_validator_parent_builder ON sql_validator_logs(parent_plan_builder_id);
CREATE INDEX idx_sql_validator_parent_intent ON sql_validator_logs(parent_intent_validator_id);
CREATE INDEX idx_sql_validator_execution_sequence ON sql_validator_logs(execution_sequence);

-- =====================================================
-- MÓDULO 2: HISTORY PREFERENCES AGENT (NÓ 1)
-- =====================================================
-- COMENTADO: Tabela não utilizada no momento
/*
CREATE TABLE IF NOT EXISTS history_preferences_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identificação (sempre presente)
    username VARCHAR(100) NOT NULL,
    projeto VARCHAR(100) NOT NULL,
    horario TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Dados recuperados
    user_preferences JSONB,
    user_patterns JSONB,
    interaction_count INTEGER,
    last_interactions TEXT[],
    
    -- Contexto identificado
    context_summary TEXT,
    relevant_history_found BOOLEAN DEFAULT FALSE,
    
    -- Performance
    execution_time REAL,
    records_retrieved INTEGER,
    
    -- Status
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    -- Metadata adicional
    metadata JSONB
);

CREATE INDEX idx_history_preferences_username ON history_preferences_logs(username);
CREATE INDEX idx_history_preferences_projeto ON history_preferences_logs(projeto);
CREATE INDEX idx_history_preferences_horario ON history_preferences_logs(horario DESC);
CREATE INDEX idx_history_preferences_username_projeto ON history_preferences_logs(username, projeto);
*/

-- =====================================================
-- MÓDULO 3: ROUTER AGENT (NÓ 2)
-- =====================================================
-- COMENTADO: Tabela não utilizada no momento
/*
CREATE TABLE IF NOT EXISTS router_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identificação (sempre presente)
    username VARCHAR(100) NOT NULL,
    projeto VARCHAR(100) NOT NULL,
    horario TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Decisão de roteamento
    route VARCHAR(100) NOT NULL,
    route_reason TEXT,
    confidence_score REAL,
    
    -- Análise da pergunta
    query_type VARCHAR(50),
    requires_aggregation BOOLEAN,
    requires_join BOOLEAN,
    complexity_level VARCHAR(20),
    
    -- Performance
    execution_time REAL,
    model_used VARCHAR(50),
    
    -- Status
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    -- Metadata adicional
    metadata JSONB
);

CREATE INDEX idx_router_username ON router_logs(username);
CREATE INDEX idx_router_projeto ON router_logs(projeto);
CREATE INDEX idx_router_horario ON router_logs(horario DESC);
CREATE INDEX idx_router_username_projeto ON router_logs(username, projeto);
CREATE INDEX idx_router_route ON router_logs(route);
*/

-- =====================================================
-- MÓDULO 4: GENERATOR AGENT (NÓ 3)
-- =====================================================
-- COMENTADO: Tabela não utilizada no momento
/*
CREATE TABLE IF NOT EXISTS generator_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identificação (sempre presente)
    username VARCHAR(100) NOT NULL,
    projeto VARCHAR(100) NOT NULL,
    horario TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- SQL Gerado
    sql_query TEXT NOT NULL,
    query_type VARCHAR(50),
    tables_used TEXT[],
    
    -- Validação
    query_valid BOOLEAN DEFAULT TRUE,
    validation_errors TEXT[],
    
    -- Execução
    query_executed BOOLEAN DEFAULT FALSE,
    rows_returned INTEGER,
    execution_error TEXT,
    
    -- Performance
    execution_time REAL,
    query_execution_time REAL,
    model_used VARCHAR(50),
    tokens_used INTEGER,
    
    -- Status
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    -- Metadata adicional
    metadata JSONB
);

CREATE INDEX idx_generator_username ON generator_logs(username);
CREATE INDEX idx_generator_projeto ON generator_logs(projeto);
CREATE INDEX idx_generator_horario ON generator_logs(horario DESC);
CREATE INDEX idx_generator_username_projeto ON generator_logs(username, projeto);
CREATE INDEX idx_generator_query_type ON generator_logs(query_type);
*/

-- =====================================================
-- MÓDULO 5: RESPONDER AGENT (NÓ 4)
-- =====================================================
-- COMENTADO: Tabela não utilizada no momento
/*
CREATE TABLE IF NOT EXISTS responder_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identificação (sempre presente)
    username VARCHAR(100) NOT NULL,
    projeto VARCHAR(100) NOT NULL,
    horario TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Resposta gerada
    resposta TEXT NOT NULL,
    resposta_format VARCHAR(50),
    
    -- Dados utilizados
    data_rows_processed INTEGER,
    charts_generated INTEGER,
    
    -- Qualidade
    response_complete BOOLEAN DEFAULT TRUE,
    user_satisfaction_score REAL,
    
    -- Performance
    execution_time REAL,
    model_used VARCHAR(50),
    tokens_used INTEGER,
    
    -- Status
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    
    -- Metadata adicional
    metadata JSONB
);

CREATE INDEX idx_responder_username ON responder_logs(username);
CREATE INDEX idx_responder_projeto ON responder_logs(projeto);
CREATE INDEX idx_responder_horario ON responder_logs(horario DESC);
CREATE INDEX idx_responder_username_projeto ON responder_logs(username, projeto);
CREATE INDEX idx_responder_format ON responder_logs(resposta_format);
*/

-- =====================================================
-- FOREIGN KEYS: Conectando rotina_usuario com módulos
-- =====================================================

ALTER TABLE rotina_usuario 
    ADD CONSTRAINT fk_rotina_intent_validator 
    FOREIGN KEY (intent_validator_id) 
    REFERENCES intent_validator_logs(id) ON DELETE SET NULL;

ALTER TABLE rotina_usuario 
    ADD CONSTRAINT fk_rotina_history_preferences 
    FOREIGN KEY (history_preferences_id) 
    REFERENCES history_preferences_logs(id) ON DELETE SET NULL;

ALTER TABLE rotina_usuario 
    ADD CONSTRAINT fk_rotina_router 
    FOREIGN KEY (router_id) 
    REFERENCES router_logs(id) ON DELETE SET NULL;

ALTER TABLE rotina_usuario 
    ADD CONSTRAINT fk_rotina_generator 
    FOREIGN KEY (generator_id) 
    REFERENCES generator_logs(id) ON DELETE SET NULL;

ALTER TABLE rotina_usuario 
    ADD CONSTRAINT fk_rotina_responder 
    FOREIGN KEY (responder_id) 
    REFERENCES responder_logs(id) ON DELETE SET NULL;

-- =====================================================
-- VIEWS ÚTEIS PARA NAVEGAÇÃO
-- =====================================================

-- View: Rotina completa do usuário com todos os detalhes
CREATE OR REPLACE VIEW vw_rotina_completa AS
SELECT 
    r.id,
    r.username,
    r.projeto,
    r.horario,
    r.modulo,
    r.pergunta,
    r.resposta_resumo,
    r.execution_time,
    r.success,
    
    -- Campos do Intent Validator
    iv.intent_valid,
    iv.intent_category,
    iv.security_violation,
    
    -- Campos do History
    hp.interaction_count,
    hp.relevant_history_found,
    
    -- Campos do Router
    rt.route,
    rt.confidence_score,
    
    -- Campos do Generator
    gn.sql_query,
    gn.rows_returned,
    
    -- Campos do Responder
    rp.resposta AS resposta_completa,
    rp.charts_generated

FROM rotina_usuario r
LEFT JOIN intent_validator_logs iv ON r.intent_validator_id = iv.id
LEFT JOIN history_preferences_logs hp ON r.history_preferences_id = hp.id
LEFT JOIN router_logs rt ON r.router_id = rt.id
LEFT JOIN generator_logs gn ON r.generator_id = gn.id
LEFT JOIN responder_logs rp ON r.responder_id = rp.id
ORDER BY r.horario DESC;

-- View: Timeline do usuário por projeto
CREATE OR REPLACE VIEW vw_timeline_usuario AS
SELECT 
    username,
    projeto,
    DATE(horario) as data,
    COUNT(*) as total_interacoes,
    COUNT(DISTINCT modulo) as modulos_diferentes,
    STRING_AGG(DISTINCT modulo, ', ') as modulos_usados,
    AVG(execution_time) as tempo_medio,
    COUNT(CASE WHEN success = TRUE THEN 1 END) as sucessos,
    COUNT(CASE WHEN success = FALSE THEN 1 END) as falhas
FROM rotina_usuario
GROUP BY username, projeto, DATE(horario)
ORDER BY username, projeto, data DESC;

-- View: Últimas 50 atividades por usuário/projeto
CREATE OR REPLACE VIEW vw_ultimas_atividades AS
SELECT 
    username,
    projeto,
    horario,
    modulo,
    pergunta,
    CASE 
        WHEN LENGTH(resposta_resumo) > 100 
        THEN SUBSTRING(resposta_resumo, 1, 100) || '...'
        ELSE resposta_resumo
    END as resposta_preview,
    execution_time,
    success
FROM rotina_usuario
ORDER BY horario DESC
LIMIT 50;

-- View: Estatísticas por módulo
CREATE OR REPLACE VIEW vw_stats_por_modulo AS
SELECT 
    projeto,
    modulo,
    COUNT(*) as total_execucoes,
    AVG(execution_time) as tempo_medio,
    COUNT(CASE WHEN success = TRUE THEN 1 END) as sucessos,
    COUNT(CASE WHEN success = FALSE THEN 1 END) as falhas,
    MIN(horario) as primeira_execucao,
    MAX(horario) as ultima_execucao
FROM rotina_usuario
GROUP BY projeto, modulo
ORDER BY projeto, total_execucoes DESC;

-- =====================================================
-- FUNÇÕES ÚTEIS
-- =====================================================

-- Função: Buscar rotina completa de um usuário em período
CREATE OR REPLACE FUNCTION get_rotina_periodo(
    p_username VARCHAR(100),
    p_projeto VARCHAR(100),
    p_data_inicio TIMESTAMP,
    p_data_fim TIMESTAMP
) RETURNS TABLE (
    horario TIMESTAMP,
    modulo VARCHAR(50),
    pergunta TEXT,
    resposta TEXT,
    tempo REAL,
    sucesso BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.horario,
        r.modulo,
        r.pergunta,
        r.resposta_resumo,
        r.execution_time,
        r.success
    FROM rotina_usuario r
    WHERE r.username = p_username
      AND r.projeto = p_projeto
      AND r.horario BETWEEN p_data_inicio AND p_data_fim
    ORDER BY r.horario ASC;
END;
$$ LANGUAGE plpgsql;

-- Função: Buscar detalhes completos de uma interação
CREATE OR REPLACE FUNCTION get_detalhes_interacao(
    p_rotina_id UUID
) RETURNS TABLE (
    modulo VARCHAR(50),
    detalhes JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.modulo,
        CASE r.modulo
            WHEN 'intent_validator' THEN row_to_json(iv.*)::JSONB
            WHEN 'history_preferences' THEN row_to_json(hp.*)::JSONB
            WHEN 'router' THEN row_to_json(rt.*)::JSONB
            WHEN 'generator' THEN row_to_json(gn.*)::JSONB
            WHEN 'responder' THEN row_to_json(rp.*)::JSONB
            ELSE '{}'::JSONB
        END as detalhes
    FROM rotina_usuario r
    LEFT JOIN intent_validator_logs iv ON r.intent_validator_id = iv.id
    LEFT JOIN history_preferences_logs hp ON r.history_preferences_id = hp.id
    LEFT JOIN router_logs rt ON r.router_id = rt.id
    LEFT JOIN generator_logs gn ON r.generator_id = gn.id
    LEFT JOIN responder_logs rp ON r.responder_id = rp.id
    WHERE r.id = p_rotina_id;
END;
$$ LANGUAGE plpgsql;

-- Função: Obter estatísticas do usuário
CREATE OR REPLACE FUNCTION get_user_stats(
    p_username VARCHAR(100),
    p_projeto VARCHAR(100)
) RETURNS TABLE (
    total_interacoes BIGINT,
    tempo_total REAL,
    tempo_medio REAL,
    modulo_mais_usado VARCHAR(50),
    taxa_sucesso REAL,
    primeira_interacao TIMESTAMP,
    ultima_interacao TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT,
        SUM(r.execution_time)::REAL,
        AVG(r.execution_time)::REAL,
        (SELECT modulo FROM rotina_usuario 
         WHERE username = p_username AND projeto = p_projeto 
         GROUP BY modulo ORDER BY COUNT(*) DESC LIMIT 1)::VARCHAR(50),
        (COUNT(CASE WHEN r.success = TRUE THEN 1 END)::REAL / COUNT(*)::REAL * 100)::REAL,
        MIN(r.horario),
        MAX(r.horario)
    FROM rotina_usuario r
    WHERE r.username = p_username
      AND r.projeto = p_projeto;
END;
$$ LANGUAGE plpgsql;


-- =====================================================
-- COMENTÁRIOS NAS TABELAS
-- =====================================================

COMMENT ON TABLE rotina_usuario IS 'TABELA CENTRAL - Permite navegar por toda a rotina do usuário através de horário, username e projeto';
COMMENT ON TABLE intent_validator_logs IS 'MÓDULO 1 - Intent Validator Agent (NÓ 0) - Validação de intenções';
COMMENT ON TABLE history_preferences_logs IS 'MÓDULO 2 - History Preferences Agent (NÓ 1) - Context Manager/Memory';
COMMENT ON TABLE router_logs IS 'MÓDULO 3 - Router Agent (NÓ 2) - Roteamento de queries';
COMMENT ON TABLE generator_logs IS 'MÓDULO 4 - Generator Agent (NÓ 3) - Geração de SQL';
COMMENT ON TABLE responder_logs IS 'MÓDULO 5 - Responder Agent (NÓ 4) - Geração de respostas';

COMMENT ON COLUMN rotina_usuario.horario IS 'TIMESTAMP SEMPRE PRESENTE - Permite ordenação temporal';
COMMENT ON COLUMN rotina_usuario.username IS 'CHAVE DE NAVEGAÇÃO - Identifica o usuário';
COMMENT ON COLUMN rotina_usuario.projeto IS 'CHAVE DE NAVEGAÇÃO - Identifica o projeto';
COMMENT ON COLUMN rotina_usuario.modulo IS 'CHAVE DE NAVEGAÇÃO - Identifica qual módulo foi executado';
COMMENT ON COLUMN rotina_usuario.intent_validator_id IS 'FK para intent_validator_logs - Permite navegar para detalhes';
COMMENT ON COLUMN rotina_usuario.history_preferences_id IS 'FK para history_preferences_logs - Permite navegar para detalhes';
COMMENT ON COLUMN rotina_usuario.router_id IS 'FK para router_logs - Permite navegar para detalhes';
COMMENT ON COLUMN rotina_usuario.generator_id IS 'FK para generator_logs - Permite navegar para detalhes';
COMMENT ON COLUMN rotina_usuario.responder_id IS 'FK para responder_logs - Permite navegar para detalhes';

-- =====================================================
-- EXEMPLOS DE USO
-- =====================================================

-- Exemplo 1: Ver toda a rotina de um usuário no projeto ezpag
-- SELECT * FROM rotina_usuario WHERE username = 'joao' AND projeto = 'ezpag' ORDER BY horario DESC;

-- Exemplo 2: Ver horários e módulos acionados nas últimas 24 horas
-- SELECT horario, modulo, pergunta FROM rotina_usuario 
-- WHERE username = 'joao' AND projeto = 'ezpag' 
-- AND horario >= NOW() - INTERVAL '24 hours' 
-- ORDER BY horario DESC;

-- Exemplo 3: Navegar da rotina para detalhes do intent_validator
-- SELECT r.horario, r.pergunta, iv.* 
-- FROM rotina_usuario r
-- JOIN intent_validator_logs iv ON r.intent_validator_id = iv.id
-- WHERE r.username = 'joao' AND r.projeto = 'ezpag';

-- Exemplo 4: Ver rotina completa com todos os módulos (usando view)
-- SELECT * FROM vw_rotina_completa WHERE username = 'joao' AND projeto = 'ezpag' LIMIT 10;

-- Exemplo 5: Estatísticas do usuário (usando função)
-- SELECT * FROM get_user_stats('joao', 'ezpag');

-- Exemplo 6: Timeline diária do usuário
-- SELECT * FROM vw_timeline_usuario WHERE username = 'joao' AND projeto = 'ezpag';

-- =====================================================
-- FIM DO SCRIPT
-- =====================================================
