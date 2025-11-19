# 🔧 Auto Correction Agent

## 📋 Visão Geral

O **Auto Correction Agent** é responsável por corrigir queries SQL inválidas, tornando-as compatíveis com o AWS Athena e seguindo as regras de segurança do sistema. Ele entra no fluxo quando o **SQL Validator** detecta que uma query é inválida.

## 🎯 Função no Fluxo

```
SQL Validator (inválido) → [Auto Correction, History] → Auto Correction → History
                   ↓
                (válido) → History
```

### Quando é Acionado?
- ✅ Query inválida detectada pelo SQL Validator
- ✅ Operações proibidas (INSERT, UPDATE, DELETE, DROP)
- ✅ Funções incompatíveis com Athena
- ✅ Sintaxe SQL incorreta
- ✅ Acesso a colunas sensíveis (CPF, email, etc.)
- ✅ Tentativas de SQL injection

### Quando NÃO é Acionado?
- ❌ Query válida (vai direto para History)

## 🔍 Funcionalidades

### 1. Correção Automática (Rule-based)
Remove/substitui automaticamente:
- **Operações proibidas**: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, GRANT, REVOKE
- **SQL Injection**: '; DROP TABLE, '; DELETE FROM, '--', '/*', '*/'
- **Funções incompatíveis**:
  - `NOW()` → `CURRENT_TIMESTAMP`
  - `STR_TO_DATE()` → `DATE_PARSE()`
  - `ISNULL()` → `COALESCE()`
  - `IFNULL()` → `COALESCE()`

### 2. Correção Semântica (GPT-4o)
Quando correções automáticas não são suficientes, usa GPT-4o para:
- Corrigir sintaxe SQL complexa
- Ajustar nomes de colunas (typos)
- Reorganizar estrutura da query
- Manter intenção original da consulta

### 3. Estratégias de Correção
1. **remove_forbidden_operations**: Remove operações não permitidas
2. **fix_syntax_errors**: Corrige erros de sintaxe SQL
3. **replace_incompatible_functions**: Substitui funções incompatíveis
4. **fix_column_names**: Corrige nomes de colunas (typos)
5. **remove_security_violations**: Remove violações de segurança
6. **fix_date_parsing**: Ajusta parsing de datas

## 📊 Entrada e Saída

### Entrada (do SQL Validator)
```json
{
  "query_original": "INSERT INTO orders VALUES (1, 100)",
  "validation_issues": [
    "Operação proibida detectada: INSERT"
  ],
  "username": "user123",
  "projeto": "ezpocket"
}
```

### Saída (para History)
```json
{
  "success": true,
  "query_original": "INSERT INTO orders VALUES (1, 100)",
  "query_corrected": "SELECT * FROM orders WHERE id = 1",
  "corrections_applied": [
    "remove_forbidden_operation: Removida operação INSERT (não permitida no Athena)",
    "gpt_correction: Convertida em consulta SELECT equivalente"
  ],
  "corrections_count": 2,
  "correction_explanation": "Operação INSERT não é suportada pelo Athena...",
  "changes_summary": "Removida operação INSERT, convertida em SELECT",
  "confidence": 0.95,
  "execution_time": 1.23,
  "model_used": "gpt-4o",
  "tokens_used": 450
}
```

## 🗄️ Banco de Dados

### Tabela: `auto_correction_logs`
```sql
CREATE TABLE auto_correction_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_sequence INTEGER DEFAULT 7,
    
    -- Parent IDs
    parent_sql_validator_id UUID REFERENCES sql_validator_logs(id),
    parent_analysis_orchestrator_id UUID,
    parent_plan_confirm_id UUID,
    parent_plan_builder_id UUID,
    parent_intent_validator_id UUID,
    
    -- Correção
    query_original TEXT NOT NULL,
    validation_issues JSONB,
    success BOOLEAN NOT NULL,
    query_corrected TEXT,
    corrections_applied JSONB,
    corrections_count INTEGER,
    correction_explanation TEXT,
    changes_summary TEXT,
    confidence REAL,
    
    -- Performance
    execution_time REAL,
    model_used VARCHAR(50),
    tokens_used INTEGER,
    
    -- Metadata
    username VARCHAR(100),
    projeto VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**12 índices criados** para performance nas buscas.

## 🧪 Testes

### Modo Servidor
Inicia servidor Flask na porta 5015:
```bash
./run_test.sh server
```

### Modo Interativo
Corrige queries manualmente:
```bash
./run_test.sh interactive
```

### Bateria de Testes Automatizada
Executa 6 testes pré-definidos:
```bash
./run_test.sh tests
```

**Testes incluídos:**
1. ✅ Correção de operação INSERT proibida
2. ✅ Correção de múltiplas queries (SQL injection)
3. ✅ Correção de coluna sensível (CPF)
4. ✅ Correção de função incompatível (NOW())
5. ✅ Correção de sintaxe SQL (aspas incorretas)
6. ✅ Correção combinada (múltiplos erros)

## 📁 Estrutura de Arquivos

```
auto_correction_agent/
├── __init__.py                  # Exports do módulo
├── auto_correction.py           # Agente principal (445 linhas)
├── roles.json                   # Regras de correção (150+ linhas)
├── run_test.sh                  # Script de teste
├── test_endpoint.py             # Servidor Flask (porta 5015)
├── test_client.py               # Cliente de teste
└── README.md                    # Esta documentação
```

## 🔗 Integração

### Worker Redis
```python
# worker_auto_correction.py
def process(data):
    result = agent.correct(
        query_original=data['query_validated'],
        validation_issues=combined_issues,
        username=data.get('username'),
        projeto=data.get('projeto')
    )
    
    # Próximo módulo: sempre History
    return {
        'previous_module': 'auto_correction',
        '_next_modules': ['history_preferences'],
        ...
    }
