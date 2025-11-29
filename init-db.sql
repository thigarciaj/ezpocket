-- =====================================================
-- EZPOCKET LOGS DATABASE - PostgreSQL
-- Estrutura modular navegável por timestamp
-- =====================================================

-- Criar banco de dados do Keycloak (se não existir)
SELECT 'CREATE DATABASE keycloak_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'keycloak_db')\gexec

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
    parent_user_proposed_plan_id UUID REFERENCES user_proposed_plan_logs(id),
    parent_plan_confirm_id UUID REFERENCES plan_confirm_logs(id),
    parent_plan_builder_id UUID REFERENCES plan_builder_logs(id),
    parent_intent_validator_id UUID REFERENCES intent_validator_logs(id),
    
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
-- MÓDULO 1.9: AUTO CORRECTION AGENT (NÓ DE CORREÇÃO)
-- =====================================================

CREATE TABLE IF NOT EXISTS auto_correction_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Rastreio de execução
    execution_sequence INTEGER,  -- Ordem de execução no fluxo (7)
    parent_sql_validator_id UUID REFERENCES sql_validator_logs(id),  -- FK para sql_validator
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
    query_original TEXT NOT NULL,  -- Query SQL original (inválida)
    validation_issues JSONB,  -- Problemas encontrados pelo SQL Validator
    
    -- Resultado da Correção
    success BOOLEAN NOT NULL,  -- Se conseguiu corrigir a query
    query_corrected TEXT,  -- Query SQL corrigida
    corrections_applied JSONB,  -- Lista de correções aplicadas
    corrections_count INTEGER,  -- Número de correções
    
    -- Explicação
    correction_explanation TEXT,  -- Explicação detalhada das mudanças
    changes_summary TEXT,  -- Resumo das mudanças
    confidence REAL,  -- Confiança na correção (0.0-1.0)
    
    -- Performance da Correção
    execution_time REAL,  -- Tempo de execução do agente
    model_used VARCHAR(50),  -- Modelo usado (gpt-4o)
    tokens_used INTEGER,  -- Tokens consumidos
    
    -- Status
    error_message TEXT,
    
    -- Metadata adicional
    metadata JSONB
);

CREATE INDEX idx_auto_correction_username ON auto_correction_logs(username);
CREATE INDEX idx_auto_correction_projeto ON auto_correction_logs(projeto);
CREATE INDEX idx_auto_correction_horario ON auto_correction_logs(horario DESC);
CREATE INDEX idx_auto_correction_username_projeto ON auto_correction_logs(username, projeto);
CREATE INDEX idx_auto_correction_success ON auto_correction_logs(success);
CREATE INDEX idx_auto_correction_corrections_count ON auto_correction_logs(corrections_count);
CREATE INDEX idx_auto_correction_parent_validator ON auto_correction_logs(parent_sql_validator_id);
CREATE INDEX idx_auto_correction_parent_analysis ON auto_correction_logs(parent_analysis_orchestrator_id);
CREATE INDEX idx_auto_correction_parent_confirm ON auto_correction_logs(parent_plan_confirm_id);
CREATE INDEX idx_auto_correction_parent_builder ON auto_correction_logs(parent_plan_builder_id);
CREATE INDEX idx_auto_correction_parent_intent ON auto_correction_logs(parent_intent_validator_id);
CREATE INDEX idx_auto_correction_execution_sequence ON auto_correction_logs(execution_sequence);

-- =====================================================
-- ATHENA EXECUTOR AGENT - Execução de Queries
-- =====================================================
-- Tabela para registrar execução de queries no AWS Athena
-- Execution Sequence: 8 (após sql_validator=6 ou auto_correction=7)
-- Chamado quando: Query validada (sql_validator) OU corrigida (auto_correction)

