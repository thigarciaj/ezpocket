# Plan Confirm Agent 📋✅

Agente responsável por solicitar confirmação do usuário sobre o plano de execução gerado pelo PlanBuilderAgent.

## 🎯 Responsabilidades

- ✅ Apresentar o plano de execução de forma clara e estruturada
- 🔍 Destacar os principais passos e recursos que serão utilizados
- 📊 Mostrar complexidade estimada e fontes de dados
- 👤 Solicitar confirmação explícita do usuário
- ✋ Permitir aceite ou rejeição do plano proposto
- 💬 Fornecer feedback sobre a decisão do usuário

## 🔧 Configurações

- **Modelo**: GPT-4o
- **Temperature**: 0.3
- **Porta**: 5010
- **Queue**: `queue:plan_confirm`
- **Database**: ❌ NÃO salva no banco (apenas imprime no console)

## 📥 Input

### Campos Obrigatórios
- `pergunta` (string): Pergunta original do usuário
- `plan` (string): Plano de execução gerado

### Campos Opcionais
- `username` (string): Nome do usuário
- `projeto` (string): Nome do projeto
- `intent_category` (string): Categoria da intenção
- `plan_steps` (list[string]): Lista de passos do plano
- `estimated_complexity` (string): Complexidade estimada (baixa/média/alta)
- `data_sources` (list[string]): Fontes de dados que serão consultadas
- `output_format` (string): Formato de saída esperado

## 📤 Output

```json
{
  "plan_confirmed": true,
  "confirmation_message": "Plano confirmado. Prosseguindo com a execução...",
  "user_feedback": null,
  "execution_time": 0.123,
  "model_used": "gpt-4o"
}
```

### Campos de Saída
- `plan_confirmed` (boolean): Se o usuário confirmou o plano
- `confirmation_message` (string): Mensagem de confirmação ou rejeição
- `user_feedback` (string | null): Feedback adicional do usuário
- `execution_time` (float): Tempo de execução em segundos
- `model_used` (string): Modelo LLM utilizado

## 🔄 Fluxo de Execução

```
┌─────────────────┐
│ PlanBuilder     │
│ (gera plano)    │
└────────┬────────┘
         │
         ├──────────────────┬─────────────────────┐
         │                  │                     │
         v                  v                     v
┌────────────────┐  ┌──────────────┐   ┌────────────────┐
│ PlanConfirm    │  │ History      │   │ (outros nós)   │
│ (solicita OK)  │  │ Preferences  │   │                │
└────────────────┘  └──────────────┘   └────────────────┘
         │
         │ (NÃO salva no DB)
         │
         v
   [Console Output]
```

## 🧪 Como Testar

### 1. Iniciar Servidor de Teste

```bash
./run_test.sh server
```

Inicia servidor Flask na porta 5010.

### 2. Modo Interativo

```bash
./run_test.sh interactive
```

Permite testar perguntas e planos interativamente.

### 3. Executar Exemplos

```bash
./run_test.sh examples
```

Executa exemplos pré-definidos.

### 4. Teste Unitário

```bash
./run_test.sh test
```

Executa teste unitário do agente.

## 📚 Exemplos

### Exemplo 1: Confirmar Plano de Contagem

**Input:**
```json
{
  "pergunta": "Quantos pedidos tivemos este mês?",
  "plan": "Consultar tabela report_orders filtrando por data >= início do mês atual",
  "plan_steps": [
    "1. Identificar data de início do mês atual",
    "2. Consultar tabela report_orders",
    "3. Filtrar por created_at >= início do mês",
    "4. Contar número de pedidos",
    "5. Retornar resultado"
  ],
  "estimated_complexity": "baixa",
  "data_sources": ["report_orders"],
  "output_format": "Número simples com unidade"
}
```

**Output:**
```json
{
  "plan_confirmed": true,
  "confirmation_message": "Plano confirmado. Prosseguindo com a execução...",
  "user_feedback": null,
  "execution_time": 0.234,
  "model_used": "gpt-4o"
}
```

### Exemplo 2: Confirmar Plano de Soma

**Input:**
```json
{
  "pergunta": "Qual o valor total de receita em outubro?",
  "plan": "Somar valores da coluna amount na tabela report_orders para outubro",
  "plan_steps": [
    "1. Filtrar pedidos de outubro",
    "2. Somar coluna amount",
    "3. Formatar valor em reais"
  ],
  "estimated_complexity": "baixa",
  "data_sources": ["report_orders"],
  "output_format": "Valor monetário em R$"
}
```

**Output:**
```json
{
  "plan_confirmed": true,
  "confirmation_message": "Plano confirmado. Executando consulta...",
  "user_feedback": null,
  "execution_time": 0.189,
  "model_used": "gpt-4o"
}
```

## 📋 Formato de Display

O agente apresenta o plano no seguinte formato:

```
[PLAN_CONFIRM] 📋 Plano de Execução Gerado
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❓ Pergunta:
   Quantos pedidos tivemos este mês?

📝 Resumo do Plano:
   Consultar tabela report_orders filtrando por data >= início do mês atual

📊 Passos de Execução:
   1. Identificar data de início do mês atual
   2. Consultar tabela report_orders
   3. Filtrar por created_at >= início do mês
   4. Contar número de pedidos
   5. Retornar resultado

⚡ Complexidade Estimada: baixa

🗄️ Fontes de Dados: report_orders

📤 Formato de Saída: Número simples com unidade

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Confirmação: Deseja prosseguir com este plano?
```

## ⚠️ Importante

- ❌ **NÃO salva dados no banco de dados**
- 📺 Apenas imprime o resultado no console
- 🔄 Roda em paralelo com `history_preferences`
- ✅ Modo teste confirma automaticamente
- 🎯 É um nó terminal (não conecta a outros nós)

## 🔗 Integração

### Recebe de:
- `plan_builder` - Plano de execução gerado

### Roda em paralelo com:
- `history_preferences` - Salvamento de contexto

### Envia para:
- Nenhum (nó terminal)

## 📝 Arquivos

```
plan_confirm_agent/
├── __init__.py              # Inicialização do módulo
├── plan_confirm.py          # Agente principal
├── roles.json               # Regras e configurações
├── run_test.sh              # Script de teste (executável)
├── test_endpoint.py         # Endpoint Flask (porta 5010)
├── test_client.py           # Cliente de teste
├── test_plan_confirm.py     # Teste unitário
└── README.md                # Esta documentação
```

## 🚀 Comandos Rápidos

```bash
# Ver ajuda
./run_test.sh help

# Iniciar servidor
./run_test.sh server

# Teste interativo
./run_test.sh interactive

# Executar exemplos
./run_test.sh examples

# Teste unitário
./run_test.sh test
```

## 📊 Endpoints HTTP

### POST /test-plan-confirm
Testa confirmação de plano

### GET /health
Health check do agente

### GET /info
Informações sobre o agente
