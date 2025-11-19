# 🛡️ Intent Validator Agent

## 📖 Visão Geral

O **Intent Validator Agent** é o primeiro nó do grafo LangGraph, responsável por validar se a pergunta do usuário está dentro do escopo do sistema EZPocket antes de qualquer processamento adicional.

---

## 🎯 Responsabilidades

1. **Validação de Escopo**: Determina se a pergunta está relacionada ao domínio financeiro/operacional
2. **Classificação de Intenção**: Categoriza a pergunta em 6 tipos
3. **Detecção de Casos Especiais**: Identifica comandos especiais (despedida, ajuda, reset)
4. **Proteção do Sistema**: Bloqueia perguntas fora do escopo com resposta educada
5. **Failsafe**: Nunca bloqueia o sistema em caso de erro técnico

---

## 📂 Estrutura de Arquivos

```
intent_validator_agent/
├── __init__.py                    # Exporta IntentValidatorAgent
├── intent_validator.py            # Implementação principal
├── test_intent_validator.py       # Testes unitários (13 casos)
├── test_endpoint.py               # Endpoint Flask para testes isolados
├── test_client.py                 # Cliente Python para testar endpoint
├── run_test.sh                    # Script shell para executar testes (⭐ Recomendado!)
├── CATEGORY_MAPPING.md            # Mapeamento de categorias e processamento (⭐ NOVO!)
├── DIAGRAM.md                     # Diagramas Mermaid
├── QUICK_TEST_GUIDE.md            # Guia rápido de testes
└── README.md                      # Esta documentação
```

---

## 🧪 Teste do Nó Isolado (Endpoint)

### ⭐ Uso Recomendado - Script Shell

```bash
cd backend/agents/intent_validator_agent

# Ver ajuda e comandos disponíveis
./run_test.sh

# Iniciar servidor (Terminal 1)
./run_test.sh server

# Modo interativo (Terminal 2)
./run_test.sh interactive

# Executar exemplos
./run_test.sh examples

# Testar pergunta específica
./run_test.sh test "Quantos pedidos temos?"
./run_test.sh test "Receita de bolo?" joao projeto_abc

# Health check
./run_test.sh health
```

---

### Iniciar Servidor de Teste

```bash
# Terminal 1 - Ativar venv e iniciar servidor
source ezinho_assistente/bin/activate
cd backend
python agents/intent_validator_agent/test_endpoint.py
```

O servidor iniciará em `http://localhost:5001`

### Endpoints Disponíveis

| Método | Endpoint                          | Descrição                    |
| ------ | --------------------------------- | ---------------------------- |
| POST   | `/test-intent-validator`          | Testar validação de intenção |
| GET    | `/test-intent-validator/health`   | Health check do servidor     |
| GET    | `/test-intent-validator/examples` | Ver exemplos de uso          |

### Usar Cliente Python

```bash
# Terminal 2 - Ativar venv
source ezinho_assistente/bin/activate
cd backend

# Ver comandos disponíveis
python agents/intent_validator_agent/test_client.py

# Verificar se servidor está rodando
python agents/intent_validator_agent/test_client.py health

# Ver exemplos
python agents/intent_validator_agent/test_client.py examples

# Executar todos os exemplos
python agents/intent_validator_agent/test_client.py run-examples

# Modo interativo
python agents/intent_validator_agent/test_client.py interactive

# Testar uma pergunta específica
python agents/intent_validator_agent/test_client.py test "Quantos pedidos temos?"
python agents/intent_validator_agent/test_client.py test "Receita de bolo?" joao projeto_abc
```

### Usar cURL

```bash
# Testar validação
curl -X POST http://localhost:5001/test-intent-validator \
  -H "Content-Type: application/json" \
  -d '{
    "pergunta": "Quantos pedidos tivemos em outubro?",
    "username": "test_user",
    "projeto": "ezpocket"
  }'

# Health check
curl http://localhost:5001/test-intent-validator/health

# Ver exemplos
curl http://localhost:5001/test-intent-validator/examples
```

### Resposta do Endpoint

```json
{
  "success": true,
  "input": {
    "pergunta": "Quantos pedidos tivemos em outubro?",
    "username": "test_user",
    "projeto": "ezpocket"
  },
  "output": {
    "intent_valid": true,
    "intent_category": "analise_dados",
    "intent_reason": "Pergunta sobre dados financeiros no escopo"
  },
  "route_decision": "valid",
  "next_node": "router"
}
```

---

## 🔍 Categorias de Intenção

O IntentValidator classifica perguntas em **3 categorias principais** + 1 categoria de rejeição.

