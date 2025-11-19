# Analysis Orchestrator Agent

## 📋 Descrição

O **Analysis Orchestrator Agent** é o **motor principal** do sistema EZPocket, responsável por transformar planos de análise em queries SQL otimizadas e seguras para AWS Athena.

## 🎯 Objetivo

Receber um plano de análise detalhado (gerado pelo PlanBuilder) e transformá-lo em uma query SQL válida, otimizada e segura, respeitando todas as regras de:
- **Segurança** (nunca expor dados sensíveis)
- **Semântica** (aplicar regras de negócio corretas)
- **Sintaxe** (garantir compatibilidade com Athena)

## 🔒 Segurança

### Dados Sensíveis Bloqueados
O agente **NUNCA** permite acesso a:
- CPF, RG, CNH, Passaporte
- E-mails pessoais (`customer_email`)
- Telefones (`customer_phone_number`)
- Endereços completos (`shipping_address`, `zip_code`)
- Serial numbers (`serial_number`)
- IMEIs (`imei_1`, `imei_2`)
- Dados bancários
- Senhas e tokens

### Operações Proibidas
- DELETE, DROP, UPDATE, TRUNCATE
- ALTER, CREATE, INSERT
- GRANT, REVOKE

### Validações Obrigatórias
- ✅ Apenas queries SELECT
- ✅ Colunas específicas (nunca SELECT *)
- ✅ Validação de segurança antes de retornar query
- ✅ Verificação de colunas sensíveis
- ✅ Verificação de operações perigosas

## 📊 Schema do Banco

Tabela principal: `receivables_db.report_orders`

### Colunas Principais
- **order_code**: Código único do pedido
- **contract_start_date**: Data de início do contrato (**principal para vendas**)
- **status**: Status do pedido (DELIVERED, CANCELED, FINISHED, etc.)
- **customer_name**: Nome do cliente (apenas agregações permitidas)
- **item_name**: Nome do produto
- **contract_total_value_expected**: Valor total esperado
- **order_total_paid**: Valor já pago
- **remaining_total**: Saldo restante

## 🛠️ Regras do Athena

### Tratamento de Datas
```sql
-- ✅ Correto
TRY(CAST(date_parse(TRIM("contract start date"), '%Y-%m-%d %I:%i %p') AS TIMESTAMP))

-- ❌ Errado
CURRENT_DATE  -- Nunca usar diretamente
```

### Filtros Temporais
```sql
-- Hoje
BETWEEN date_trunc('day', current_timestamp AT TIME ZONE 'America/New_York')
AND date_trunc('day', current_timestamp AT TIME ZONE 'America/New_York') + interval '1' day

-- Mês atual
BETWEEN date_trunc('month', current_timestamp AT TIME ZONE 'America/New_York')
AND date_trunc('month', current_timestamp AT TIME ZONE 'America/New_York') + interval '1' month
```

### Agregações
```sql
-- ✅ Sempre com alias
COUNT(*) AS total
SUM(COALESCE("order total paid", 0)) AS total_recebido

-- ❌ Sem alias
COUNT(*)  -- ERRO
```

### Funções Proibidas
- ❌ `LAST_DAY` (não existe no Athena)
- ✅ Usar: `date_trunc('month', timestamp) + interval '1' month - interval '1' day`

## 🔄 Fluxo de Execução

```
PlanBuilder → [plan gerado] 
    ↓
PlanConfirm → [usuário aceita]
    ↓
AnalysisOrchestrator → [query SQL gerada]
    ↓
QueryExecutor → [executa no Athena]
    ↓
Responder → [formata resposta]
```

## 📁 Estrutura de Arquivos

