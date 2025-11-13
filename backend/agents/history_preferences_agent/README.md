# 🧠 History and Preferences Agent

**Context Manager / Memory Node** do sistema EzPocket LangGraph

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Estrutura](#-estrutura)
- [Funcionalidades](#-funcionalidades)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [Testes](#-testes)
- [Integração com LangGraph](#-integração-com-langgraph)
- [API Reference](#-api-reference)

---

## 🎯 Visão Geral

O **History and Preferences Agent** é responsável por:

- 📜 **Gerenciar histórico** de interações do usuário
- ⚙️ **Armazenar preferências** personalizadas
- 🔍 **Identificar padrões** de uso
- 🧠 **Fornecer contexto** para outros nós do grafo
- 📊 **Aprender automaticamente** com base no comportamento

### Posição no Grafo

```
┌─────────────────────┐
│ IntentValidator     │ (NÓ 0)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ History/Preferences │ (NÓ 1) ◄── VOCÊ ESTÁ AQUI
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Router Agent        │ (NÓ 2)
└─────────────────────┘
```

---

## 📂 Estrutura

```
history_preferences_agent/
├── __init__.py                      # Exporta HistoryPreferencesAgent
├── history_preferences.py           # Implementação principal (419 linhas)
├── roles.json                       # Configurações do agente (118 linhas)
├── test_endpoint.py                 # Servidor Flask teste (porta 5002)
├── test_client.py                   # Cliente CLI para testes
├── run_test.sh                      # Script de automação
├── test_history_preferences.py      # Testes unitários (26 testes)
└── README.md                        # Esta documentação
```

---

## ⚡ Funcionalidades

### 1. Histórico de Interações

Armazena todas as interações do usuário:

```python
{
  "pergunta": "Quantos pedidos tivemos hoje?",
  "intent_category": "quantidade",
  "interaction_type": "query",
  "metadata": {
    "sql_query": "SELECT COUNT(*) FROM orders WHERE date = today()",
    "execution_time": 0.5
  },
  "timestamp": "2025-11-12 14:30:00"
}
```

### 2. Preferências Personalizadas

4 categorias de preferências:

| Categoria         | Descrição                      | Opções Principais                                |
| ----------------- | ------------------------------ | ------------------------------------------------ |
| **visualization** | Como usuário prefere ver dados | `chart_type`, `color_scheme`, `detail_level`     |
| **analysis**      | Tipo de análise preferida      | `time_period`, `comparison`, `metrics_priority`  |
| **reporting**     | Formato de relatórios          | `format`, `include_recommendations`, `verbosity` |
| **communication** | Estilo de comunicação          | `tone`, `language_style`, `use_emojis`           |

### 3. Padrões Identificados

Detecta automaticamente:
- 📅 Horários de pico de uso
- 📊 Métricas favoritas
- 🎯 Complexidade das queries
- 🔄 Tópicos recorrentes

### 4. Aprendizado Automático

Configurable em `roles.json`:

```json
"learning_rules": {
  "auto_learn_preferences": true,
  "min_interactions_for_pattern": 5,
  "confidence_threshold": 0.7,
  "update_strategy": "incremental"
}
```

---

## 🔧 Configuração

### roles.json

Arquivo de configuração centralizado:

```json
{
  "module_info": {
    "name": "History and Preferences Agent",
    "node_id": "history_preferences",
    "version": "1.0.0"
  },
  "memory_configuration": {
    "max_history_items": 50,
    "history_retention_days": 90
  },
  "preference_types": { ... },
  "learning_rules": { ... }
}
```

### Banco de Dados

3 tabelas SQLite (`backend/database/user_context.db`):

1. **interaction_history** - Histórico de interações
2. **user_preferences** - Preferências do usuário
3. **user_patterns** - Padrões identificados

---

## 🚀 Uso

### 1. No LangGraph

```python
from agents.history_preferences_agent import HistoryPreferencesAgent

agent = HistoryPreferencesAgent()

# Carregar contexto
state = agent.load_context({
    "username": "joao_silva",
    "projeto": "ezpag",
    "pergunta": "Quantos pedidos tivemos?"
})

# Salvar interação
agent.save_interaction({
    "username": "joao_silva",
    "projeto": "ezpag",
    "pergunta": "Quantos pedidos tivemos?",
    "intent_category": "quantidade"
})
```

### 2. API Direta

```python
# Obter preferências
prefs = agent.get_preferences("joao_silva", "ezpag")

# Atualizar preferências
agent.update_preferences(
    username="joao_silva",
    projeto="ezpag",
    category="visualization",
    preferences={"chart_type": "bar"},
    confidence=1.0
)
```

---

## 🧪 Testes

### Setup de Dois Terminais

```bash
# Terminal 1: Iniciar servidor de teste
cd backend/agents/history_preferences_agent
./run_test.sh server

# Terminal 2: Rodar testes
./run_test.sh interactive  # Modo interativo
./run_test.sh examples     # Exemplos predefinidos
./run_test.sh health       # Verificar servidor
```

### Modos do run_test.sh

```bash
./run_test.sh server      # Inicia servidor (porta 5002)
./run_test.sh health      # Verifica health
./run_test.sh interactive # Modo interativo
./run_test.sh examples    # Roda 5 exemplos
./run_test.sh test <user> <proj> <pergunta> [cat]  # Teste específico
./run_test.sh clean       # Limpa banco de dados
```

### Cliente Python

```bash
# Health check
python3 test_client.py health

# Modo interativo
python3 test_client.py interactive

# Salvar interação
python3 test_client.py save joao_silva ezpag "Quantos pedidos?" quantidade

# Carregar contexto
python3 test_client.py load joao_silva ezpag

# Ver histórico
python3 test_client.py history joao_silva ezpag 10

# Ver preferências
python3 test_client.py preferences joao_silva ezpag
```

### Testes Unitários

```bash
# Rodar todos os testes
python3 -m pytest test_history_preferences.py -v

# ou com unittest
python3 test_history_preferences.py

# Cobertura: 26 testes
# - Inicialização: 3 testes
# - Load Context: 3 testes
# - Save Interaction: 3 testes
# - Preferences: 6 testes
# - Patterns: 1 teste
# - Métodos auxiliares: 4 testes
# - Edge cases: 3 testes
# - Integração: 3 testes
```

---

## 🔗 Integração com LangGraph

### Estado do Grafo

Campos adicionados ao `GraphState`:

```python
class GraphState(TypedDict):
    # ... campos existentes ...
    
    # Novos campos do History/Preferences
    user_context: Dict          # Contexto completo do usuário
    has_user_context: bool      # Se tem contexto disponível
    interaction_saved: bool     # Se interação foi salva
```

### Integração no ezinho_graph.py

```python
from agents.history_preferences_agent import HistoryPreferencesAgent

# Criar agente
history_agent = HistoryPreferencesAgent()

# Adicionar ao grafo
graph_builder.add_node("history_preferences", history_agent.load_context)

# Conectar após IntentValidator
graph_builder.add_edge("intent_validator", "history_preferences")
graph_builder.add_edge("history_preferences", "router")

# No final do fluxo, salvar interação
graph_builder.add_node("save_interaction", history_agent.save_interaction)
```

### Exemplo de Fluxo Completo

```python
# 1. Usuário faz pergunta
input_state = {
    "username": "joao_silva",
    "projeto": "ezpag",
    "pergunta": "Quantos pedidos tivemos hoje?"
}

# 2. IntentValidator valida
# state["intent_category"] = "quantidade"

# 3. History carrega contexto
# state["user_context"] = {...histórico e preferências...}
# state["has_user_context"] = True

# 4. Router usa contexto para decisão
# 5. Generator gera SQL
# 6. Responder responde

# 7. No final, salva interação
history_agent.save_interaction(final_state)
```

---

## 📚 API Reference

### HistoryPreferencesAgent

#### Métodos Principais

##### `load_context(state: Dict) -> Dict`

Carrega histórico e preferências do usuário.

**Parâmetros:**
- `state`: Estado do grafo com `username`, `projeto`, `pergunta`

**Retorna:**
- Estado atualizado com:
  - `user_context`: Contexto completo
  - `has_user_context`: bool

**Exemplo:**
```python
state = agent.load_context({
    "username": "joao",
    "projeto": "ezpag",
    "pergunta": "Pergunta aqui"
})

print(state["user_context"]["recent_history"])
print(state["user_context"]["preferences"])
```

##### `save_interaction(state: Dict) -> Dict`

Salva interação atual no histórico.

**Parâmetros:**
- `state`: Estado do grafo com dados da interação

**Retorna:**
- Estado atualizado com `interaction_saved: bool`

**Exemplo:**
```python
state = agent.save_interaction({
    "username": "joao",
    "projeto": "ezpag",
    "pergunta": "Quantos pedidos?",
    "intent_category": "quantidade",
    "sql_query": "SELECT COUNT(*) FROM orders",
    "response": "150 pedidos"
})
```

##### `get_preferences(username: str, projeto: str) -> Dict`

Obtém preferências do usuário.

**Retorna:**
```python
{
  "visualization": {
    "chart_type": {"value": "bar", "confidence": 1.0},
    "color_scheme": {"value": "corporate", "confidence": 0.8}
  },
  "analysis": { ... }
}
```

##### `update_preferences(username, projeto, category, preferences, confidence) -> bool`

Atualiza preferências do usuário.

**Parâmetros:**
- `username`: Nome do usuário
- `projeto`: Nome do projeto
- `category`: Categoria (`visualization`, `analysis`, `reporting`, `communication`)
- `preferences`: Dict com preferências
- `confidence`: Confiança (0.0 a 1.0)

**Exemplo:**
```python
success = agent.update_preferences(
    username="joao",
    projeto="ezpag",
    category="visualization",
    preferences={
        "chart_type": "line",
        "color_scheme": "blue"
    },
    confidence=1.0
)
```

#### Métodos Privados

- `_get_recent_history(username, projeto, limit)` - Obtém histórico recente
- `_get_user_preferences(username, projeto)` - Obtém preferências
- `_get_user_patterns(username, projeto)` - Obtém padrões
- `_map_category_to_interaction(category)` - Mapeia categoria para tipo
- `_extract_metadata(state)` - Extrai metadata do estado
- `_auto_learn_preferences(username, projeto, state)` - Aprendizado automático

---

## 🎨 Beautiful Logs

O agente usa prints formatados com emojis:

```
================================================================================
🧠 HISTORY AND PREFERENCES AGENT - LOAD CONTEXT
================================================================================

📥 INPUTS:
  • Username: joao_silva
  • Projeto: ezpag

⚙️  PROCESSAMENTO:
  ✓ Carregando histórico recente...
    → 5 interações encontradas
  ✓ Carregando preferências do usuário...
    → 3 preferências carregadas
  ✓ Identificando padrões de uso...
    → 2 padrões identificados
  ✓ Construindo contexto personalizado...

📤 OUTPUT:
  • Has Context: True
  • History Items: 5
  • Preferences: 3
  • Patterns: 2
================================================================================
```

---

## 🔐 Isolamento de Dados

- Cada usuário tem contexto separado
- Dados isolados por (username, projeto)
- Histórico mantido por 90 dias (configurável)
- Máximo 50 itens no histórico recente (configurável)

---

## 🛠️ Manutenção

### Limpeza de Dados Antigos

```python
# Implementar rotina de limpeza periódica
def clean_old_data(days=90):
    """Remove interações antigas"""
    # SQL: DELETE FROM interaction_history WHERE timestamp < NOW() - INTERVAL days DAYS
```

### Backup do Banco

```bash
# Backup
cp backend/database/user_context.db backup/user_context_$(date +%Y%m%d).db

# Restore
cp backup/user_context_20251112.db backend/database/user_context.db
```

---

## 📈 Métricas

Informações disponíveis:

- Total de interações por usuário
- Tópicos mais consultados
- Preferências mais comuns
- Taxa de aprendizado automático
- Tempo médio de resposta

---

## 🚧 Próximos Passos

- [ ] Implementar limpeza automática de dados antigos
- [ ] Adicionar cache para contextos frequentes
- [ ] Melhorar algoritmo de aprendizado
- [ ] Adicionar exportação de relatórios
- [ ] Implementar analytics dashboard

---

## 📞 Suporte

Para problemas ou dúvidas:

1. Verifique os logs com prints formatados
2. Rode os testes unitários
3. Use `./run_test.sh health` para verificar servidor
4. Consulte este README

---

**Desenvolvido com ❤️ para o sistema EzPocket**
