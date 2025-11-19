# Athena Executor Agent

## 📋 Visão Geral

O **Athena Executor Agent** é responsável por **executar queries SQL no AWS Athena**. Este agente **NÃO usa IA**, apenas executa a query final validada ou corrigida no banco de dados Athena.

## 🎯 Objetivo

Executar queries SQL no AWS Athena e retornar os resultados para o usuário.

## 🔄 Posição no Fluxo

```
┌─────────────────┐
│ SQL Validator   │ ──(query válida)──┐
└─────────────────┘                   │
                                      ▼
                            ┌─────────────────────┐
                            │ Athena Executor     │ ──► History ──► FIM
                            └─────────────────────┘
                                      ▲
┌─────────────────┐                   │
│ Auto Correction │ ──(query corrigida)┘
└─────────────────┘
```

### Quando é Chamado?

1. **Após SQL Validator**: Se a query foi validada e está OK
2. **Após Auto Correction**: Se a query foi corrigida

### Execution Sequence: **8**

## 📥 Input

Recebe dados do **SQL Validator** (query válida) OU **Auto Correction** (query corrigida):

```json
{
  "query_validated": "SELECT * FROM orders WHERE status = 'pending'",
  "query_corrected": "SELECT * FROM orders WHERE status = 'pending'",
  "username": "joao.silva",
  "projeto": "ecommerce",
  "pergunta": "Mostre os pedidos pendentes",
  "parent_sql_validator_id": "uuid...",
  "parent_auto_correction_id": "uuid..."
}
```

## 📤 Output

Retorna resultado da execução:

```json
{
  "success": true,
  "query_executed": "SELECT * FROM orders WHERE status = 'pending'",
  "execution_time_seconds": 2.45,
  "row_count": 150,
  "column_count": 8,
  "columns": ["order_id", "customer_name", "total", "status", "created_at"],
  "results_preview": [
    {"order_id": "ORD-001", "customer_name": "João Silva", "total": 250.00, "status": "pending"},
    {"order_id": "ORD-002", "customer_name": "Maria Santos", "total": 180.50, "status": "pending"}
  ],
  "data_size_mb": 0.85,
  "database": "receivables_db",
  "region": "us-east-1",
  "error": null,
  "_next_modules": ["history_preferences"]
}
```

## ⚙️ Processamento

O agente executa os seguintes passos:

### 1️⃣ Determinar Query Final
```python
# Prioridade: query_corrected > query_validated > query_sql
query_sql = data.get('query_corrected') or data.get('query_validated') or data.get('query_sql')
```

### 2️⃣ Executar no Athena
```python
df = wr.athena.read_sql_query(
    sql=query_sql,
    database=self.database,
    boto3_session=self.boto3_session,
    s3_output=self.athena_output_s3
)
```

### 3️⃣ Processar Resultados
- Conta linhas e colunas
- Extrai primeiras 100 linhas para preview
- Calcula tamanho dos dados
- Converte DataFrame para JSON

### 4️⃣ Tratar Erros
Se houver erro na execução:
```json
{
  "success": false,
  "error": "SYNTAX_ERROR: line 1:8: Column 'invalid_column' cannot be resolved",
  "error_type": "QueryExecutionError"
}
```

## 🗄️ Banco de Dados

Salva log em `athena_executor_logs`:

```sql
CREATE TABLE athena_executor_logs (
    id UUID PRIMARY KEY,
    execution_sequence INTEGER DEFAULT 8,
    
    -- Parent IDs
    parent_sql_validator_id UUID,
    parent_auto_correction_id UUID,
    parent_analysis_orchestrator_id UUID,
    parent_plan_confirm_id UUID,
    parent_plan_builder_id UUID,
    parent_intent_validator_id UUID,
    
    -- Query Execution
    query_executed TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    
    -- Results
    row_count INTEGER,
    column_count INTEGER,
    columns JSONB,
    results_preview JSONB,
    data_size_mb REAL,
    
    -- Athena Info
    database VARCHAR(255),
    region VARCHAR(50),
    
    -- Error Info
    error TEXT,
    error_type VARCHAR(100),
    
    -- Performance
    execution_time_seconds REAL,
    
    -- Metadata
    username VARCHAR(255),
    projeto VARCHAR(255),
    created_at TIMESTAMP
);
```

## 🔀 Próximo Módulo

Sempre vai para: **`history_preferences`**

O History salva o resultado da execução na tabela `athena_executor_logs`.

## 🚀 Como Testar

### Teste com Script Interativo (Recomendado)
```bash
cd /home/developer/Projetos/projectezpocket/ezpocket/EZPOKET/backend/agents/athena_executor_agent
./run_test.sh
```

O script oferece 3 opções:
1. **Servidor Flask (HTTP API)** - Porta 5017
2. **Cliente Interativo (Terminal)** - Menu interativo com exemplos
3. **Teste Rápido (Standalone)** - Execução simples

