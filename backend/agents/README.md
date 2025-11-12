# 🔄 Arquitetura LangGraph - Ezinho Assistant

## 📁 Estrutura de Pastas

```
backend/
├── agents/                          # 🎯 Pacote de Agentes LangGraph
│   ├── __init__.py
│   ├── intent_validator_agent/     # NÓ 0: Intent Validator Agent
│   │   ├── __init__.py
│   │   └── intent_validator.py    # Valida intenção e escopo
│   ├── router_agent/               # NÓ 1: Router Agent
│   │   ├── __init__.py
│   │   └── router.py              # Detecta casos especiais + FAQ matching
│   ├── generator_agent/            # NÓ 2: Generator Agent
│   │   ├── __init__.py
│   │   └── generator.py           # Gera SQL com IA
│   └── responder_agent/            # NÓ 3: Responder Agent
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
  ↓         
[NÓ 1: ROUTER]
        ↓
   Caso especial?
   ↙️    ↓    ↘️
Reset  Ajuda  Despedida → Resposta
        ↓
   FAQ match?
   ↙️         ↘️
 SIM         NÃO
  ↓           ↓
  │    [NÓ 2: GENERATOR]
  │           ↓
  │      Gera SQL
  │           ↓
  └─────→ [NÓ 3: RESPONDER]
              ↓
         Executa SQL
              ↓
         Formata resposta
              ↓
          Resposta final
```

---

## 🎯 Descrição dos Nós

### **NÓ 0: Intent Validator Agent** (`agents/intent_validator_agent/intent_validator.py`)

**Responsabilidades:**
- ✅ Validar se a pergunta está dentro do escopo do sistema
- ✅ Classificar a categoria da intenção (análise_dados, despedida, ajuda, reset, faq, fora_escopo)
- ✅ Detectar tentativas de uso fora do domínio (perguntas pessoais, tópicos gerais)
- ✅ Gerar respostas educadas para perguntas fora do escopo
- ✅ Usar GPT-4 para validação inteligente de intenção

**Saídas:**
- `intent_valid`: true/false (se pergunta está no escopo)
- `intent_category`: "despedida" | "ajuda" | "reset" | "analise_dados" | "faq" | "fora_escopo"
- `intent_reason`: Explicação da validação
- `is_special_case`: true se for despedida/ajuda/reset detectado na validação

**Escopo Válido:**
- Análise de dados financeiros (valores, receitas, inadimplência)
- Consultas sobre pedidos, transações, clientes
- Relatórios operacionais e métricas
- Análises temporais (períodos, datas, meses)
- Informações sobre recebíveis, antecipações
- Comandos: despedidas, help, reset
- Perguntas sobre FAQ conhecidas

**Fora do Escopo:**
- Perguntas pessoais não relacionadas ao negócio
- Tópicos gerais sem relação com dados
- Conversas casuais sem objetivo analítico
- Outros domínios (receitas, esportes, etc)

---

### **NÓ 1: Router Agent** (`agents/router_agent/router.py`)

**Responsabilidades:**
- ✅ Detectar comandos especiais (`#resetar`)
- ✅ Detectar despedidas (gera resposta com IA)
- ✅ Detectar pedidos de ajuda sobre colunas
- ✅ Buscar match com FAQ (usando embeddings)
- ✅ Validar similaridade + intenção
- ✅ Decidir: usar FAQ ou gerar nova query

**Saídas:**
- `route`: "special" | "faq" | "generate"
- `sql_query`: SQL pré-aprovada (se FAQ match)
- `tipo`: "reset" | "despedida" | "help" (se caso especial)

---

### **NÓ 2: Generator Agent** (`agents/generator_agent/generator.py`)

**Responsabilidades:**
- ✅ Carregar schema das tabelas
- ✅ Carregar regras e instruções
- ✅ Usar OpenAI GPT-4 para gerar SQL
- ✅ Validar sintaxe básica
- ✅ Manter histórico de conversação

**Saídas:**
- `sql_query`: Query SQL gerada dinamicamente
- `source`: "AI_GENERATION"

---

### **NÓ 3: Responder Agent** (`agents/responder_agent/responder.py`)

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
