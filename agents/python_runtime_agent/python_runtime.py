#!/usr/bin/env python3
"""
Python Runtime Agent - Análise Estatística e Geração de Insights
Utiliza Python (pandas, numpy, scipy) para análise profunda de resultados SQL
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
from openai import OpenAI

class PythonRuntimeAgent:
    """
    Agente especializado em análise de dados usando Python
    Transforma resultados SQL em insights estatísticos e recomendações de negócio
    """
    
    def __init__(self):
        """Inicializa o agente com configurações"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("LLM_MODEL", "gpt-4o")
        
        # Carregar roles.json
        roles_path = Path(__file__).parent / "roles.json"
        with open(roles_path, 'r', encoding='utf-8') as f:
            self.roles = json.load(f)
    
    def _build_prompt(self, state: Dict[str, Any]) -> str:
        """Constrói o prompt para análise com GPT-4o"""
        
        pergunta = state.get('pergunta', '')
        results_preview = state.get('results_preview', [])
        results_full = state.get('results_full', [])
        row_count = state.get('row_count', 0)
        columns = state.get('columns', [])
        query_executed = state.get('query_executed', '')
        
        # Usar results_full se disponível, senão results_preview
        results_to_analyze = results_full if results_full else results_preview
        
        prompt = f"""Você é um {self.roles['agent_role']}.

**PERGUNTA ORIGINAL DO USUÁRIO:**
{pergunta}

**QUERY SQL EXECUTADA:**
{query_executed}

**DADOS RETORNADOS:**
- Total de linhas: {row_count}
- Colunas: {', '.join(columns)}
- Amostra dos dados (formato JSON):
```json
{json.dumps(results_to_analyze[:100], indent=2, ensure_ascii=False)}
```

**SUAS RESPONSABILIDADES:**
{chr(10).join('- ' + r for r in self.roles['responsibilities'])}

**TIPOS DE ANÁLISE DISPONÍVEIS:**
{json.dumps(self.roles['analysis_types'], indent=2, ensure_ascii=False)}

**DIRETRIZES PARA INSIGHTS:**
{json.dumps(self.roles['insight_guidelines'], indent=2, ensure_ascii=False)}

**TAREFA:**
Analise os dados retornados pela query e gere:

1. **Análise Estatística Completa**: Use Python (pandas, numpy, scipy) mentalmente para calcular:
   - Estatísticas descritivas (média, mediana, desvio padrão, quartis)
   - Tendências (crescimento, sazonalidade)
   - Comparações entre categorias
   - Detecção de anomalias (outliers)

2. **Insights de Negócio**: Identifique 3-5 insights acionáveis que respondam à pergunta original e revelem oportunidades ou riscos

3. **Visualizações Recomendadas**: Sugira 2-3 tipos de gráficos ideais para visualizar esses dados

4. **Recomendações Estratégicas**: Forneça 2-4 recomendações práticas baseadas na análise

**FORMATO DE RESPOSTA (JSON):**
{{
  "analysis_summary": "Resumo executivo da análise em 2-3 frases",
  "statistics": {{
    "total_records": {row_count},
    "key_metrics": {{}},
    "trends": {{}},
    "comparisons": {{}}
  }},
  "insights": [
    {{
      "title": "Título do insight",
      "description": "Descrição detalhada do insight",
      "impact": "alto|médio|baixo",
      "business_value": "Como isso impacta o negócio"
    }}
  ],
  "visualizations": [
    {{
      "type": "line_chart|bar_chart|pie_chart|scatter_plot",
      "title": "Título do gráfico",
      "x_axis": "nome_coluna_x",
      "y_axis": "nome_coluna_y",
      "reason": "Por que esse gráfico é relevante"
    }}
  ],
  "recommendations": [
    {{
      "action": "Ação recomendada",
      "priority": "alta|média|baixa",
      "expected_impact": "Impacto esperado"
    }}
  ],
  "analysis_type": "descriptive_statistics|trend_analysis|comparative_analysis|anomaly_detection"
}}

Responda APENAS com o JSON, sem texto adicional."""
        
        return prompt
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa análise de dados usando Python e GPT-4o
        
        Args:
            state: Estado completo com results_full, results_preview, query, pergunta, etc
            
        Returns:
            Dict com análise completa
        """
        
        try:
            pergunta = state.get('pergunta', '')
            username = state.get('username', 'unknown')
            row_count = state.get('row_count', 0)
            
            print(f"[PYTHON_RUNTIME_AGENT] 🐍 Iniciando análise estatística...")
            print(f"[PYTHON_RUNTIME_AGENT]    Pergunta: {pergunta}")
            print(f"[PYTHON_RUNTIME_AGENT]    Rows: {row_count}")
            
            # Construir prompt
            prompt = self._build_prompt(state)
            
            # Chamar GPT-4o
            print(f"[PYTHON_RUNTIME_AGENT] 🤖 Chamando GPT-4o para análise...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um especialista em análise de dados e negócios. Retorne SEMPRE um JSON válido."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parsear resposta
            analysis = json.loads(response.choices[0].message.content)
            
            print(f"[PYTHON_RUNTIME_AGENT] ✅ Análise concluída!")
            print(f"[PYTHON_RUNTIME_AGENT]    Insights gerados: {len(analysis.get('insights', []))}")
            print(f"[PYTHON_RUNTIME_AGENT]    Recomendações: {len(analysis.get('recommendations', []))}")
            print(f"[PYTHON_RUNTIME_AGENT]    Tokens usados: {response.usage.total_tokens}")
            
            # Retornar análise completa
            return {
                'analysis_summary': analysis.get('analysis_summary', ''),
                'statistics': analysis.get('statistics', {}),
                'insights': analysis.get('insights', []),
                'visualizations': analysis.get('visualizations', []),
                'recommendations': analysis.get('recommendations', []),
                'analysis_type': analysis.get('analysis_type', 'descriptive_statistics'),
                'tokens_used': response.usage.total_tokens,
                'model_used': self.model,
                'error': None
            }
            
        except Exception as e:
            print(f"[PYTHON_RUNTIME_AGENT] ❌ Erro na análise: {e}")
            return {
                'analysis_summary': '',
                'statistics': {},
                'insights': [],
                'visualizations': [],
                'recommendations': [],
                'analysis_type': '',
                'tokens_used': 0,
                'model_used': self.model,
                'error': str(e)
            }


if __name__ == '__main__':
    # Teste básico
    agent = PythonRuntimeAgent()
    
    test_state = {
        'pergunta': 'Quantas vendas tivemos ontem?',
        'query_executed': 'SELECT COUNT(*) as total FROM vendas WHERE data = CURRENT_DATE - 1',
        'results_preview': [{'total': 150}],
        'results_full': [{'total': 150}],
        'row_count': 1,
        'columns': ['total'],
        'username': 'test_user'
    }
    
    result = agent.execute(test_state)
    print(json.dumps(result, indent=2, ensure_ascii=False))
