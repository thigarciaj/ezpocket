# Response Composer Agent 🎨

Agente especializado em **formatação de respostas bonitas e amigáveis** para usuários de negócios.

## 🎯 Propósito

Transforma análises técnicas e dados brutos do **Python Runtime Agent** em respostas elegantes, visuais e fáceis de entender, usando:
- ✨ Markdown formatado
- 🎨 Emojis contextuais
- 📊 Estrutura hierárquica
- 💡 Linguagem de negócio clara

## 🔄 Posição no Fluxo

```
Python Runtime (análise técnica) 
    ↓
Response Composer (formatação bonita)
    ↓
History Preferences (salva resposta)
    ↓
Usuário final (recebe resposta amigável)
```

## 📥 Input (do Python Runtime)

```json
{
  "pergunta": "Quantas vendas tivemos ontem?",
  "username": "joao.silva",
  "projeto": "retail_analytics",
  "analysis_summary": "Foram registradas 150 vendas...",
  "statistics": {
    "total": 150,
    "media_diaria": 120,
    "variacao": "+25%"
  },
  "insights": [...],
  "recommendations": [...],
  "visualizations": [...]
}
```

## 📤 Output (para History e Usuário)

```json
{
  "response_text": "## 🎯 Resposta Direta\n\nOntem tivemos **150 vendas**...",
  "response_summary": "Ontem tivemos 150 vendas, 25% acima da média.",
  "key_numbers": ["150", "120", "25%"],
  "formatting_style": "markdown_with_emojis",
  "user_friendly_score": 9.5,
  "tokens_used": 450,
  "model_used": "gpt-4o",
  "error": null
}
```

## 🎨 Estrutura da Resposta

### 1. 🎯 Resposta Direta
- Responde imediatamente à pergunta
- Destaca o número principal em **negrito**
- Usa emoji contextual

### 2. 📊 Análise Detalhada
- Apresenta estatísticas de forma organizada
- Usa listas e tabelas para clareza
- Compara com benchmarks (média, meta, etc)

### 3. 💡 Principais Insights
- Lista 3-5 descobertas importantes
- Explica o impacto de negócio
- Ordena por relevância

### 4. 🎯 Recomendações
- Sugere ações práticas
- Indica prioridade (alta/média/baixa)
- Menciona impacto esperado

### 5. 📈 Visualizações Sugeridas
- Recomenda gráficos adequados
- Explica por que cada visualização é útil

## 🚀 Como Usar

### Teste Rápido

```bash
python agents/response_composer_agent/response_composer.py
```

### Integração com Worker

```python
from agents.response_composer_agent.response_composer import ResponseComposerAgent

agent = ResponseComposerAgent()

state = {
    'pergunta': 'Quantas vendas tivemos ontem?',
    'username': 'test_user',
    'analysis_summary': '...',
    'statistics': {...},
    'insights': [...],
    'recommendations': [...],
    'visualizations': [...]
}

result = agent.execute(state)
print(result['response_text'])  # Resposta formatada em Markdown
```

## 🎭 Características

### ✨ Formatação Rica
- Markdown completo (títulos, listas, negrito, etc)
- Emojis contextuais para guiar a leitura
- Estrutura hierárquica clara

### 💬 Linguagem de Negócio
- Evita jargão técnico
- Usa termos de negócio claros
- Tom profissional mas amigável

### 📊 Visual e Organizado
- Informação em blocos lógicos
- Ordem de importância (mais relevante primeiro)
- Fácil scanning e leitura rápida

### 🎯 Acionável
- Insights práticos
- Recomendações claras
- Próximos passos sugeridos

## 🔧 Configuração

### Variáveis de Ambiente

```bash
OPENAI_API_KEY=sk-...        # Obrigatório
LLM_MODEL=gpt-4o              # Opcional (default: gpt-4o)
```

### Modelo GPT

- **Temperatura**: 0.7 (mais criativo para respostas bonitas)
- **Formato**: JSON estruturado
- **Response Format**: `{"type": "json_object"}`

## 📊 Métricas

- **tokens_used**: Tokens consumidos na formatação
- **user_friendly_score**: Score 0-10 de amigabilidade
- **execution_time**: Tempo de processamento
- **formatting_style**: Estilo aplicado

## 🧪 Testes

```bash
# Teste unitário do agente
python agents/response_composer_agent/response_composer.py

# Teste com dados reais
python agents/response_composer_agent/test_client.py

# Teste do endpoint
python agents/response_composer_agent/test_endpoint.py
```

## 📝 Exemplo Real

**Input (dados técnicos):**
```json
{
  "analysis_summary": "150 vendas registradas",
  "statistics": {"total": 150, "media": 120},
  "insights": [{"title": "Volume alto", "impact": "alto"}]
}
```

**Output (resposta bonita):**
```markdown
## 🎯 Resposta Direta

Ontem tivemos **150 vendas**, um resultado **25% acima** da média diária!

## 📊 Análise Detalhada

- **Total de vendas**: 150
- **Média diária**: 120 vendas
- **Variação**: +25% 📈

## 💡 Principal Insight

✨ **Desempenho excepcional**: O volume de 150 vendas representa 
um dos melhores dias do mês, indicando momentum positivo.

## 🎯 Recomendação

- **Investigar fatores de sucesso**: Identificar o que contribuiu 
para este resultado para replicar em outros dias.
```

## 🎓 Diretrizes de Qualidade

### ✅ Boas Práticas
- Responder diretamente à pergunta no topo
- Usar emojis de forma consistente (não exagerar)
- Destacar números principais em negrito
- Manter parágrafos curtos e escaneáveis
- Linguagem ativa e positiva

### ❌ Evitar
- Jargão técnico desnecessário
- Textos muito longos sem estrutura
- Informações redundantes
- Tom muito formal ou robótico
- Excesso de emojis

## 🔗 Integração

### Entrada (Python Runtime)
```
Python Runtime → analysis_summary, statistics, insights, recommendations
```

### Saída (History Preferences)
```
Response Composer → response_text, response_summary, key_numbers
```

### Banco de Dados
```sql
response_composer_logs (
  id, username, projeto, pergunta,
  response_text, response_summary, key_numbers,
  user_friendly_score, execution_time, tokens_used
)
```

## 📈 Performance

- **Latência média**: ~2-3 segundos (GPT-4o)
- **Tokens médios**: 400-600 tokens
- **Success rate**: >99%
- **User satisfaction**: ~9.5/10

## 🆘 Troubleshooting

### Erro: OpenAI API Key não configurada
```bash
export OPENAI_API_KEY=sk-...
```

### Resposta vazia
- Verificar se `analysis_summary` e `statistics` estão presentes
- Conferir logs do GPT-4o para erros de API

### Score baixo de user-friendliness
- Revisar qualidade do prompt
- Verificar se emojis e formatação estão presentes

## 📚 Referências

- [roles.json](./roles.json) - Definições e exemplos
- [response_composer.py](./response_composer.py) - Implementação
- [worker_response_composer.py](../graph_orchestrator/worker_response_composer.py) - Worker

---

**Desenvolvido para transformar dados em histórias que inspiram ação** ✨
