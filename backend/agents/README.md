# 🔄 Arquitetura LangGraph - Ezinho Assistant

## 📁 Estrutura de Pastas

```
backend/
├── agents/                          # 🎯 Pacote de Agentes LangGraph
│   ├── __init__.py
│   ├── intent_validator_agent/     # NÓ 0: Intent Validator Agent
│   │   ├── __init__.py
│   │   ├── intent_validator.py    # Valida intenção e escopo
│   │   ├── roles.json             # Configurações de categorias
│   │   ├── test_endpoint.py       # Endpoint de teste (porta 5001)
│   │   ├── test_client.py         # Cliente CLI
│   │   ├── run_test.sh            # Script de automação
│   │   ├── test_intent_validator.py  # Testes unitários
│   │   └── README.md              # Documentação completa
│   ├── history_preferences_agent/  # NÓ 1: History & Preferences Agent
│   │   ├── __init__.py
│   │   ├── history_preferences.py # Context Manager / Memory
│   │   ├── roles.json             # Configurações de memória
│   │   ├── test_endpoint.py       # Endpoint de teste (porta 5002)
│   │   ├── test_client.py         # Cliente CLI
│   │   ├── run_test.sh            # Script de automação
│   │   ├── test_history_preferences.py  # Testes unitários
│   │   └── README.md              # Documentação completa
│   ├── router_agent/               # NÓ 2: Router Agent
│   │   ├── __init__.py
│   │   └── router.py              # Detecta casos especiais + FAQ matching
│   ├── generator_agent/            # NÓ 3: Generator Agent
│   │   ├── __init__.py
│   │   └── generator.py           # Gera SQL com IA
│   └── responder_agent/            # NÓ 4: Responder Agent
│       ├── __init__.py
│       └── responder.py           # Executa SQL + formata resposta
│
├── ezinho_graph.py                 # 🔀 Orquestrador LangGraph
├── ezinho_assistant.py
└── main.py                         # 🌐 Aplicação Flask (usa ezinho_graph)
```

---

## 🔀 Fluxo do Grafo LangGraph

```
Pergunta do usuário
        ↓
[NÓ 0: INTENT VALIDATOR]
        ↓
  Valida escopo
    ↙️     ↘️
VÁLIDO   INVÁLIDO
  ↓         ↓
  │    "Fora do escopo"
  ↓         ↓
[NÓ 1: HISTORY/PREFERENCES]  [SAVE & END]
        ↓
 Carrega contexto
    (histórico + preferências)
        ↓
[NÓ 2: ROUTER]
        ↓
   Caso especial?
   ↙️    ↓    ↘️
Reset  Ajuda  Despedida → Resposta → [SAVE & END]
        ↓
   FAQ match?
   ↙️         ↘️
 SIM         NÃO
  ↓           ↓
  │    [NÓ 3: GENERATOR]
  │           ↓
  │      Gera SQL
  │      (usa contexto)
  │           ↓
  └─────→ [NÓ 4: RESPONDER]
              ↓
         Executa SQL
              ↓
    Formata resposta
    (aplica preferências)
              ↓
         Resposta final
              ↓
      [SAVE INTERACTION]
              ↓
             END
```

---

## 🎯 Descrição dos Nós

### **NÓ 0: Intent Validator Agent** (`agents/intent_validator_agent/intent_validator.py`)

**Responsabilidades:**
- ✅ Validar se a pergunta está dentro do escopo do sistema
- ✅ Classificar em 3 categorias: quantidade, conhecimentos_gerais, analise_estatistica
- ✅ Detectar tentativas de uso fora do domínio
- ✅ Proteger dados sensíveis (CPF, RG, senhas, etc)
- ✅ Gerar respostas educadas para perguntas fora do escopo
- ✅ Usar GPT-4o para validação inteligente

**Saídas:**
- `intent_valid`: true/false (se pergunta está no escopo)
- `intent_category`: "quantidade" | "conhecimentos_gerais" | "analise_estatistica" | "fora_escopo"
- `intent_reason`: Explicação da validação

**Porta de Teste:** 5001  
**Documentação:** `intent_validator_agent/README.md`

---

### **NÓ 1: History & Preferences Agent** (`agents/history_preferences_agent/history_preferences.py`)

**Responsabilidades:**
- 📜 Gerenciar histórico de interações do usuário
- ⚙️ Armazenar e recuperar preferências personalizadas
- 🔍 Identificar padrões de uso
- 🧠 Fornecer contexto para outros nós do grafo
- 📊 Aprender automaticamente com base no comportamento
- 💾 Persistir dados em SQLite (user_context.db)

**Saídas:**
- `user_context`: Dict com histórico, preferências e padrões
- `has_user_context`: true/false
- `interaction_saved`: true/false (ao final)

**Banco de Dados:**
- `interaction_history`: Histórico de perguntas e respostas
- `user_preferences`: Preferências de visualização, análise, reporting
- `user_patterns`: Padrões identificados automaticamente

**Preferências Suportadas:**
- 📊 **visualization**: tipo de gráfico, esquema de cores, nível de detalhe
- 📈 **analysis**: período temporal, comparações, métricas prioritárias
- 📄 **reporting**: formato, recomendações, verbosidade
- 💬 **communication**: tom, estilo de linguagem, uso de emojis

