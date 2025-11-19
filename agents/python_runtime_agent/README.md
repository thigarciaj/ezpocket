# Python Runtime Agent

## 🐍 Visão Geral
Agente responsável por executar análises estatísticas sobre os resultados das queries SQL, gerando insights, estatísticas e recomendações usando Python.

## 🎯 Funcionalidade Principal
Recebe resultados de queries do Athena Executor e aplica análise estatística com Python para:
- Calcular métricas descritivas (média, mediana, desvio padrão)
- Identificar tendências e padrões
- Detectar anomalias e outliers
- Gerar insights acionáveis
- Sugerir visualizações apropriadas
- Fornecer recomendações baseadas em dados

## 📊 Tipos de Análise

### 1. Estatísticas Descritivas
- Total, soma, contagem
- Média, mediana, moda
- Desvio padrão, variância
- Mínimo, máximo, amplitude
- Quartis e percentis

### 2. Análise de Tendências
- Taxa de crescimento
- Direção da tendência
- Sazonalidade
- Média móvel

### 3. Análise Comparativa
- Diferença percentual
- Razões e proporções
- Rankings
- Distribuições

### 4. Detecção de Anomalias
- Identificação de outliers
- Z-score
- Método IQR

## 📥 Input Esperado
```python
state = {
    'pergunta': 'Quantas vendas tivemos ontem?',
    'username': 'usuario',
    'projeto': 'projeto1',
    'query_results': {
        'success': True,
        'row_count': 10,
        'column_count': 3,
        'columns': ['data', 'vendas', 'valor'],
        'results_full': [...],
        'results_preview': [...],
        'results_message': '...'
    }
}
```

## 📤 Output Gerado
```python
{
    'success': True,
    'has_analysis': True,
    'analysis_summary': 'Resumo executivo da análise',
    'statistics': {
        'total': 100,
        'media': 50.5,
        'mediana': 48,
        'desvio_padrao': 12.3
    },
    'insights': [
        'Insight 1: ...',
        'Insight 2: ...'
    ],
    'visualizations': [
        'Gráfico de linha para tendência temporal',
        'Box plot para visualizar distribuição'
    ],
    'recommendations': [
        'Recomendação 1',
        'Recomendação 2'
    ],
    'python_code': 'import pandas as pd\n...'
}
```

## 🚀 Como Usar

### Modo Standalone
```bash
python python_runtime.py
```

### Integrado no Grafo
```python
from agents.python_runtime_agent import PythonRuntimeAgent

agent = PythonRuntimeAgent()
result = agent.analyze(state)
```

## 🧪 Testes

### Teste Básico
```bash
python python_runtime.py
```

### Teste com Servidor
```bash
./run_test.sh
```

### Teste Interativo
```bash
./run_test.sh interactive
```

## 📋 Estrutura de Arquivos
```
python_runtime_agent/
├── __init__.py              # Exports do módulo
├── python_runtime.py        # Implementação principal
├── roles.json               # Regras e configurações
├── README.md                # Esta documentação
├── run_test.sh              # Script de teste
└── test_endpoint.py         # Servidor Flask para testes
```

## 🔧 Configuração
O agente usa as seguintes variáveis de ambiente:
- `OPENAI_API_KEY`: Chave da API OpenAI (obrigatória)
- `PYTHON_RUNTIME_PORT`: Porta do servidor (padrão: 5018)

## 💡 Exemplos de Uso

### Exemplo 1: Análise de Vendas
**Input:** "Quantas vendas tivemos nos últimos 7 dias?"
**Output:** 
- Total: 349 vendas
- Média: 49.9 vendas/dia
- Insight: Pico no dia 16 (61 vendas, 22% acima da média)
- Recomendação: Investigar fatores do dia 16 para replicação

### Exemplo 2: Valor Médio
**Input:** "Qual o valor médio dos pedidos?"
**Output:**
- Valor médio: R$ 1.250,50
- Insight: Análise limitada - necessário distribuição completa
- Recomendação: Solicitar dados segmentados por categoria

## 🔗 Integração no Fluxo
Este agente é executado **após** o Athena Executor e **antes** de retornar ao usuário:

```
User → Intent Validator → Plan Builder → ... → Athena Executor 
    → Python Runtime → History/Response → User
```

## 📝 Notas Importantes
- Sempre verifica qualidade dos dados antes de analisar
- Menciona quando amostra é pequena demais para conclusões
- Evita forçar insights quando dados são simples/diretos
- Transparente sobre limitações e suposições
- Foca em insights acionáveis para negócio