CREATE TABLE athena_executor_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_sequence INTEGER DEFAULT 8 NOT NULL,
    
    -- Foreign Keys (Parent Modules)
    parent_sql_validator_id UUID REFERENCES sql_validator_logs(id) ON DELETE CASCADE,
    parent_auto_correction_id UUID REFERENCES auto_correction_logs(id) ON DELETE CASCADE,
    parent_analysis_orchestrator_id UUID,
    parent_plan_confirm_id UUID,
    parent_plan_builder_id UUID,
    parent_intent_validator_id UUID,
    
    -- Query Execution
    query_executed TEXT NOT NULL,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Results
    row_count INTEGER DEFAULT 0,
    column_count INTEGER DEFAULT 0,
    columns JSONB, -- Array de nomes das colunas
    results_preview JSONB, -- Primeiras 100 linhas em formato JSON
    results_full JSONB, -- Todos os resultados completos
    results_message TEXT, -- Mensagem formatada com os resultados
    data_size_mb REAL DEFAULT 0,
    
    -- Athena Info
    database VARCHAR(255),
    region VARCHAR(50),
    
    -- Error Info (se houver)
    error TEXT,
    error_type VARCHAR(100),
    
    -- Performance Metrics
    execution_time_seconds REAL,
    
    -- Metadata
    username VARCHAR(255),
    projeto VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes para performance
CREATE INDEX idx_athena_executor_parent_validator ON athena_executor_logs(parent_sql_validator_id);
CREATE INDEX idx_athena_executor_parent_correction ON athena_executor_logs(parent_auto_correction_id);
CREATE INDEX idx_athena_executor_parent_analysis ON athena_executor_logs(parent_analysis_orchestrator_id);
CREATE INDEX idx_athena_executor_parent_confirm ON athena_executor_logs(parent_plan_confirm_id);
CREATE INDEX idx_athena_executor_parent_builder ON athena_executor_logs(parent_plan_builder_id);
CREATE INDEX idx_athena_executor_parent_intent ON athena_executor_logs(parent_intent_validator_id);
CREATE INDEX idx_athena_executor_success ON athena_executor_logs(success);
CREATE INDEX idx_athena_executor_username_projeto ON athena_executor_logs(username, projeto);
CREATE INDEX idx_athena_executor_created_at ON athena_executor_logs(created_at);
CREATE INDEX idx_athena_executor_execution_sequence ON athena_executor_logs(execution_sequence);

-- =====================================================
-- MÓDULO 8.5: PYTHON RUNTIME AGENT (ANÁLISE ESTATÍSTICA)
-- =====================================================
-- Tabela para registrar análises estatísticas dos resultados
-- Execution Sequence: 9 (após athena_executor=8)
-- Chamado quando: Query executada e resultados precisam de análise

CREATE TABLE IF NOT EXISTS python_runtime_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_sequence INTEGER DEFAULT 9 NOT NULL,
    
    -- Foreign Keys (Parent Modules)
    parent_athena_executor_id UUID REFERENCES athena_executor_logs(id) ON DELETE CASCADE,
    parent_auto_correction_id UUID REFERENCES auto_correction_logs(id) ON DELETE CASCADE,
    parent_sql_validator_id UUID REFERENCES sql_validator_logs(id) ON DELETE CASCADE,
    parent_analysis_orchestrator_id UUID,
    parent_plan_confirm_id UUID,
    parent_plan_builder_id UUID,
    parent_intent_validator_id UUID,
    
    -- Identificação
    username VARCHAR(100) NOT NULL,
    projeto VARCHAR(100) NOT NULL,
    horario TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    pergunta TEXT NOT NULL,
    
    -- Análise Estatística
    success BOOLEAN NOT NULL DEFAULT FALSE,
    has_analysis BOOLEAN DEFAULT FALSE,
    analysis_summary TEXT,
    statistics JSONB, -- {total, media, mediana, desvio_padrao, minimo, maximo}
    insights JSONB, -- Array de insights gerados
    
    -- Performance
    execution_time REAL,
    
    -- Error Info
    error TEXT,
    
    -- Metadata adicional (código Python, visualizações sugeridas, etc)
    metadata JSONB
);

