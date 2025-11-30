# Documento Técnico de Arquitetura - ezpocket

## Índice

1. [Visão Geral](#visão-geral)
2. [Stack Tecnológico](#stack-tecnológico)
3. [Arquitetura de Filas e Workers](#arquitetura-de-filas-e-workers)
4. [Pipeline de Processamento](#pipeline-de-processamento)
5. [Gerenciamento de Contexto](#gerenciamento-de-contexto)
6. [Persistência de Dados](#persistência-de-dados)
7. [Segurança](#segurança)
8. [Infraestrutura e Deploy](#infraestrutura-e-deploy)
9. [Escalabilidade](#escalabilidade)
10. [Monitoramento e Logs](#monitoramento-e-logs)

---

## Visão Geral

O ezpocket é uma plataforma de análise de dados conversacional que utiliza IA (GPT-4o) para processar perguntas em linguagem natural e gerar insights sobre dados operacionais. A arquitetura é baseada em um sistema de **pipeline assíncrono com filas Redis customizadas** que orquestram 14 agentes especializados.

### Características Principais

- **Arquitetura de Microserviços**: 14 agentes independentes processando jobs especializados
- **Sistema de Filas Customizado**: Implementação própria sobre Redis (não usa RQ/Celery/BullMQ)
- **Pipeline DAG (Directed Acyclic Graph)**: Fluxo condicional com ramificações e loops controlados
- **Gerenciamento de Contexto**: Propagação de histórico de conversas entre todos os agentes
- **Processamento Assíncrono**: Workers independentes com comunicação via filas Redis
- **Execução Dual**: Queries locais (PostgreSQL) ou cloud (AWS Athena)

---

## Stack Tecnológico

### Backend

**Python 3.11**
- Framework: Flask 3.1.2
- WebSocket: Flask-SocketIO 5.5.1
- Autenticação: PyJWT 2.10.1
- Environment: python-dotenv 1.2.1

### Banco de Dados

**PostgreSQL 15**
- Tabelas: `projects`, `conversations`, `order_report`
- Pool de conexões: psycopg2-binary 2.9.11
- Schemas: Projetos com isolamento por usuário

**Redis 7.0.1**
- Uso: Sistema de filas customizado
- Estruturas: Listas (RPUSH/BLPOP), Strings (SET/GET), Sets (SADD/SISMEMBER)
- TTL: Jobs com expiração de 1 hora

### Cloud Services

**AWS Athena**
- Engine: Presto SQL
- Fonte: S3 Bucket `receivables_db` (Parquet)
- Biblioteca: awswrangler 3.14.0
- Região: Configurável via .env

### Inteligência Artificial

**OpenAI GPT-4o**
- API: openai 2.7.2
- Temperatura: 0.1 (precisão) a 0.7 (criatividade)
- Tokens: Contexto até 128k tokens
- Agentes: 8 agentes utilizam GPT-4o

### Frontend

**HTML5 + Vanilla JavaScript**
- Estilização: Tailwind CSS (CDN)
- WebSocket Client: Socket.IO Client 4.x
- Markdown: marked.js para renderização

### Infraestrutura

**PM2 Process Manager**
- Configuração: ezpocket_remastered.config.js
- Instâncias: 8 workers Flask em cluster
- Workers: 13 agentes Python em modo fork
- Auto-restart: Habilitado com limite de 10 tentativas

**Nginx**
- Reverse Proxy: Porta 80 → 3004
- WebSocket: Upgrade habilitado
- Static Files: Servindo arquivos estáticos

---

## Arquitetura de Filas e Workers

### Sistema de Filas Customizado

O ezpocket **não utiliza bibliotecas de filas prontas** (RQ, Celery, BullMQ). Implementa um sistema próprio sobre Redis por razões específicas:

#### Por que Customizado?

1. **Controle total do fluxo DAG**: Conexões condicionais entre módulos
2. **Propagação de contexto**: Estado compartilhado entre todos os workers
3. **Parent tracking**: Rastreabilidade completa via parent_id chain
4. **Interatividade**: Suporte a confirmações e feedback do usuário
5. **Simplicidade**: Sem overhead de frameworks complexos

#### Implementação Redis

```python
# Estrutura de filas
queue:{module_name}  # Lista para cada módulo
job:{job_id}         # Hash com dados do job
cancelled_jobs:{username}:{projeto}  # Set de jobs cancelados
```

**Operações principais:**

```python
# Enfileirar job
redis.rpush(f"queue:{module_name}", job_id)

# Consumir job (bloqueante)
result = redis.blpop(f"queue:{module_name}", timeout=1)

# Armazenar dados do job
redis.setex(f"job:{job_id}", 3600, json.dumps(job_data))

# Verificar cancelamento
redis.sismember(f"cancelled_jobs:{username}:{projeto}", job_id)
```

### Arquitetura de Workers

#### Classe Base: ModuleWorker

Todos os workers herdam de `ModuleWorker` (graph_orchestrator.py):

```python
class ModuleWorker:
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.redis_client = Redis(**REDIS_CONFIG)
        self.queue_name = f"queue:{module_name}"
        self.connections = GRAPH_CONNECTIONS
        
    def start(self):
        """Loop infinito consumindo fila"""
        while self.running:
            result = self.redis_client.blpop(self.queue_name, timeout=1)
            if result:
                self.process_job(job_id)
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Método abstrato - implementado por cada worker"""
        raise NotImplementedError
```

#### Ciclo de Vida de um Job

1. **Submissão**: Graph Orchestrator cria job_id e enfileira
2. **Consumo**: Worker executa `blpop` (bloqueante até ter job)
3. **Verificação**: Checa se job foi cancelado
4. **Processamento**: Executa lógica específica do agente
5. **Propagação**: Determina próximos módulos via `_next_modules`
6. **Enfileiramento**: Submete job_id para filas dos próximos módulos
7. **Salvamento**: History Preferences persiste no PostgreSQL
8. **TTL**: Job expira após 1 hora no Redis

#### Gestão de Estado

```python
job_data = {
    'job_id': str(uuid.uuid4()),
    'username': username,
    'projeto': projeto,
    'start_module': 'intent_validator',
    'current_module': 'plan_builder',
    'data': {
        'pergunta': '...',
        'conversation_context': '...',
        'has_history': True,
        # Resultados acumulados de módulos anteriores
    },
    'execution_chain': [
        {'module': 'intent_validator', 'timestamp': '...', 'execution_time': 1.2},
        {'module': 'plan_builder', 'timestamp': '...', 'execution_time': 2.5}
    ],
    'status': 'processing',
    'created_at': '2025-11-29T10:30:00',
    'parent_job_id': None  # Para jobs paralelos
}
```

### Configuração do Grafo (graph_config.py)

O arquivo `graph_config.py` define as conexões entre módulos:

```python
GRAPH_CONNECTIONS = {
    'intent_validator': ['plan_builder', 'history_preferences'],
    'plan_builder': ['plan_confirm', 'history_preferences'],
    'plan_confirm': ['history_preferences'],  # Simplificado
    'user_proposed_plan': ['plan_refiner', 'history_preferences'],
    'plan_refiner': ['plan_confirm', 'history_preferences'],
    'analysis_orchestrator': ['history_preferences'],
    'history_preferences': []
}
```

**Nota**: Esta configuração está **simplificada**. Na prática, o pipeline real continua:
- `analysis_orchestrator` → `sql_validator`
- `sql_validator` → `athena_executor` (se válido) ou `auto_correction` (se inválido)
- `athena_executor` → `python_runtime`
- `python_runtime` → `response_composer`
- `response_composer` → `user_feedback`
- `user_feedback` → `history_preferences`

Os workers implementam essa lógica via `_next_modules` no dicionário de retorno.

---

## Pipeline de Processamento

### Fluxo Principal (Happy Path)

```
Usuário
  ↓
WebSocket (Socket.IO)
  ↓
Graph Orchestrator (submit_job)
  ↓
[1] Intent Validator (valida intenção) ───→ History (paralelo)
  ↓
[2] Plan Builder (gera plano) ───→ History (paralelo)
  ↓
[3] Plan Confirm (aguarda confirmação) ───→ History (paralelo)
  ↓ (se aceito)
[4] Analysis Orchestrator (gera SQL) ───→ History (paralelo)
  ↓
[5] SQL Validator (valida sintaxe) ───→ History (paralelo)
  ↓ (se válido)
[6] Athena Executor (executa query) ───→ History (paralelo)
  ↓
[7] Python Runtime (análise estatística) ───→ History (paralelo)
  ↓
[8] Response Composer (formata resposta) ───→ History (paralelo)
  ↓
[9] User Feedback (coleta rating) ───→ History (paralelo)
  ↓
[10] History Preferences (salva tudo)
  ↓
Graph Orchestrator (job completo)
  ↓
WebSocket emit('message')
  ↓
Frontend (renderiza resposta)
```

### Agentes e Responsabilidades

#### 1. Intent Validator (IA - GPT-4o)
- **Função**: Valida se pergunta é adequada ao domínio
- **Input**: `pergunta`, `username`, `projeto`, `conversation_context`
- **Output**: `intent_valid`, `intent_category`, `intent_reason`
- **Roles**: `roles.json`
- **Queue**: `queue:intent_validator`

#### 2. Plan Builder (IA - GPT-4o)
- **Função**: Gera plano de execução da query
- **Input**: Resultado do Intent Validator + contexto
- **Output**: `plan`, `plan_steps`, `estimated_complexity`
- **Roles**: `roles.json` + `roles_local.json`
- **Queue**: `queue:plan_builder`

#### 3. Plan Confirm (Utility)
- **Função**: Aguarda confirmação do usuário (interativo)
- **Input**: Plano gerado
- **Output**: `plan_confirmed`, `plan_rejected`, `user_response`
- **Timeout**: 5 minutos
- **Queue**: `queue:plan_confirm` + `queue:interactive_plan_confirm`

#### 4. User Proposed Plan (Utility)
- **Função**: Recebe sugestão de alteração do usuário
- **Input**: Plano original + sugestão
- **Output**: `user_suggestion`, `modified_plan`
- **Timeout**: 5 minutos
- **Queue**: `queue:user_proposed_plan`

#### 5. Plan Refiner (IA - GPT-4o)
- **Função**: Refina plano com sugestões do usuário
- **Input**: Plano original + sugestão
- **Output**: `refined_plan`, `refinement_summary`
- **Roles**: `roles_local.json`
- **Queue**: `queue:plan_refiner`

#### 6. Analysis Orchestrator (IA - GPT-4o)
- **Função**: Transforma plano em query SQL otimizada
- **Input**: Plano confirmado + contexto
- **Output**: `query_sql`, `query_explanation`, `columns_used`
- **Roles**: `roles.json` + `roles_local.json`
- **Queue**: `queue:analysis_orchestrator`

#### 7. SQL Validator (IA - GPT-4o)
- **Função**: Valida sintaxe e compatibilidade Athena/PostgreSQL
- **Input**: `query_sql`
- **Output**: `valid`, `syntax_valid`, `athena_compatible`, `security_issues`
- **Validações**: Sintaxe, segurança, custo estimado
- **Queue**: `queue:sql_validator`

#### 8. Auto Correction (IA - GPT-4o)
- **Função**: Corrige SQL inválido
- **Input**: SQL inválido + erros
- **Output**: `query_corrected`, `corrections_applied`
- **Roles**: `roles_local.json`
- **Queue**: `queue:auto_correction`

#### 9. Athena Executor (Utility)
- **Função**: Executa query no banco escolhido
- **Input**: `query_validated` ou `query_corrected`
- **Output**: `results_full`, `row_count`, `execution_time_seconds`
- **Destinos**: 
  - **Local**: PostgreSQL `order_report` (se `BD_REFERENCE=Local`)
  - **Cloud**: AWS Athena S3 (se `BD_REFERENCE=Athena`)
- **Queue**: `queue:athena_executor`

#### 10. Python Runtime (IA - GPT-4o)
- **Função**: Análise estatística com pandas/numpy
- **Input**: Resultados da query + contexto
- **Output**: `analysis_summary`, `statistics`, `insights`, `recommendations`
- **Bibliotecas**: pandas, numpy
- **Queue**: `queue:python_runtime`

#### 11. Response Composer (IA - GPT-4o)
- **Função**: Formata resposta em Markdown humanizado
- **Input**: Análise estatística + contexto
- **Output**: `response_text`, `key_numbers`, `formatting_style`
- **Formato**: Markdown com tabelas, listas, destaques
- **Queue**: `queue:response_composer`

#### 12. User Feedback (Utility)
- **Função**: Coleta avaliação do usuário (1-5 estrelas)
- **Input**: Resposta final
- **Output**: `rating`, `feedback_comment`
- **Timeout**: 5 minutos
- **Queue**: `queue:user_feedback`

#### 13. History Preferences (Utility)
- **Função**: Salva toda a interação no PostgreSQL
- **Input**: Dados de todos os módulos anteriores
- **Output**: Registros persistidos
- **Tabela**: `conversations`
- **Metadados**: Parent IDs para rastreabilidade completa
- **Queue**: `queue:history_preferences`

#### 14. Data Sync Agent (Utility - Separado)
- **Função**: Sincroniza Athena → PostgreSQL periodicamente
- **Execução**: Cron PM2 (não faz parte do pipeline principal)
- **Destino**: Tabela `order_report` local
- **Frequência**: Configurável (ex: a cada 1 hora)

---

## Gerenciamento de Contexto

### Sistema de Propagação de Contexto

O ezpocket implementa **contexto conversacional** que permite continuidade entre perguntas:

#### Busca de Histórico

Quando o usuário tem um **projeto ativo**, o sistema:

1. **Frontend**: Busca histórico via `GET /api/projects/{id}/conversations`
2. **Backend**: Retorna array de mensagens anteriores
3. **Frontend**: Envia `conversation_history[]` no `socket.emit('start_job')`

#### Formatação de Contexto

O Graph Orchestrator formata o histórico antes de submeter o job:

```python
def format_context(conversation_history: List[Dict]) -> str:
    """
    Formata array de conversas em string legível
    """
    if not conversation_history:
        return ""
    
    context = "--- HISTÓRICO DE CONVERSAS ---\n"
    for msg in conversation_history[-10:]:  # Últimas 10 mensagens
        sender = msg['sender']
        message = msg['message']
        context += f"{sender}: {message}\n"
    context += "--- FIM DO HISTÓRICO ---\n"
    
    return context
```

#### Propagação para Agentes

Todos os agentes recebem no `initial_data`:

```python
initial_data = {
    'pergunta': 'E hoje?',
    'username': 'diogo',
    'projeto': 'vendas_2024',
    'conversation_context': '--- HISTÓRICO ---\nUsuário: Quantas vendas ontem?\nAssistente: Foram 150 vendas.\n--- FIM ---',
    'has_history': True  # Flag booleano
}
```

#### Otimização com Contexto

**Sem contexto** (Chat Geral):
- Pergunta: "E hoje?" → **Sem referência**, gera erro

**Com contexto** (Projeto ativo):
- Pergunta: "E hoje?" → **Entende continuidade**, busca vendas de hoje
- SQL otimizado: `WHERE date = CURRENT_DATE` (apenas hoje)
- Resposta comparativa: "Hoje 200 vs ontem 150 (+33%)"

#### Exemplos de Uso

**Exemplo 1: Comparação automática**
```
Usuário: Vendas ontem?
Assistente: 150 vendas

Usuário: E hoje?
Assistente: 200 vendas hoje, enquanto ontem foram 150 (crescimento de 33%)
```

**Exemplo 2: Refinamento progressivo**
```
Usuário: Vendas por estado
Assistente: [Tabela com todos estados]

Usuário: Apenas SP e RJ
Assistente: [Tabela filtrada] - Refinei para mostrar apenas SP e RJ
```

---

## Persistência de Dados

### PostgreSQL Schema

#### Tabela: projects

```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    username VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(name, username)
);
```

#### Tabela: conversations

```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    message_order INTEGER NOT NULL,
    sender VARCHAR(50) NOT NULL,  -- 'user' ou 'assistant'
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ratings INTEGER CHECK (ratings BETWEEN 1 AND 5),
    metadata JSONB DEFAULT '{}',
    
    -- Parent tracking para rastreabilidade
    parent_intent_validator_id INTEGER,
    parent_plan_builder_id INTEGER,
    parent_plan_confirm_id INTEGER,
    parent_analysis_orchestrator_id INTEGER,
    parent_sql_validator_id INTEGER,
    parent_auto_correction_id INTEGER,
    parent_athena_executor_id INTEGER,
    parent_python_runtime_id INTEGER,
    parent_response_composer_id INTEGER,
    parent_user_feedback_id INTEGER,
    
    UNIQUE(project_id, message_order)
);
```

**Metadata JSONB** contém:
```json
{
    "module": "response_composer",
    "execution_time": 2.3,
    "query_sql": "SELECT ...",
    "row_count": 150,
    "intent_category": "vendas",
    "plan_confirmed": true,
    "rating": 5,
    "feedback_comment": "Ótima análise!"
}
```

#### Tabela: order_report (Dados Operacionais)

```sql
CREATE TABLE order_report (
    -- Dados desnormalizados sincronizados do Athena
    order_id VARCHAR(50),
    date DATE,
    customer_name VARCHAR(255),
    state VARCHAR(2),
    revenue DECIMAL(10,2),
    status VARCHAR(50),
    -- ... demais colunas operacionais
);
```

### Redis Schema

#### Keys e Estruturas

```
# Jobs
job:{job_id}                              String (JSON) - TTL: 3600s
job:{branch_job_id}                       String (JSON) - TTL: 3600s

# Filas (Listas)
queue:intent_validator                    List
queue:plan_builder                        List
queue:plan_confirm                        List
queue:analysis_orchestrator               List
queue:sql_validator                       List
queue:auto_correction                     List
queue:athena_executor                     List
queue:python_runtime                      List
queue:response_composer                   List
queue:user_feedback                       List
queue:history_preferences                 List
queue:user_proposed_plan                  List
queue:plan_refiner                        List

# Filas Interativas
queue:interactive_plan_confirm            List
queue:interactive_user_proposed_plan      List
queue:interactive_user_feedback           List

# Cancelamento
cancelled_jobs:{username}:{projeto}       Set

# Resposta Interativa
user_response:{job_id}                    String (JSON) - TTL: 300s
```

#### Estrutura de Job no Redis

```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "diogo",
    "projeto": "vendas_2024",
    "start_module": "intent_validator",
    "current_module": "python_runtime",
    "data": {
        "pergunta": "Vendas por estado hoje",
        "conversation_context": "--- HISTÓRICO ---...",
        "has_history": true,
        "intent_valid": true,
        "intent_category": "vendas",
        "plan": "1. Buscar vendas agrupadas por estado...",
        "plan_confirmed": true,
        "query_sql": "SELECT state, SUM(revenue)...",
        "valid": true,
        "results_full": [...],
        "row_count": 27,
        "analysis_summary": "...",
        "response_text": "..."
    },
    "execution_chain": [
        {"module": "intent_validator", "timestamp": "2025-11-29T10:30:01", "execution_time": 1.2},
        {"module": "plan_builder", "timestamp": "2025-11-29T10:30:03", "execution_time": 2.5},
        {"module": "plan_confirm", "timestamp": "2025-11-29T10:30:10", "execution_time": 7.1},
        {"module": "analysis_orchestrator", "timestamp": "2025-11-29T10:30:13", "execution_time": 3.2}
    ],
    "status": "processing",
    "created_at": "2025-11-29T10:30:00.123456",
    "parent_job_id": null
}
```

---

## Segurança

### Autenticação e Autorização

#### JWT Cookie-based

```python
@app.route('/api/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    # Validar credenciais (implementação omitida)
    if validate_credentials(username, password):
        token = jwt.encode(
            {'username': username, 'exp': datetime.utcnow() + timedelta(hours=24)},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        response = make_response({'success': True})
        response.set_cookie('token', token, httponly=True, secure=True, samesite='Strict')
        return response
    
    return {'error': 'Invalid credentials'}, 401
```

#### Middleware de Autenticação

```python
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')
        if not token:
            return {'error': 'Token missing'}, 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = data['username']
        except jwt.ExpiredSignatureError:
            return {'error': 'Token expired'}, 401
        except jwt.InvalidTokenError:
            return {'error': 'Invalid token'}, 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated
```

### Isolamento de Dados

#### Por Usuário e Projeto

Todas as queries incluem filtros de segurança:

```python
# Listar projetos - apenas do usuário autenticado
@app.route('/api/projects', methods=['GET'])
@token_required
def get_projects(current_user):
    cursor.execute("""
        SELECT * FROM projects 
        WHERE username = %s AND is_active = true
        ORDER BY updated_at DESC
    """, (current_user,))
```

```python
# Conversas - apenas do projeto do usuário
@app.route('/api/projects/<int:project_id>/conversations', methods=['GET'])
@token_required
def get_conversations(current_user, project_id):
    # Verificar ownership
    cursor.execute("SELECT username FROM projects WHERE id = %s", (project_id,))
    project = cursor.fetchone()
    if not project or project['username'] != current_user:
        return {'error': 'Unauthorized'}, 403
    
    # Buscar conversas
    cursor.execute("""
        SELECT * FROM conversations 
        WHERE project_id = %s 
        ORDER BY message_order ASC
    """, (project_id,))
```

### Validação SQL

#### Análise de Segurança (SQL Validator)

```python
def validate_security(query_sql: str) -> dict:
    """
    Valida segurança da query SQL
    """
    security_issues = []
    
    # Verificar operações perigosas
    dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'GRANT', 'REVOKE']
    for keyword in dangerous_keywords:
        if re.search(rf'\b{keyword}\b', query_sql, re.IGNORECASE):
            security_issues.append(f"Operação perigosa detectada: {keyword}")
    
    # Verificar injeção
    if re.search(r';\s*\w+', query_sql):
        security_issues.append("Possível SQL Injection: múltiplos statements")
    
    # Verificar comandos de sistema
    if re.search(r'\bSYSTEM\b|\bEXEC\b|\bxp_\w+', query_sql, re.IGNORECASE):
        security_issues.append("Comando de sistema detectado")
    
    return {
        'safe': len(security_issues) == 0,
        'security_issues': security_issues
    }
```

#### Rate Limiting

```python
# Implementar rate limiting por usuário
from functools import wraps
from flask import request

def rate_limit(max_requests=10, window=60):
    """Limita requisições por usuário"""
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            key = f"rate_limit:{current_user}"
            count = redis_client.incr(key)
            if count == 1:
                redis_client.expire(key, window)
            
            if count > max_requests:
                return {'error': 'Rate limit exceeded'}, 429
            
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator
```

### Proteção de Dados Sensíveis

#### Variáveis de Ambiente (.env)

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ezpocket_db
DB_USER=ezpocket_user
DB_PASSWORD=********

# Redis
REDIS_HOST=localhost
REDIS_PORT=6493
REDIS_DB=0

# OpenAI
OPENAI_API_KEY=sk-********

# AWS
AWS_ACCESS_KEY_ID=********
AWS_SECRET_ACCESS_KEY=********
AWS_REGION=us-east-1
AWS_ATHENA_DATABASE=receivables_db
AWS_ATHENA_OUTPUT_LOCATION=s3://ezpocket-athena-results/

# JWT
SECRET_KEY=********

# Config
BD_REFERENCE=Local  # ou Athena
NODE_ENV=production
```

#### .gitignore

```
.env
*.pyc
__pycache__/
*.log
.venv/
ezinho_assistente/
```

### Certificados SSL/TLS

#### Certbot (Let's Encrypt)

O ezpocket utiliza **Certbot** para gerenciamento automático de certificados SSL/TLS com Let's Encrypt. A instalação é feita via apt-get no Nginx, gerando certificados para os domínios principais e subdomínios. A renovação acontece automaticamente via cron job a cada 90 dias.

**Configuração Nginx com SSL** implementa TLS 1.2 e 1.3 com redirect automático de HTTP para HTTPS. Utiliza ciphers recomendados pela Mozilla (perfil Intermediate) garantindo compatibilidade com navegadores modernos. HSTS é habilitado com max-age de 1 ano, forçando HTTPS em futuras conexões. OCSP Stapling melhora performance da validação de certificados.

**Security Headers** são configurados para proteção adicional:
- X-Frame-Options: SAMEORIGIN (previne clickjacking)
- X-Content-Type-Options: nosniff (previne MIME sniffing)
- X-XSS-Protection: ativado com modo block
- Referrer-Policy: strict-origin-when-cross-origin
- Content-Security-Policy: restringe fontes de conteúdo permitidas

**Benefícios da automatização**:
- Certificados renovados automaticamente a cada 90 dias
- Zero downtime durante renovação
- Grade A+ no SSL Labs
- Suporte TLS 1.2 e 1.3

### Web Application Firewall (WAF)

#### ModSecurity + OWASP Core Rule Set

O ezpocket implementa **ModSecurity 3** com as regras OWASP CRS (Core Rule Set) para proteção contra ataques web. A instalação inclui a biblioteca libmodsecurity3 e o conector nginx-modsecurity compilado como módulo dinâmico. O OWASP CRS é clonado do repositório oficial e configurado com as regras padrão.

**Configuração ModSecurity** habilita o engine em modo ativo (SecRuleEngine On), processa corpo de requisições até 13MB, e mantém logs de auditoria em formato serial. O sistema processa XML e JSON nativamente, aplicando transformações específicas para cada tipo de conteúdo. Logging é configurado como RelevantOnly para capturar apenas eventos de segurança relevantes.

**Integração com Nginx** carrega o módulo ModSecurity dinamicamente e aplica as regras em todos os virtual hosts SSL. O arquivo de configuração principal referencia o OWASP CRS que contém milhares de regras contra ataques comuns.

#### Regras Customizadas de Proteção

**Proteção contra SQL Injection**: Utiliza o operador @detectSQLi nativo do ModSecurity para identificar patterns de SQL Injection em todos os argumentos da requisição. Quando detectado, bloqueia a requisição e registra no audit log com severidade CRITICAL.

**Proteção contra XSS**: Aplica o operador @detectXSS para detectar tentativas de Cross-Site Scripting nos parâmetros. Bloqueio imediato com log detalhado incluindo o dado que triggerou a regra.

**Rate Limiting WAF**: Implementa contador por IP usando collections do ModSecurity. Cada IP tem limite de 100 requisições por 60 segundos. Requisições excedentes são bloqueadas com severidade WARNING. O contador expira automaticamente após 1 minuto.

**Bloqueio de User-Agents maliciosos**: Mantém lista de user-agents conhecidos de ferramentas de scan e ataque (sqlmap, nikto, nmap, masscan, burpsuite, dirbuster, hydra). Requisições com estes user-agents são bloqueadas preventivamente na fase 1 do processamento.

#### OWASP Top 10 Protection

O ModSecurity + OWASP CRS protege contra:

1. **A01:2021 – Broken Access Control**: Validação de autorização em cada requisição
2. **A02:2021 – Cryptographic Failures**: TLS 1.2+ obrigatório
3. **A03:2021 – Injection**: Regras anti-SQL Injection, XSS, Command Injection
4. **A04:2021 – Insecure Design**: Rate limiting e validação de inputs
5. **A05:2021 – Security Misconfiguration**: Headers de segurança configurados
6. **A06:2021 – Vulnerable Components**: Atualizações automáticas via Dependabot
7. **A07:2021 – Authentication Failures**: JWT com expiração, rate limiting no login
8. **A08:2021 – Data Integrity Failures**: Validação de integridade de requests
9. **A09:2021 – Logging Failures**: Logs completos no ModSecurity
10. **A10:2021 – SSRF**: Bloqueio de requisições a IPs privados

#### Monitoramento WAF

**Logs do ModSecurity** são armazenados em dois arquivos principais: audit log com ataques bloqueados e suas características, e debug log com informações detalhadas do processamento de regras. Estatísticas de bloqueios podem ser extraídas filtrando por IDs de regras no audit log.

**Dashboard de Segurança** processa os logs do ModSecurity para gerar relatórios de ataques. Utiliza regex para extrair tipos de ataque (via campo msg) e IPs de origem. Gera ranking de top 10 tipos de ataques mais frequentes e top 10 IPs atacantes, permitindo identificar padrões e tomar ações preventivas como bloqueio permanente de IPs.

### Fail2Ban Integration

Proteção adicional contra ataques de força bruta implementada com **Fail2Ban**. O sistema monitora logs do Nginx e ModSecurity para detectar padrões de ataque e banir IPs automaticamente.

**Configuração nginx-modsecurity jail**: Monitora audit log do ModSecurity, permite máximo 5 tentativas em 10 minutos, aplica ban de 1 hora. Detecta acessos negados e triggers de regras customizadas (IDs 1000-1999).

**Configuração nginx-limit-req jail**: Monitora error log do Nginx para rate limiting, permite 10 tentativas em 10 minutos, ban de 1 hora. Complementa o rate limiting do próprio Nginx e do ModSecurity.

**Filtros customizados** utilizam regex para identificar linhas de log relevantes, extraindo o IP do atacante via capture group <HOST>. Padrão ignoreregex vazio garante que todos os matches sejam processados.

### Resumo de Camadas de Segurança

```
┌─────────────────────────────────────────┐
│   Usuário Final                         │
└──────────────┬──────────────────────────┘
               │ HTTPS (TLS 1.3)
┌──────────────▼──────────────────────────┐
│   Certbot (Let's Encrypt)               │
│   - Certificados SSL/TLS                │
│   - Renovação automática                │
│   - Grade A+ SSL Labs                   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│   Nginx + ModSecurity WAF               │
│   - OWASP CRS 3.3                       │
│   - Anti SQL Injection                  │
│   - Anti XSS                            │
│   - Rate Limiting                       │
│   - Bloqueio de bots                    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│   Fail2Ban                              │
│   - Ban automático de IPs maliciosos    │
│   - Proteção força bruta                │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│   Flask Application                     │
│   - JWT Authentication                  │
│   - Rate Limiting                       │
│   - SQL Validation                      │
│   - Input Sanitization                  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│   PostgreSQL / Redis                    │
│   - Isolamento por usuário              │
│   - Prepared Statements                 │
└─────────────────────────────────────────┘
```

---

## Infraestrutura e Deploy

### PM2 Configuration (ezpocket_remastered.config.js)

```javascript
module.exports = {
  apps: [
    {
      name: 'flask-app',
      script: 'python3',
      args: 'test_endpoint_websocket.py',
      cwd: '/home/servidores/ezpocket/agents/graph_orchestrator',
      instances: 8,
      exec_mode: 'cluster',
      autorestart: true,
      max_restarts: 10,
      watch: false,
      env: {
        FLASK_ENV: 'production',
        PORT: 3004
      }
    },
    {
      name: 'worker-intent-validator',
      script: 'python3',
      args: 'worker_intent_validator.py',
      cwd: '/home/servidores/ezpocket/agents/graph_orchestrator',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      max_restarts: 10
    },
    {
      name: 'worker-plan-builder',
      script: 'python3',
      args: 'worker_plan_builder.py',
      cwd: '/home/servidores/ezpocket/agents/graph_orchestrator',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      max_restarts: 10
    },
    // ... demais 11 workers
    {
      name: 'data-sync-agent',
      script: 'python3',
      args: 'data_sync_agent.py',
      cwd: '/home/servidores/ezpocket/agents/data_sync_agent',
      instances: 1,
      exec_mode: 'fork',
      cron_restart: '0 */1 * * *',  // A cada 1 hora
      autorestart: false
    }
  ]
};
```

### Nginx Configuration

```nginx
upstream flask_backend {
    server localhost:3004;
    server localhost:3005;
    server localhost:3006;
    server localhost:3007;
    server localhost:3008;
    server localhost:3009;
    server localhost:3010;
    server localhost:3011;
}

server {
    listen 80;
    server_name ezpocket.com.br;

    # Static files
    location /static/ {
        alias /home/servidores/ezpocket/agents/graph_orchestrator/static/;
        expires 30d;
    }

    # WebSocket upgrade
    location /socket.io/ {
        proxy_pass http://flask_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket timeout
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    # API endpoints
    location / {
        proxy_pass http://flask_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Comandos de Deploy

```bash
# Start all services
pm2 start production/ezpocket_remastered.config.js

# Restart specific worker
pm2 restart worker-intent-validator

# View logs
pm2 logs flask-app
pm2 logs worker-analysis-orchestrator

# Monitor
pm2 monit

# Stop all
pm2 stop all

# Delete all
pm2 delete all

# Save configuration
pm2 save

# Setup startup
pm2 startup
```

### Health Checks

```python
@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    checks = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {}
    }
    
    # Check PostgreSQL
    try:
        cursor.execute('SELECT 1')
        checks['services']['postgresql'] = 'up'
    except Exception as e:
        checks['services']['postgresql'] = 'down'
        checks['status'] = 'unhealthy'
    
    # Check Redis
    try:
        redis_client.ping()
        checks['services']['redis'] = 'up'
    except Exception as e:
        checks['services']['redis'] = 'down'
        checks['status'] = 'unhealthy'
    
    # Check workers
    active_workers = 0
    for module in ['intent_validator', 'plan_builder', 'analysis_orchestrator']:
        if redis_client.llen(f"queue:{module}") is not None:
            active_workers += 1
    
    checks['services']['workers'] = f"{active_workers}/13 queues active"
    
    status_code = 200 if checks['status'] == 'healthy' else 503
    return checks, status_code
```

---

## Escalabilidade

### Horizontal Scaling

#### Workers

**Adicionar mais workers** para um módulo específico:

```javascript
// pm2 config
{
  name: 'worker-analysis-orchestrator',
  script: 'python3',
  args: 'worker_analysis_orchestrator.py',
  instances: 3,  // Múltiplas instâncias do mesmo worker
  exec_mode: 'fork'
}
```

Vantagens:
- Processamento paralelo de jobs do mesmo tipo
- Redis `blpop` garante que cada job é processado por apenas 1 worker
- Distribuição automática de carga

#### Flask Instances

```javascript
{
  name: 'flask-app',
  instances: 16,  // Aumentar de 8 para 16
  exec_mode: 'cluster'
}
```

### Vertical Scaling

#### Redis

```bash
# redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru
```

#### PostgreSQL

```sql
-- postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
maintenance_work_mem = 64MB
max_connections = 200
```

### Load Balancing

Nginx distribui requisições entre 8 instâncias Flask:

```nginx
upstream flask_backend {
    least_conn;  # Algoritmo de menor conexão
    server localhost:3004 weight=1;
    server localhost:3005 weight=1;
    # ... demais instâncias
}
```

### Caching Strategy

#### Redis Cache

```python
def get_with_cache(key: str, fetch_func, ttl=300):
    """
    Busca do cache ou executa função
    """
    cached = redis_client.get(f"cache:{key}")
    if cached:
        return json.loads(cached)
    
    result = fetch_func()
    redis_client.setex(f"cache:{key}", ttl, json.dumps(result))
    return result

# Uso
projects = get_with_cache(
    f"projects:{username}",
    lambda: fetch_projects_from_db(username),
    ttl=600  # 10 minutos
)
```

### Bottlenecks Identificados

1. **OpenAI API**: Rate limit de 10k requests/min
   - Solução: Queue com retry e backoff exponencial
   
2. **PostgreSQL Connections**: Max 200 conexões
   - Solução: Connection pooling com pgbouncer
   
3. **Redis Memory**: Jobs com TTL 1h podem acumular
   - Solução: Monitorar `redis-cli info memory`, ajustar TTL

---

## Monitoramento e Logs

### Application Logs

#### Estrutura de Logs

Cada worker gera logs estruturados:

```python
print(f"[{self.module_name}] 🚀 Worker iniciado")
print(f"[{self.module_name}] 📍 Processando job {job_id[:8]}...")
print(f"[{self.module_name}] ✅ Job concluído em {execution_time:.2f}s")
print(f"[{self.module_name}] ❌ Erro: {error_message}")
```

#### PM2 Logs

```bash
# Ver logs em tempo real
pm2 logs

# Logs de worker específico
pm2 logs worker-analysis-orchestrator

# Últimas 100 linhas
pm2 logs --lines 100

# Logs apenas de erros
pm2 logs --err
```

#### Logs Persistidos

PM2 salva logs em:
```
~/.pm2/logs/
├── flask-app-out.log
├── flask-app-error.log
├── worker-intent-validator-out.log
├── worker-intent-validator-error.log
└── ...
```

### Métricas de Performance

#### Job Execution Time

Rastreado em `execution_chain`:

```python
execution_chain.append({
    'module': self.module_name,
    'timestamp': datetime.now().isoformat(),
    'execution_time': time.time() - start_time,
    'status': 'success'
})
```

#### Queue Depth

Monitorar tamanho das filas:

```python
@app.route('/api/metrics/queues', methods=['GET'])
def queue_metrics():
    """Retorna tamanho de cada fila"""
    metrics = {}
    for module in GRAPH_CONNECTIONS.keys():
        queue_length = redis_client.llen(f"queue:{module}")
        metrics[module] = queue_length
    return metrics
```

#### Worker Status

```bash
pm2 status

# Output:
# ┌─────┬──────────────────────────────┬─────────┬─────────┬──────────┐
# │ id  │ name                         │ status  │ ↺       │ cpu      │
# ├─────┼──────────────────────────────┼─────────┼─────────┼──────────┤
# │ 0   │ flask-app                    │ online  │ 0       │ 12%      │
# │ 1   │ worker-intent-validator      │ online  │ 0       │ 2%       │
# │ 2   │ worker-plan-builder          │ online  │ 0       │ 5%       │
# │ 3   │ worker-analysis-orchestrator │ online  │ 0       │ 8%       │
# └─────┴──────────────────────────────┴─────────┴─────────┴──────────┘
```

### Error Tracking

#### Exception Handling

```python
try:
    result = self.process(data)
except Exception as e:
    print(f"[{self.module_name}] ❌ Erro crítico: {str(e)}")
    print(f"[{self.module_name}] 📋 Traceback: {traceback.format_exc()}")
    
    # Atualizar job com erro
    job_data['status'] = 'failed'
    job_data['error'] = str(e)
    job_data['error_traceback'] = traceback.format_exc()
    redis_client.setex(f"job:{job_id}", 3600, json.dumps(job_data))
    
    # Notificar usuário via WebSocket
    socketio.emit('error', {
        'job_id': job_id,
        'module': self.module_name,
        'error': str(e)
    }, room=f"{username}:{projeto}")
```

### Alertas

Implementar alertas para:

1. **Worker Down**: PM2 detecta crash e reinicia automaticamente
2. **Queue Overflow**: Se fila > 100 jobs, enviar alerta
3. **High Error Rate**: Se > 10% jobs falhando
4. **OpenAI API Errors**: Rate limit ou timeout
5. **Database Connection Errors**: PostgreSQL ou Redis indisponíveis

---

## Comparação: Solução Atual vs. Alternativas

### ezpocket (Customizado) vs. RQ vs. Celery

| Característica | ezpocket | RQ | Celery |
|----------------|----------|-----|---------|
| **Linguagem** | Python | Python | Python |
| **Backend** | Redis customizado | Redis | Redis/RabbitMQ/SQS |
| **Complexidade** | Média | Baixa | Alta |
| **DAG Support** | ✅ Nativo | ❌ Manual | ✅ Canvas/Workflows |
| **Retry** | ❌ Manual | ✅ Automático | ✅ Automático |
| **Priorização** | ❌ Não | ✅ Sim | ✅ Sim |
| **Timeout** | ⚠️ Manual | ✅ Automático | ✅ Automático |
| **Monitoramento** | ⚠️ Logs + PM2 | ✅ rq-dashboard | ✅ Flower |
| **Escalabilidade** | ✅ Boa | ✅ Boa | ✅ Excelente |
| **Contexto Propagado** | ✅ Nativo | ⚠️ Manual | ⚠️ Manual |
| **Interatividade** | ✅ Nativo | ❌ Difícil | ❌ Difícil |
| **Learning Curve** | Média | Baixa | Alta |

### Quando Usar Cada Solução

**ezpocket (Customizado)**: 
- ✅ Fluxo DAG específico
- ✅ Contexto propagado essencial
- ✅ Interatividade (confirmações/feedback)
- ✅ Controle total necessário

**RQ**:
- ✅ Jobs simples assíncronos
- ✅ Quer dashboard visual
- ✅ Retry automático importante
- ❌ Não precisa DAG complexo

**Celery**:
- ✅ Sistema distribuído grande
- ✅ Precisa workflows avançados
- ✅ Múltiplos backends (SQS, RabbitMQ)
- ❌ Complexidade justificada

---

## Diagrama de Decisão: Escolha de Tecnologia

```
Precisa de DAG com condicionais?
├─ Não → RQ (simples e eficiente)
└─ Sim
    ├─ Contexto propagado essencial?
    │   ├─ Não → Celery Workflows
    │   └─ Sim → Solução Customizada (ezpocket)
    │
    └─ Precisa interatividade (confirmações)?
        ├─ Não → Celery Canvas
        └─ Sim → Solução Customizada (ezpocket)
```

---

## Conclusão

O ezpocket implementa uma **arquitetura de pipeline assíncrono baseado em DAG** com sistema de filas customizado sobre Redis. Esta escolha oferece:

### Vantagens

1. **Controle Total**: Lógica específica de propagação de contexto e interatividade
2. **Simplicidade**: Sem overhead de frameworks complexos
3. **Performance**: Processamento paralelo eficiente
4. **Rastreabilidade**: Parent tracking completo via parent_id chain
5. **Escalabilidade**: Workers independentes, fácil de escalar horizontalmente

### Trade-offs

1. **Manutenção**: Código customizado requer manutenção própria
2. **Features**: Sem retry automático, priorização ou timeout built-in
3. **Monitoramento**: Requer implementação própria de dashboards

### Recomendações Futuras

1. **Migração para RQ**: Se o DAG simplificar e contexto não for crítico
2. **Implementar Retry**: Adicionar lógica de retry automático nos workers
3. **Dashboard de Monitoramento**: Criar interface visual para filas e jobs
4. **Health Checks**: Expandir endpoints de health para cada worker
5. **Metrics**: Integrar Prometheus + Grafana para métricas avançadas

---

**Documento gerado em**: 29 de novembro de 2025  
**Versão**: 1.0  
**Autor**: Equipe Técnica ezpocket
