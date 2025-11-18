# SQL Validator Agent

## 📋 Descrição

Agente responsável por validar queries SQL geradas para AWS Athena, verificando sintaxe, segurança, custos e limites operacionais.

## 🎯 Funcionalidades

### 1. Validação de Sintaxe
- Verifica sintaxe SQL padrão
- Valida compatibilidade com Athena (Presto SQL)
- Identifica funções não suportadas

### 2. Validação de Segurança
- Detecta operações proibidas (INSERT, UPDATE, DELETE, DROP, etc)
- Identifica SQL injection patterns
- Verifica funções perigosas (LOAD_FILE, INTO OUTFILE)
- Detecta UNION attacks
- Previne múltiplas queries (;)

### 3. Estimativa de Custos
- Calcula tamanho estimado de scan (GB)
- Estima custo em USD ($5.00 por TB escaneado)
- Prevê tempo de execução

### 4. Análise de Risco
- **Low**: Queries simples, custo < $0.01, tempo < 10s
- **Medium**: Queries moderadas, custo $0.01-$0.10, tempo 10-30s
- **High**: Queries complexas, custo > $0.10, tempo > 30s, problemas de segurança

### 5. Otimizações
- Sugere melhorias de performance
- Identifica SELECT * desnecessários
- Recomenda uso de partições
- Alerta sobre JOINs custosos

## 🔧 Limites do AWS Athena

| Limite                      | Valor      |
| --------------------------- | ---------- |
| Tamanho máximo da query     | 256 KB     |
| Tempo máximo de execução    | 30 minutos |
| Queries concorrentes        | 25         |
| Tamanho máximo do resultado | 10 GB      |
| Custo por TB escaneado      | $5.00 USD  |

## 📥 Input Esperado

```json
{
  "query_sql": "SELECT COUNT(*) FROM orders WHERE date >= current_date",
  "username": "test_user",
  "projeto": "ezpocket",
  "estimated_complexity": "baixa"
}
```

## 📤 Output Gerado

```json
{
  "valid": true,
  "query_validated": "SELECT COUNT(*) FROM orders WHERE date >= current_date",
  "syntax_valid": true,
  "athena_compatible": true,
  "security_issues": [],
  "warnings": ["Query usa COUNT(*) que pode ser otimizado"],
  "optimization_suggestions": ["Considere adicionar filtros de partição"],
  "estimated_scan_size_gb": 0.5,
  "estimated_cost_usd": 0.0025,
  "estimated_execution_time_seconds": 3.5,
  "risk_level": "low",
  "tokens_used": 450,
  "model_used": "gpt-4o",
  "execution_time": 1.2,
  "error": null
}
```

## 🚀 Uso

### Modo Interativo
```bash
cd backend/agents/sql_validator_agent
python sql_validator.py
```

### Modo Servidor
```bash
python sql_validator.py server
```

### Integração no Grafo
O agente é chamado automaticamente após o `analysis_orchestrator` e antes do `history_preferences`:

```
analysis_orchestrator → [sql_validator, history_preferences]
```

## 🔗 Dependências

- OpenAI GPT-4o para validação semântica
- PostgreSQL para armazenar logs
- Redis para comunicação entre workers

## 📊 Logs no Banco

Tabela: `sql_validator_logs`

Campos principais:
- `query_sql`: Query validada
- `valid`: Se passou na validação
- `risk_level`: Nível de risco (low/medium/high)
- `estimated_cost_usd`: Custo estimado
- `security_issues`: Problemas de segurança encontrados
- Parent IDs para rastreabilidade completa

## 🎓 Exemplos

### Query Válida
```sql
SELECT order_id, SUM(amount) 
FROM orders 
WHERE date_partition >= '2025-01-01' 
GROUP BY order_id
```
✅ Valid: true, Risk: low, Cost: $0.002

### Query com Problemas
```sql
SELECT * FROM orders; DROP TABLE orders;
```
❌ Valid: false, Security Issues: ["Múltiplas queries", "Operação DROP proibida"]

### Query Custosa
```sql
SELECT * 
FROM large_table a 
JOIN another_large_table b ON a.id = b.id 
JOIN third_table c ON b.id = c.id
```
⚠️ Valid: true, Risk: high, Cost: $0.50, Warnings: ["JOINs múltiplos sem filtros", "SELECT * desnecessário"]