```

### History Preferences
```python
# history_preferences.py - linha 758-840
case 'auto_correction':
    # Salva logs na tabela auto_correction_logs
    INSERT INTO auto_correction_logs (...)
```

## ⚙️ Configuração

### Variáveis de Ambiente
```bash
OPENAI_API_KEY=sk-...                    # Obrigatório
OPENAI_MODEL=gpt-4o                      # Padrão: gpt-4o
AUTO_CORRECTION_TIMEOUT=30               # Padrão: 30s
AUTO_CORRECTION_MAX_TOKENS=2000          # Padrão: 2000
AUTO_CORRECTION_TEMPERATURE=0.2          # Padrão: 0.2
```

### Dependências
```bash
pip install openai flask requests
```

## 📈 Métricas e Performance

### Logs Registrados
- ✅ Query original e corrigida
- ✅ Lista de correções aplicadas
- ✅ Explicação detalhada
- ✅ Nível de confiança (0.0-1.0)
- ✅ Tempo de execução
- ✅ Tokens usados (GPT-4o)
- ✅ Modelo utilizado

### Performance Esperada
- **Correção rule-based**: < 0.1s
- **Correção GPT-4o**: 1-3s (depende da complexidade)
- **Tokens médios**: 300-600 por correção

## 🚀 Como Usar

### 1. Iniciar servidor de teste
```bash
cd backend/agents/auto_correction_agent
chmod +x run_test.sh
./run_test.sh server
```

### 2. Testar correção (outro terminal)
```bash
./run_test.sh interactive
```

### 3. Executar bateria de testes
```bash
./run_test.sh tests
```

### 4. Usar no fluxo completo
```bash
cd backend/agents/graph_orchestrator
./start_workers.sh  # Inicia worker 8/9 (auto_correction)
```

## 🔒 Segurança

### Operações Proibidas
O agente **sempre remove** estas operações:
- INSERT, UPDATE, DELETE
- DROP, ALTER, CREATE, TRUNCATE
- GRANT, REVOKE

### Colunas Sensíveis
Queries com acesso a colunas sensíveis são **rejeitadas** (não corrigidas):
- cpf, email, password, senha, credit_card, etc.

### SQL Injection
Padrões de SQL injection são **automaticamente removidos**:
- `'; DROP TABLE`
- `'; DELETE FROM`
- `--` (comentários)
- `/* */` (comentários multi-linha)

## 🎓 Exemplos de Uso

### Exemplo 1: Operação Proibida
**Entrada:**
```sql
INSERT INTO orders (id, amount) VALUES (1, 100)
```

**Saída:**
```sql
SELECT * FROM orders WHERE id = 1
```

**Correções:**
- ✅ Removida operação INSERT
- ✅ Convertida em SELECT equivalente

---

### Exemplo 2: Função Incompatível
**Entrada:**
```sql
SELECT * FROM orders WHERE date > NOW()
```

**Saída:**
```sql
SELECT * FROM orders WHERE date > CURRENT_TIMESTAMP
```

**Correções:**
- ✅ Substituída NOW() por CURRENT_TIMESTAMP

---

### Exemplo 3: SQL Injection
**Entrada:**
```sql
SELECT * FROM orders WHERE id = 1; DROP TABLE orders;
```

**Saída:**
```sql
SELECT * FROM orders WHERE id = 1
```

**Correções:**
- ✅ Removida segunda query (DROP TABLE)
- ✅ Mantida apenas consulta SELECT segura

---

## 📚 Documentação Técnica

### Arquivo Principal: `auto_correction.py`
- **Classe:** `AutoCorrectionAgent`
- **Método principal:** `correct(query_original, validation_issues, username, projeto)`
- **Retorno:** Dicionário com resultado da correção

### Arquivo de Regras: `roles.json`
- **system_role:** Prompt do GPT-4o
- **athena_rules:** Regras do AWS Athena
- **schema_rules:** Regras de schema do banco
- **correction_strategies:** 6 estratégias detalhadas

### Worker: `worker_auto_correction.py`
- **Fila:** `auto_correction`
- **Entrada:** Dados do SQL Validator
- **Saída:** Próximo módulo = History

## 🐛 Troubleshooting

### Erro: "Não foi possível conectar ao servidor"
```bash
# Verifique se o servidor está rodando
./run_test.sh server

# Em outro terminal
curl http://localhost:5015/health
```

### Erro: "OPENAI_API_KEY não definida"
```bash
export OPENAI_API_KEY=sk-...
```

### Erro: "Timeout ao corrigir query"
```bash
# Aumente o timeout (padrão: 30s)
export AUTO_CORRECTION_TIMEOUT=60
```

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs em `auto_correction_logs`
2. Execute `./run_test.sh tests` para validar funcionalidade
3. Consulte a documentação do SQL Validator Agent

## 🎯 Roadmap

- [x] Correção rule-based
- [x] Correção semântica (GPT-4o)
- [x] Bateria de testes automatizada
- [x] Integração com History
- [ ] Métricas de acurácia das correções
- [ ] Dashboard de correções aplicadas
- [ ] Cache de correções comuns
- [ ] Fine-tuning do modelo para correções específicas

---

**Versão:** 1.0.0  
**Última atualização:** Janeiro 2025  
**Autor:** EZPoket Team
