# User Feedback Agent

## 📊 Visão Geral

O **User Feedback Agent** captura e processa avaliações dos usuários sobre as respostas fornecidas pelo sistema EZPocket. Este agente NÃO usa IA - apenas estrutura e analisa o feedback recebido.

## 🎯 Funcionalidades

### Captura de Feedback
- **Rating**: Avaliação de 1-5 estrelas
- **Comentários**: Feedback textual opcional
- **Útil/Não Útil**: Indicador binário de utilidade
- **Qualidade**: Classificação (poor/fair/good/very_good/excellent)
- **Satisfação**: Nível de satisfação do usuário
- **Recomendação**: Se recomendaria o sistema
- **Tags**: Marcadores de aspectos (accurate, fast, clear, incomplete, wrong)

### Análise Automática
- **Sentiment Analysis**: Classificação automática de sentiment (very_positive → very_negative)
- **Aspectos Positivos**: Identifica pontos fortes mencionados
- **Áreas de Melhoria**: Identifica problemas relatados
- **Resumo**: Geração automática de resumo do feedback

## 📋 Input/Output

### Input
```python
{
    'pergunta': 'Pergunta original do usuário',
    'username': 'nome_usuario',
    'projeto': 'nome_projeto',
    'response_text': 'Resposta apresentada ao usuário',
    'rating': 5,  # 1-5
    'comment': 'Resposta excelente e clara!',
    'is_helpful': True,
    'response_quality': 'excellent',
    'user_satisfaction': 'very_satisfied',
    'would_recommend': True,
    'feedback_tags': ['accurate', 'fast', 'clear']
}
```

### Output
```python
{
    'feedback_recorded': True,
    'rating': 5,
    'comment': 'Resposta excelente e clara!',
    'is_helpful': True,
    'response_quality': 'excellent',
    'user_satisfaction': 'very_satisfied',
    'would_recommend': True,
    'feedback_tags': ['accurate', 'fast', 'clear'],
    'feedback_summary': 'Avaliação: 5/5 | Útil: Sim | Qualidade: Excelente',
    'positive_aspects': ['accurate', 'fast', 'clear'],
    'improvement_areas': [],
    'sentiment': 'very_positive',
    'feedback_date': '2025-11-19T10:30:00',
    'error': None
}
```

## 🔄 Fluxo de Execução

1. **Recebe feedback** do usuário (via API/interface)
2. **Valida dados** (rating 1-5, campos obrigatórios)
3. **Classifica tags** em positivas/negativas
4. **Calcula sentiment** baseado em rating, helpful, recommendation
5. **Gera resumo** textual do feedback
6. **Retorna estruturado** para salvar no banco via History Preferences

## 📊 Classificação de Sentiment

### Algoritmo de Score
```
Score = 0

Rating >= 4: +3 pontos
Rating == 3: +1 ponto
Rating <= 2: -2 pontos

is_helpful = True: +2 pontos
is_helpful = False: -1 ponto

would_recommend = True: +2 pontos
would_recommend = False: -1 ponto
```

### Classificação Final
- **very_positive**: score >= 5
- **positive**: score >= 2
- **neutral**: score >= -1
- **negative**: score >= -3
- **very_negative**: score < -3

## 🏷️ Tags Disponíveis

### Positivas
- `accurate` - Informação precisa/correta
- `fast` - Resposta rápida
- `clear` - Fácil de entender
- `helpful` - Útil para resolver o problema
- `complete` - Completa, sem faltar informação
- `easy_to_understand` - Linguagem clara

### Negativas
- `incomplete` - Falta informação
- `wrong` - Informação incorreta
- `slow` - Resposta demorada
- `confusing` - Difícil de entender
- `unclear` - Linguagem confusa
- `not_helpful` - Não ajudou a resolver

## 🗄️ Banco de Dados

### Tabela: `user_feedback_logs`

```sql
- id: UUID
- execution_sequence: 11
- parent_response_composer_id: UUID (FK)
- parent_python_runtime_id: UUID (FK)
- username, projeto, pergunta
- response_text: Resposta avaliada
- rating: 1-5
- comment: Texto do comentário
- is_helpful: Boolean
- response_quality: varchar
- user_satisfaction: varchar
- would_recommend: Boolean
- feedback_tags: array
- feedback_summary: Resumo
- positive_aspects: array
- improvement_areas: array
- sentiment: varchar
- metadata: JSONB
```

## 🧪 Testes

### Teste Básico
```bash
cd agents/user_feedback_agent
python user_feedback.py
```

### Teste com Redis
```bash
# Terminal 1: Iniciar worker
bash run_test.sh server

# Terminal 2: Executar teste
bash run_test.sh interactive
```

## 📈 Uso no Fluxo

```
Response Composer → User Feedback → History Preferences
```

O agente é chamado **opcionalmente** após o Response Composer quando o usuário fornece feedback sobre a resposta recebida.

## 🎯 Casos de Uso

1. **Avaliação de Qualidade**: Medir satisfação com respostas
2. **Identificação de Problemas**: Detectar respostas incorretas/incompletas
3. **Melhoria Contínua**: Coletar dados para melhorar sistema
4. **Analytics**: Gerar métricas de satisfação do usuário
5. **A/B Testing**: Comparar versões diferentes de respostas

## 📝 Exemplos

### Feedback Positivo
```python
{
    'rating': 5,
    'is_helpful': True,
    'would_recommend': True,
    'feedback_tags': ['accurate', 'fast', 'clear'],
    'comment': 'Perfeito! Respondeu exatamente o que eu precisava.'
}
# Resultado: sentiment = 'very_positive'
```

### Feedback Negativo
```python
{
    'rating': 2,
    'is_helpful': False,
    'would_recommend': False,
    'feedback_tags': ['incomplete', 'wrong'],
    'comment': 'A resposta está incorreta, faltou considerar os dados filtrados.'
}
# Resultado: sentiment = 'very_negative'
```

### Feedback Neutro
```python
{
    'rating': 3,
    'is_helpful': True,
    'would_recommend': False,
    'feedback_tags': ['slow'],
    'comment': 'A resposta está correta mas demorou muito.'
}
# Resultado: sentiment = 'neutral'
```

## 🔧 Manutenção

### Adicionar Nova Tag
Editar `user_feedback.py`:
```python
self.positive_tags = {'accurate', 'fast', 'clear', 'NEW_TAG'}
self.negative_tags = {'incomplete', 'wrong', 'NEW_TAG'}
```

### Ajustar Algoritmo de Sentiment
Modificar `_calculate_sentiment()` para alterar pesos ou thresholds.

## 📊 Métricas Recomendadas

- **NPS (Net Promoter Score)**: % would_recommend
- **CSAT (Customer Satisfaction)**: Média de rating
- **Helpfulness Rate**: % is_helpful = True
- **Tag Frequency**: Tags mais mencionadas
- **Sentiment Distribution**: Distribuição de sentiments

## 🚀 Próximos Passos

1. Dashboard de visualização de feedbacks
2. Alertas para feedbacks muito negativos
3. Machine Learning para prever satisfação
4. Análise de texto dos comentários com NLP
5. Comparação de performance entre versões