-- Indexes para performance
CREATE INDEX idx_python_runtime_parent_athena ON python_runtime_logs(parent_athena_executor_id);
CREATE INDEX idx_python_runtime_parent_correction ON python_runtime_logs(parent_auto_correction_id);
CREATE INDEX idx_python_runtime_parent_validator ON python_runtime_logs(parent_sql_validator_id);
CREATE INDEX idx_python_runtime_parent_analysis ON python_runtime_logs(parent_analysis_orchestrator_id);
CREATE INDEX idx_python_runtime_username_projeto ON python_runtime_logs(username, projeto);
CREATE INDEX idx_python_runtime_horario ON python_runtime_logs(horario DESC);
CREATE INDEX idx_python_runtime_execution_sequence ON python_runtime_logs(execution_sequence);

-- =====================================================
-- RESPONSE COMPOSER AGENT (NÓ 10) - Formatação de Respostas
-- =====================================================
CREATE TABLE IF NOT EXISTS response_composer_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_sequence INTEGER DEFAULT 10 NOT NULL,
    
    -- Foreign Keys (Parent Modules)
    parent_python_runtime_id UUID REFERENCES python_runtime_logs(id) ON DELETE CASCADE,
    parent_athena_executor_id UUID REFERENCES athena_executor_logs(id) ON DELETE CASCADE,
    parent_auto_correction_id UUID REFERENCES auto_correction_logs(id) ON DELETE CASCADE,
    parent_sql_validator_id UUID REFERENCES sql_validator_logs(id) ON DELETE CASCADE,
    parent_analysis_orchestrator_id UUID,
    parent_plan_confirm_id UUID,
    parent_plan_builder_id UUID,
    parent_intent_validator_id UUID,
    
    -- Identificação
    username VARCHAR(100) NOT NULL,
    projeto VARCHAR(100) NOT NULL,
    horario TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    pergunta TEXT NOT NULL,
    
    -- Resposta Formatada
    success BOOLEAN NOT NULL DEFAULT FALSE,
    response_text TEXT,
    response_summary TEXT,
    key_numbers TEXT[],
    formatting_style VARCHAR(50),
    user_friendly_score REAL,
    
    -- Performance
    execution_time REAL,
    tokens_used INTEGER,
    model_used VARCHAR(50),
    
    -- Error Info
    error TEXT,
    
    -- Metadata adicional
    metadata JSONB
);

-- Indexes para performance
CREATE INDEX idx_response_composer_parent_python ON response_composer_logs(parent_python_runtime_id);
CREATE INDEX idx_response_composer_parent_athena ON response_composer_logs(parent_athena_executor_id);
CREATE INDEX idx_response_composer_username_projeto ON response_composer_logs(username, projeto);
CREATE INDEX idx_response_composer_horario ON response_composer_logs(horario DESC);
CREATE INDEX idx_response_composer_execution_sequence ON response_composer_logs(execution_sequence);