### Teste via HTTP (Servidor Flask)
```bash
# Terminal 1 - Iniciar servidor
./run_test.sh  # Escolher opção 1

# Terminal 2 - Enviar requisição
curl -X POST http://localhost:5017/test-executor \
  -H "Content-Type: application/json" \
  -d '{
    "query_sql": "SELECT * FROM orders LIMIT 10",
    "username": "joao.silva",
    "projeto": "ecommerce"
  }'

# Teste com mock (sem executar no Athena real)
curl -X POST http://localhost:5017/test-executor-mock \
  -H "Content-Type: application/json" \
  -d '{"query_sql": "SELECT * FROM orders LIMIT 10"}'
```

### Teste Standalone
```bash
cd /home/developer/Projetos/projectezpocket/ezpocket/EZPOKET/backend/agents/athena_executor_agent
python athena_executor.py
```

### Teste com Worker (Redis)
```bash
# Em um terminal
cd /home/developer/Projetos/projectezpocket/ezpocket/EZPOKET/backend/agents/graph_orchestrator
python worker_athena_executor.py

# Em outro terminal
python -c "
import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0)
job = {
    'query_validated': 'SELECT * FROM orders LIMIT 10',
    'username': 'test_user',
    'projeto': 'test_project'
}
r.lpush('queue:athena_executor', json.dumps(job))
print('Job enviado!')
"
```

### ✅ Verificar Resultados no Banco

Após executar, verifique os logs salvos:

```sql
-- Ver últimas execuções
SELECT 
    id,
    query_executed,
    success,
    row_count,
    execution_time_seconds,
    username,
    projeto,
    created_at
FROM athena_executor_logs
ORDER BY created_at DESC
LIMIT 10;

-- Ver execuções com erro
SELECT 
    query_executed,
    error,
    error_type,
    username,
    created_at
FROM athena_executor_logs
WHERE success = FALSE
ORDER BY created_at DESC;

-- Estatísticas de execução
SELECT 
    success,
    COUNT(*) as total_execucoes,
    AVG(execution_time_seconds) as tempo_medio,
    AVG(row_count) as linhas_media,
    AVG(data_size_mb) as tamanho_medio_mb
FROM athena_executor_logs
GROUP BY success;
```

## 📊 Métricas

O agente registra:
- ✅ **Success rate**: Percentual de queries executadas com sucesso
- ⏱️ **Execution time**: Tempo médio de execução das queries
- 📦 **Data size**: Tamanho médio dos resultados retornados
- 📊 **Row count**: Número médio de linhas retornadas

## ⚠️ Observações Importantes

1. **NÃO usa IA**: Este é um agente executor puro, sem LLM
2. **Execução real**: Executa queries reais no AWS Athena (custa dinheiro!)
3. **Limite de preview**: Retorna apenas primeiras 100 linhas no preview
4. **Timeout**: Queries podem dar timeout se demorarem muito
5. **Credenciais AWS**: Precisa de `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, `AWS_REGION` e `ATHENA_OUTPUT_S3` no `.env`

## 🔧 Configuração

Variáveis de ambiente necessárias (`.env`):

```bash
AWS_ACCESS_KEY=sua_access_key
AWS_SECRET_KEY=sua_secret_key
AWS_REGION=us-east-1
ATHENA_OUTPUT_S3=s3://seu-bucket/athena-results/
```

## 🐛 Troubleshooting

### Erro: "Unable to connect to Athena"
- Verifique as credenciais AWS no `.env`
- Confirme que a região está correta
- Verifique se o bucket S3 existe

### Erro: "Query timeout"
- A query pode ser muito complexa
- Verifique se há problemas de performance no Athena
- Considere otimizar a query

### Erro: "Table not found"
- Verifique se a tabela existe no database `receivables_db`
- Confirme que o database está correto

## 📝 Logs

O agente produz logs detalhados:

```
🚀 ATHENA EXECUTOR AGENT - EXECUÇÃO DE QUERY
📥 INPUTS:
   👤 Username: joao.silva
   📁 Projeto: ecommerce
   📝 Query: SELECT * FROM orders...

⚙️  PROCESSAMENTO:
   🔄 Executando query no AWS Athena...

📤 OUTPUT:
   ✅ Execução bem-sucedida
   📊 Linhas retornadas: 150
   📋 Colunas: 8
   💾 Tamanho dos dados: 0.85 MB
   ⏱️  Tempo de execução: 2.45s
   🏛️  Database: receivables_db
```

## 🔗 Integração

O Athena Executor é chamado automaticamente pelo:
- **Worker SQL Validator**: Quando query é válida
- **Worker Auto Correction**: Após corrigir query

Não precisa ser chamado manualmente.