**Porta de Teste:** 5002  
**Documentação:** `history_preferences_agent/README.md`

---

### **NÓ 2: Router Agent** (`agents/router_agent/router.py`)

**Responsabilidades:**
- ✅ Detectar comandos especiais (`#resetar`)
- ✅ Detectar despedidas (gera resposta com IA)
- ✅ Detectar pedidos de ajuda sobre colunas
- ✅ Buscar match com FAQ (usando embeddings)
- ✅ Validar similaridade + intenção
- ✅ Decidir: usar FAQ ou gerar nova query
- ✅ Usar contexto do usuário para melhor roteamento

**Saídas:**
- `route`: "special" | "faq" | "generate"
- `sql_query`: SQL pré-aprovada (se FAQ match)
- `tipo`: "reset" | "despedida" | "help" (se caso especial)

---

### **NÓ 3: Generator Agent** (`agents/generator_agent/generator.py`)

**Responsabilidades:**
- ✅ Carregar schema das tabelas
- ✅ Carregar regras e instruções
- ✅ Usar OpenAI GPT-4 para gerar SQL
- ✅ Validar sintaxe básica
- ✅ Manter histórico de conversação
- ✅ Adaptar SQL baseado nas preferências do usuário (via contexto)

**Saídas:**
- `sql_query`: Query SQL gerada dinamicamente
- `source`: "AI_GENERATION"

---

### **NÓ 4: Responder Agent** (`agents/responder_agent/responder.py`)

**Responsabilidades:**
- ✅ Executar SQL no Amazon Athena
- ✅ Formatar valores monetários (adiciona $)
- ✅ Extrair contexto temporal (datas da pergunta)
- ✅ Usar OpenAI GPT-4 para gerar resposta natural
- ✅ Formatar query para exibição legível

**Saídas:**
- `resposta_final`: Resposta formatada e natural
- `query`: SQL formatada para exibição
- `source`: Origem + status (ex: "FAQ_MATCH_SUCCESS")

---

## 🚀 Como Usar

### **No código (main.py):**

```python
from ezinho_graph import get_ezinho_graph

# Obtém instância do grafo (singleton)
ezinho_graph = get_ezinho_graph()

# Processa pergunta
resultado = ezinho_graph.invoke("Quantas vendas tivemos hoje?")

# Acessa resposta
print(resultado['resposta'])  # Resposta natural
print(resultado['query'])     # SQL executada
print(resultado['source'])    # Origem (FAQ_MATCH ou AI_GENERATION)
```

### **Função de compatibilidade:**

```python
from ezinho_graph import responder

# Mantém compatibilidade com código legado
resultado = responder("Quantas vendas tivemos hoje?")
```

---

## 🔧 Manutenção

### **Adicionar nova lógica no Router:**
Edite: `agents/router_agent/router.py` → método `route()`

### **Modificar geração de SQL:**
Edite: `agents/generator_agent/generator.py` → método `generate()`

### **Alterar formatação de resposta:**
Edite: `agents/responder_agent/responder.py` → método `respond()`

### **Modificar fluxo do grafo:**
Edite: `ezinho_graph.py` → método `_build_graph()`

---

## 📊 Logs de Execução

O sistema imprime logs detalhados de cada etapa:

```
============================================================
[GRAPH] 🚀 INICIANDO PROCESSAMENTO
[GRAPH] Pergunta: Quantas vendas tivemos hoje?
============================================================

============================================================
[GRAPH] NÓ 1: ROUTER AGENT
============================================================
[ROUTER] Buscando FAQ match para: 'Quantas vendas tivemos hoje?'
[ROUTER] ✅ FAQ Match encontrado! Similaridade: 0.8234
[GRAPH] 🔀 Roteamento: faq

============================================================
[GRAPH] NÓ 3: RESPONDER AGENT
============================================================
[RESPONDER] 🔄 Executando SQL e formatando resposta
[RESPONDER] 📄 Query formatada:
    SELECT COUNT(*) as total_vendas
    FROM receivables_db.report_orders
    WHERE DATE(date_order_created) = CURRENT_DATE
[RESPONDER] ✅ Resposta gerada com sucesso

============================================================
[GRAPH] ✅ PROCESSAMENTO CONCLUÍDO
[GRAPH] Source: FAQ_MATCH_SUCCESS
============================================================
```

---

## ✅ Vantagens da Arquitetura

1. **Modular**: Cada nó é independente e testável
2. **Observável**: Logs claros em cada etapa
3. **Extensível**: Fácil adicionar novos nós
4. **Manutenível**: Código organizado por responsabilidade
5. **Debugável**: Pode inspecionar estado entre nós
6. **Compatível**: Mantém função legada `responder()`

---

## 🔄 Migração Completa

**Antes:**
```python
from ezinho_assistant import EzinhoAssistant
assistant = EzinhoAssistant()
resultado = assistant.responder(pergunta)
```

**Depois:**
```python
from ezinho_graph import get_ezinho_graph
graph = get_ezinho_graph()
resultado = graph.invoke(pergunta)
```

**Funcionalidade:** 100% mantida ✅