-- =====================================================
-- USER FEEDBACK AGENT (NÓ 11) - Avaliação do Usuário
-- =====================================================
CREATE TABLE IF NOT EXISTS user_feedback_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_sequence INTEGER DEFAULT 11 NOT NULL,
    
    -- Foreign Keys (Parent Modules)
    parent_response_composer_id UUID REFERENCES response_composer_logs(id) ON DELETE CASCADE,
    parent_python_runtime_id UUID REFERENCES python_runtime_logs(id) ON DELETE CASCADE,
    parent_athena_executor_id UUID REFERENCES athena_executor_logs(id) ON DELETE CASCADE,
    parent_auto_correction_id UUID REFERENCES auto_correction_logs(id) ON DELETE CASCADE,
    parent_sql_validator_id UUID REFERENCES sql_validator_logs(id) ON DELETE CASCADE,
    parent_analysis_orchestrator_id UUID,
    parent_plan_confirm_id UUID,
    parent_plan_builder_id UUID,
    parent_intent_validator_id UUID,
    
    -- Identificação
    username VARCHAR(100) NOT NULL,
    projeto VARCHAR(100) NOT NULL,
    horario TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    pergunta TEXT NOT NULL,
    
    -- Resposta avaliada
    response_text TEXT,  -- Resposta que foi apresentada ao usuário
    
    -- Avaliação do Usuário
    success BOOLEAN NOT NULL DEFAULT TRUE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),  -- 1-5 estrelas
    comment TEXT,  -- Comentário opcional
    is_helpful BOOLEAN,  -- Se a resposta foi útil
    response_quality VARCHAR(50),  -- poor/fair/good/very_good/excellent
    user_satisfaction VARCHAR(50),  -- unsatisfied/neutral/satisfied/very_satisfied
    would_recommend BOOLEAN,  -- Se recomendaria o sistema
    feedback_tags TEXT[],  -- Tags: accurate, fast, clear, incomplete, wrong, etc
    
    -- Análise do Feedback
    feedback_summary TEXT,
    positive_aspects TEXT[],  -- Aspectos positivos mencionados
    improvement_areas TEXT[],  -- Áreas que precisam melhorar
    sentiment VARCHAR(50),  -- very_positive/positive/neutral/negative/very_negative
    
    -- Performance
    execution_time REAL,
    feedback_date TIMESTAMP,
    
    -- Error Info
    error TEXT,
    
    -- Metadata adicional
    metadata JSONB
);

-- Indexes para performance
CREATE INDEX idx_user_feedback_parent_response ON user_feedback_logs(parent_response_composer_id);
CREATE INDEX idx_user_feedback_parent_python ON user_feedback_logs(parent_python_runtime_id);
CREATE INDEX idx_user_feedback_rating ON user_feedback_logs(rating);
CREATE INDEX idx_user_feedback_sentiment ON user_feedback_logs(sentiment);
CREATE INDEX idx_user_feedback_username_projeto ON user_feedback_logs(username, projeto);
CREATE INDEX idx_user_feedback_horario ON user_feedback_logs(horario DESC);
CREATE INDEX idx_user_feedback_execution_sequence ON user_feedback_logs(execution_sequence);


-- =====================================================
-- TABELA ORDER REPORT - Schema idêntico ao CSV
-- =====================================================

CREATE TABLE IF NOT EXISTS order_report (
    -- Tipos baseados no schema do Athena
    "Order Code" BIGINT NOT NULL,
    "Date Order Created" TEXT,
    "Status" TEXT,
    "Customer Name" TEXT,
    "Customer Email" TEXT,
    "Shipping Address" TEXT,
    "Zip Code" TEXT,
    "item_name" TEXT,
    "TAC Expected" DOUBLE PRECISION,
    "TAC Paid" DOUBLE PRECISION,
    "Downpayment Paid" DOUBLE PRECISION,
    "Taxes Percent" DOUBLE PRECISION,
    "Installments Value" DOUBLE PRECISION,
    "Taxes Value Installments" DOUBLE PRECISION,
    "Taxes Value Initial Payment" DOUBLE PRECISION,
    "Shipment Value" DOUBLE PRECISION,
    "Discount Value" DOUBLE PRECISION,
    "Total Installments" DOUBLE PRECISION,
    "Dealer" TEXT,
    "Sellers" TEXT,
    "Coupons" TEXT,
    "Delivery Date" TEXT,
    "Contract Start Date" TEXT,
    "Status Default" TEXT,
    "Customer Phone Number" TEXT,
    "Serial Number" TEXT,
    "IMEI 1" TEXT,
    "IMEI 2" TEXT,
    "Contract Total Value Expected" DOUBLE PRECISION,
    "Installments Paid Value" DOUBLE PRECISION,
    "Order Total Paid" DOUBLE PRECISION,
    "Remaining Total" DOUBLE PRECISION,
    "Total Delay" DOUBLE PRECISION,
    "Total Extra Payment Value Paid" DOUBLE PRECISION,
    "Total Value Refunded" DOUBLE PRECISION,
    "Early Purchase Value" DOUBLE PRECISION,
    "Early Purchase Date" TEXT,
    "customer_income" DOUBLE PRECISION,
    "Cancelled At" TEXT,
    "Finished At" TEXT,
    "PDD at" TEXT,
    
    -- Metadados e controle
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Chave primária composta
    PRIMARY KEY ("Order Code", "item_name")
);