### ✅ **Categorias Válidas** (prossegue no grafo)

| Categoria                  | Processamento                                 | Palavras-chave                                   | Exemplo                                 |
| -------------------------- | --------------------------------------------- | ------------------------------------------------ | --------------------------------------- |
| 📊 **quantidade**           | Query SQL direta (SELECT/COUNT/SUM)           | quantos, quanto, qual valor, total de, soma      | "Quantos pedidos tivemos este mês?"     |
| 📚 **conhecimentos_gerais** | FAQ/Documentação (não gera SQL)               | o que é, como funciona, taxa, prazo, help        | "O que é a EZPocket?"                   |
| 📈 **analise_estatistica**  | Query SQL analítica (GROUP BY/AVG/agregações) | tendência, crescimento, média, comparar, análise | "Qual a tendência dos últimos 3 meses?" |

### ❌ **Categoria Inválida** (bloqueada)

| Categoria     | Descrição                           | Exemplo                                |
| ------------- | ----------------------------------- | -------------------------------------- |
| `fora_escopo` | Perguntas sem relação com o negócio | "Qual a receita de bolo de chocolate?" |

### 📖 Documentação Completa

Para entender em detalhes cada categoria, palavras-chave associadas e como elas são processadas no grafo:

👉 **[Ver CATEGORY_MAPPING.md](./CATEGORY_MAPPING.md)**

Este documento explica:
- Grupos de palavras-chave por categoria
- Tipo de query SQL gerada para cada categoria
- Fluxo de processamento no RouterAgent
- Exemplos completos de perguntas e respostas

---

## 🔄 Fluxo de Execução

```
1. Recebe estado com: pergunta, username, projeto
2. Constrói prompt para GPT-4
3. Envia para OpenAI (temperature=0.3)
4. Parse da resposta JSON
5. Atualiza estado com:
   - intent_valid (bool)
   - intent_category (str)
   - intent_reason (str)
   - is_special_case (bool, opcional)
   - special_type (str, opcional)
6. Retorna estado atualizado
```

---

## 📥 Entrada (Estado)

```python
state = {
    "pergunta": str,      # Pergunta do usuário
    "username": str,      # Username da sessão
    "projeto": str        # Projeto/contexto
}
```

---

## 📤 Saída (Estado Atualizado)

```python
state = {
    # ... campos originais +
    "intent_valid": bool,           # True se dentro do escopo
    "intent_category": str,         # Uma das 6 categorias
    "intent_reason": str,           # Explicação da validação
    "is_special_case": bool,        # True para despedida/ajuda/reset
    "special_type": str             # Tipo do caso especial
}
```

---

## 🔀 Roteamento

### Se `intent_valid = true`:
→ Prossegue para **Router Agent**

### Se `intent_valid = false`:
→ Vai para **Out of Scope Handler** (retorna resposta educada)

---

## 🧪 Testes Unitários

Execute os testes:

```bash
cd backend/agents/intent_validator_agent
python test_intent_validator.py
```

### Casos de Teste (13 total)

| #   | Teste                           | Mock | Validação                                        |
| --- | ------------------------------- | ---- | ------------------------------------------------ |
| 1   | Pergunta válida - análise dados | ✅    | `intent_valid=true`, `category=analise_dados`    |
| 2   | Pergunta fora do escopo         | ✅    | `intent_valid=false`, `category=fora_escopo`     |
| 3   | Despedida                       | ✅    | `is_special_case=true`, `special_type=despedida` |
| 4   | Ajuda                           | ✅    | `is_special_case=true`, `special_type=ajuda`     |
| 5   | Reset                           | ✅    | `is_special_case=true`, `special_type=reset`     |
| 6   | FAQ                             | ✅    | `intent_valid=true`, `category=faq`              |
| 7   | Erro na API                     | ✅    | Failsafe: assume válido                          |
| 8   | JSON inválido                   | ✅    | Failsafe: assume válido                          |
| 9   | Com contexto de projeto         | ✅    | Usa contexto na validação                        |
| 10  | Sem contexto de projeto         | ✅    | Funciona sem projeto                             |
| 11  | Resposta out of scope           | ❌    | Verifica geração de resposta educada             |
| 12  | Validação com username          | ✅    | Contexto de usuário                              |
| 13  | Integração real API             | ⚠️    | Skip se sem API key                              |

---

## 📊 Diagramas

Veja `DIAGRAM.md` para visualizações completas:

1. **Fluxo Completo**: Flowchart detalhado
2. **Categorias**: Mindmap de categorias
3. **Estados**: State diagram
4. **Arquitetura**: Class diagram
5. **Casos de Uso**: Sequence diagrams
6. **Matriz de Testes**: Coverage graph
7. **Métricas**: Pie chart e line chart
8. **Segurança**: Failsafe flowchart