```
analysis_orchestrator_agent/
├── __init__.py                      # Exporta AnalysisOrchestratorAgent
├── analysis_orchestrator.py         # Agente principal (geração de queries)
├── roles.json                       # Regras detalhadas (schemas, instruções, exemplos)
├── test_analysis_orchestrator.py    # Testes unitários
├── test_endpoint.py                 # Servidor Flask de teste (porta 5012)
├── test_client.py                   # Cliente HTTP para testar endpoint
├── run_test.sh                      # Script para rodar testes
└── README.md                        # Esta documentação
```

## 🧪 Como Testar

### 1. Teste Unitário Direto
```bash
cd backend
source ../ezinho_assistente/bin/activate
python agents/analysis_orchestrator_agent/test_analysis_orchestrator.py
```

### 2. Teste via HTTP

**Terminal 1** - Iniciar servidor:
```bash
cd backend/agents/analysis_orchestrator_agent
./run_test.sh server
```

**Terminal 2** - Executar testes:
```bash
cd backend/agents/analysis_orchestrator_agent
./run_test.sh client
```

### 3. Teste Interativo
```bash
./run_test.sh help  # Ver todos os modos disponíveis
```

## 📥 Input Esperado

```python
{
    "pergunta": "Quantas vendas tivemos hoje?",
    "plan": "Plano detalhado gerado pelo PlanBuilder...",
    "intent_category": "quantidade",
    "username": "usuario123",
    "projeto": "projeto_x",
    "plan_confirmed": True
}
```

## 📤 Output Gerado

```python
{
    "query_sql": "SELECT COUNT(*) AS total FROM receivables_db.report_orders WHERE...",
    "query_explanation": "Conta o número de vendas realizadas hoje...",
    "columns_used": ["order code", "contract start date"],
    "filters_applied": ["contract_start_date = hoje", "timezone America/New_York"],
    "security_validated": True,
    "optimization_notes": "Query otimizada com índices...",
    "execution_time": 1.23
}
```

## 🗄️ Persistência no PostgreSQL

Tabela: `analysis_orchestrator_logs`

### Chaves Estrangeiras
- `parent_plan_confirm_id` → `plan_confirm_logs(id)`
- `parent_plan_builder_id` → `plan_builder_logs(id)`
- `parent_intent_validator_id` → `intent_validator_logs(id)`
- `parent_user_proposed_plan_id` → `user_proposed_plan_logs(id)` (opcional)

### Campos Principais
- `query_sql`: Query gerada
- `security_validated`: Passou nas validações de segurança
- `columns_used`: Array de colunas usadas
- `filters_applied`: Array de filtros aplicados
- `query_complexity`: baixa, média, alta
- `execution_time`: Tempo de geração em segundos

## 🎨 Exemplos de Queries

### Exemplo 1: Contagem Simples
**Pergunta**: "Quantas vendas tivemos hoje?"

**Query Gerada**:
```sql
SELECT COUNT(*) AS total 
FROM receivables_db.report_orders 
WHERE TRY(CAST(date_parse(TRIM("contract start date"), '%Y-%m-%d %I:%i %p') AS TIMESTAMP))
BETWEEN date_trunc('day', current_timestamp AT TIME ZONE 'America/New_York')
AND date_trunc('day', current_timestamp AT TIME ZONE 'America/New_York') + interval '1' day
```

### Exemplo 2: Top 5 Produtos
**Pergunta**: "Quais os 5 produtos mais vendidos este mês?"

**Query Gerada**:
```sql
SELECT "item_name", COUNT(*) AS total_vendas 
FROM receivables_db.report_orders 
WHERE TRY(CAST(date_parse(TRIM("contract start date"), '%Y-%m-%d %I:%i %p') AS TIMESTAMP))
BETWEEN date_trunc('month', current_timestamp AT TIME ZONE 'America/New_York')
AND date_trunc('month', current_timestamp AT TIME ZONE 'America/New_York') + interval '1' month
GROUP BY "item_name" 
ORDER BY total_vendas DESC 
LIMIT 5
```

### Exemplo 3: Comparação de Períodos
**Pergunta**: "Compare vendas deste mês com mês passado"