-- =====================================================
-- TABELA DE CONTROLE DE SINCRONIZAÇÃO
-- =====================================================

CREATE TABLE IF NOT EXISTS data_sync_control (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Informações da sincronização
    sync_type VARCHAR(50) NOT NULL,  -- 'order_report', 'customers', etc.
    source_system VARCHAR(50) NOT NULL,  -- 'athena', 's3', etc.
    target_table VARCHAR(100) NOT NULL,
    
    -- Timestamps
    sync_started_at TIMESTAMP NOT NULL,
    sync_completed_at TIMESTAMP,
    
    -- Estatísticas
    records_processed INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    
    -- Status
    sync_status VARCHAR(20) DEFAULT 'running',  -- 'running', 'completed', 'failed', 'partial'
    
    -- Detalhes técnicos
    execution_time_seconds REAL,
    batch_size INTEGER,
    retry_count INTEGER DEFAULT 0,
    
    -- Logs e erros
    success_message TEXT,
    error_message TEXT,
    error_details JSONB,
    
    -- Metadados
    sync_config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_data_sync_control_type ON data_sync_control(sync_type);
CREATE INDEX idx_data_sync_control_status ON data_sync_control(sync_status);
CREATE INDEX idx_data_sync_control_started ON data_sync_control(sync_started_at DESC);
CREATE INDEX idx_data_sync_control_completed ON data_sync_control(sync_completed_at DESC);
CREATE INDEX idx_data_sync_control_target_table ON data_sync_control(target_table);


-- Comentários das tabelas
COMMENT ON TABLE intent_validator_logs IS 'Logs de validação de intenções';
COMMENT ON TABLE plan_builder_logs IS 'Logs de construção de planos';
COMMENT ON TABLE plan_confirm_logs IS 'Logs de confirmação de planos';  
COMMENT ON TABLE user_proposed_plan_logs IS 'Logs de planos propostos pelo usuário';
COMMENT ON TABLE plan_refiner_logs IS 'Logs de refinamento de planos';
COMMENT ON TABLE analysis_orchestrator_logs IS 'Logs de orquestração de análises';
COMMENT ON TABLE sql_validator_logs IS 'Logs de validação de SQL';
COMMENT ON TABLE auto_correction_logs IS 'Logs de correção automática';
COMMENT ON TABLE athena_executor_logs IS 'Logs de execução no Athena';
COMMENT ON TABLE python_runtime_logs IS 'Logs de runtime Python';
COMMENT ON TABLE response_composer_logs IS 'Logs de composição de respostas';
COMMENT ON TABLE user_feedback_logs IS 'Logs de feedback do usuário';
COMMENT ON TABLE order_report IS 'Relatório de pedidos';
COMMENT ON TABLE data_sync_control IS 'Controle de sincronização de dados';
COMMENT ON COLUMN order_report."Order Code" IS 'Código único do pedido - permite múltiplos itens por pedido';
COMMENT ON COLUMN order_report."Status" IS 'Status do pedido: FINISHED, EARLY_PURCHASE, CANCELED, CLOSED, PDD, FRAUD, etc';
COMMENT ON COLUMN order_report."customer_income" IS 'Renda do cliente em valor monetário';
COMMENT ON COLUMN order_report."TAC Expected" IS 'Valor TAC esperado';
COMMENT ON COLUMN order_report."TAC Paid" IS 'Valor TAC efetivamente pago';
COMMENT ON COLUMN order_report."Contract Total Value Expected" IS 'Valor total esperado do contrato';
COMMENT ON COLUMN order_report."Order Total Paid" IS 'Valor total efetivamente pago';
COMMENT ON COLUMN order_report."Remaining Total" IS 'Valor restante a ser pago';