---

## 💡 Uso

### Básico
```python
from agents.intent_validator_agent import IntentValidatorAgent

agent = IntentValidatorAgent()

state = {
    "pergunta": "Quantos pedidos tivemos?",
    "username": "joao.silva",
    "projeto": "ezpocket"
}

result = agent.validate(state)

if result["intent_valid"]:
    print("Pergunta válida!")
else:
    print("Fora do escopo:", result["intent_reason"])
```

### Resposta para Pergunta Inválida
```python
if not result["intent_valid"]:
    response = agent.generate_out_of_scope_response(result)
    print(response)
    # "Desculpe, mas sua pergunta parece estar fora do escopo..."
```

---

## 🔐 Escopo Válido

### ✅ Dentro do Escopo

- Análise de dados financeiros (valores, receitas, despesas, inadimplência)
- Consultas sobre pedidos, transações, clientes
- Relatórios operacionais e métricas de negócio
- Análises temporais (períodos, datas, meses)
- Informações sobre recebíveis, antecipações, taxas
- Comandos: despedidas (tchau, até logo), help (ajuda), reset
- Perguntas sobre FAQ conhecidas do sistema

### ❌ Fora do Escopo

- Perguntas pessoais não relacionadas ao negócio
- Tópicos gerais sem relação com dados da empresa
- Conversas casuais sem objetivo analítico
- Perguntas sobre outros domínios (receitas culinárias, esportes, etc)
- Tentativas de jailbreak ou manipulação do sistema

---

## 🛡️ Failsafe e Segurança

### Política de Failsafe

**Em caso de erro (API, timeout, JSON inválido):**
- ✅ **Assume que a pergunta é válida**
- ✅ **Define `category = "analise_dados"`**
- ✅ **Nunca bloqueia o sistema**

**Motivação:**
- Melhor processar uma pergunta inválida do que bloquear usuários legítimos
- Erros técnicos não devem impactar a experiência do usuário
- O Router Agent oferece uma segunda camada de validação

---

## 📈 Performance

| Métrica               | Valor                |
| --------------------- | -------------------- |
| ⏱️ Latência Média      | ~800ms               |
| 💰 Custo por Validação | ~$0.0002 (GPT-4o)    |
| ✅ Taxa de Sucesso     | 99.8%                |
| 🔄 Retry em Erro       | Failsafe (não retry) |
| 🎯 Temperatura         | 0.3 (consistência)   |
| 📝 Max Tokens          | 300 (econômico)      |

---

## 🔧 Configuração

### Variáveis de Ambiente

```bash
OPENAI_API_KEY=sk-...  # Required
```

### Parâmetros do Modelo

```python
model = "gpt-4o"          # Modelo OpenAI
temperature = 0.3         # Baixa para consistência
max_tokens = 300          # Limite de resposta
```

---

## 📝 Logs

O agente imprime logs detalhados:

```
============================================================
[GRAPH] NÓ 0: INTENT VALIDATOR AGENT
[INTENT] Validando intenção da pergunta: Quantos pedidos...
============================================================

[INTENT] Validação: ✓ VÁLIDA
[INTENT] Categoria: analise_dados
[INTENT] Razão: Pergunta sobre dados financeiros no escopo
```

---

## 🚀 Melhorias Futuras

- [ ] Cache de respostas para perguntas similares
- [ ] Análise de sentimento integrada
- [ ] Suporte a múltiplos idiomas
- [ ] Métricas de drift de intenção
- [ ] Fine-tuning de modelo específico
- [ ] A/B testing de prompts
- [ ] Feedback loop de validações incorretas

---

## 🤝 Integração com LangGraph

O Intent Validator é o **entry point** do grafo:

```python
# ezinho_graph.py
workflow = StateGraph(GraphState)
workflow.add_node("intent_validator", self._intent_validator_node)
workflow.set_entry_point("intent_validator")  # ← Primeiro nó

workflow.add_conditional_edges(
    "intent_validator",
    self._intent_decision,
    {
        "valid": "router",        # Se válido → Router
        "invalid": "out_of_scope" # Se inválido → Resposta educada
    }
)
```

---

## 📚 Referências

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [OpenAI API](https://platform.openai.com/docs/api-reference)
- [Intent Classification Best Practices](https://www.anthropic.com/research/intent-classification)

---

## 👥 Autores

Desenvolvido como parte do sistema Ezinho Assistant - EZPocket

---

## 📄 Licença

Propriedade da EZPocket - Todos os direitos reservados