**Query Gerada**:
```sql
WITH mes_atual AS (
    SELECT COUNT(*) as total 
    FROM receivables_db.report_orders 
    WHERE TRY(CAST(date_parse(TRIM("contract start date"), '%Y-%m-%d %I:%i %p') AS TIMESTAMP))
    BETWEEN date_trunc('month', current_timestamp AT TIME ZONE 'America/New_York')
    AND date_trunc('month', current_timestamp AT TIME ZONE 'America/New_York') + interval '1' month
),
mes_passado AS (
    SELECT COUNT(*) as total 
    FROM receivables_db.report_orders 
    WHERE TRY(CAST(date_parse(TRIM("contract start date"), '%Y-%m-%d %I:%i %p') AS TIMESTAMP))
    BETWEEN date_trunc('month', date_add('month', -1, current_timestamp AT TIME ZONE 'America/New_York'))
    AND date_trunc('month', current_timestamp AT TIME ZONE 'America/New_York')
)
SELECT ma.total as mes_atual_total, mp.total as mes_passado_total 
FROM mes_atual ma 
CROSS JOIN mes_passado mp
```

## ⚠️ Tratamento de Erros

### Tipos de Erro
- **security**: Violação de segurança (dados sensíveis)
- **syntax**: Erro de sintaxe SQL
- **semantic**: Erro semântico (regra de negócio)
- **timeout**: Timeout na geração
- **api_error**: Erro na API OpenAI

### Resposta em Caso de Erro
```python
{
    "error": "Query rejeitada por violação de segurança: coluna customer_email detectada",
    "security_validated": False,
    "execution_time": 0.5
}
```

## 🔧 Configuração

### Variáveis de Ambiente Necessárias
```bash
OPENAI_API_KEY=sk-...              # API key da OpenAI
POSTGRES_HOST=localhost             # Host do PostgreSQL
POSTGRES_PORT=5546                  # Porta do PostgreSQL
POSTGRES_DB=ezpocket_logs          # Nome do banco
POSTGRES_USER=ezpocket_user        # Usuário do banco
POSTGRES_PASSWORD=ezpocket_pass    # Senha do banco
```

### Modelo de IA Utilizado
- **Modelo**: GPT-4o
- **Temperature**: 0.1 (baixa para respostas determinísticas)
- **Output Format**: JSON estruturado

## 📈 Métricas de Performance

- **Tempo médio de geração**: 1-3 segundos
- **Taxa de sucesso**: > 95%
- **Validação de segurança**: 100% das queries

## 🚀 Integração no Graph Orchestrator

### Worker
Arquivo: `backend/agents/graph_orchestrator/worker_analysis_orchestrator.py`

### Conexões no Grafo
```python
GRAPH_CONNECTIONS = {
    "plan_confirm": ["analysis_orchestrator", "history_preferences"],  # Se aceito
    "analysis_orchestrator": ["query_executor", "history_preferences"]  # Próximo
}
```

## 📝 Notas Importantes

1. **Timezone**: Todas as datas devem usar `America/New_York`
2. **TRIM**: Sempre aplicar `TRIM()` antes de `date_parse`
3. **TRY()**: Sempre usar `TRY(CAST(...))` para evitar erros
4. **COALESCE**: Tratar valores nulos em agregações
5. **Aliases**: Todas as agregações devem ter aliases
6. **Aspas**: Colunas com espaços devem usar aspas duplas: `"order code"`

## 🤝 Contribuição

Para adicionar novas regras ou melhorar o agente:
1. Atualizar `roles.json` com as novas regras
2. Adicionar testes em `test_analysis_orchestrator.py`
3. Atualizar documentação neste README
4. Testar com `./run_test.sh test`

## 📞 Suporte

Em caso de dúvidas ou problemas:
- Verificar logs do PostgreSQL
- Verificar validações de segurança nos logs
- Executar testes unitários
- Consultar `roles.json` para regras detalhadas
