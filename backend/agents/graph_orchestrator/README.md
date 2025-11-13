# Graph Orchestrator - Sistema de Filas

Sistema de processamento assíncrono usando **Redis** como fila de mensagens.

## 🎯 Vantagens sobre HTTP

- ⚡ **Muito mais rápido** - processamento assíncrono
- 🔄 **Paralelo** - múltiplos workers processando simultaneamente
- 🛡️ **Resiliente** - jobs não se perdem se um worker cair
- 📊 **Escalável** - adicione mais workers conforme necessário

## 📁 Estrutura

```
graph_orchestrator/
├── graph_orchestrator.py        # Engine principal + classe base
├── worker_intent_validator.py   # Worker do Intent Validator
├── worker_history_preferences.py # Worker do History Preferences
├── submit_job.py                # Script para submeter jobs
└── start_workers.sh             # Helper para iniciar sistema
```

## 🔧 Configuração

### 1. Iniciar Redis

```bash
docker run -d -p 6379:6379 --name ezpocket_redis redis:alpine
```

### 2. Definir Conexões (graph_orchestrator.py)

```python
GRAPH_CONNECTIONS = {
    'intent_validator': ['history_preferences'],
    'history_preferences': [],  # Nó final
}
```

## 🚀 Uso

### Iniciar Workers

```bash
# Terminal 1 - Intent Validator Worker
cd backend/agents/graph_orchestrator
python worker_intent_validator.py

# Terminal 2 - History Preferences Worker  
python worker_history_preferences.py

# Terminal 3 - Flow Orchestration (para salvar no PostgreSQL)
cd backend/agents
python flow_orchestration.py
```

### Submeter Job

```bash
# Terminal 4
cd backend/agents/graph_orchestrator
python submit_job.py
```

Ou via código:

```python
from graph_orchestrator import submit, status

# Submeter
job_id = submit(
    start_module='intent_validator',
    username='joao',
    projeto='ezpag',
    pergunta='quantos pedidos tivemos hoje?'
)

# Consultar status
result = status(job_id)
```

## 🔄 Como Funciona

1. **Job é submetido** → vai para `queue:intent_validator`
2. **Worker Intent Validator** consome job → processa → **deposita output** em `queue:history_preferences`
3. **Worker History Preferences** consome job → processa → **job completo**
4. **Salva no PostgreSQL** via Flow Orchestration

## 📊 Visualizar Grafo

```bash
python graph_orchestrator.py viz
```

## ⚙️ Variáveis de Ambiente

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
FLOW_ORCHESTRATION_URL=http://localhost:5004
```

## 🔌 Adicionar Novo Módulo

1. Atualizar `GRAPH_CONNECTIONS`
2. Criar `worker_novo_modulo.py`:

```python
from graph_orchestrator import ModuleWorker

class NovoModuloWorker(ModuleWorker):
    def __init__(self):
        super().__init__('novo_modulo')
    
    def process(self, data):
        # Seu código aqui
        return {'resultado': '...'}

if __name__ == '__main__':
    worker = NovoModuloWorker()
    worker.start()
```

3. Iniciar worker em novo terminal

## 📈 Monitoramento

```python
from graph_orchestrator import GraphOrchestrator

orch = GraphOrchestrator()

# Ver filas
print(orch.list_queues())
# {'intent_validator': 0, 'history_preferences': 2}
```
