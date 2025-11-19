#!/usr/bin/env python3
"""
Response Composer Agent - Formatação de Respostas Bonitas
Transforma dados técnicos em respostas elegantes e amigáveis para o usuário
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List
from openai import OpenAI

class ResponseComposerAgent:
    """
    Agente responsável por compor respostas bonitas e amigáveis
    Transforma análises técnicas do Python Runtime em texto humanizado
    """
    
    def __init__(self):
        """Inicializa o agente com configurações"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("LLM_MODEL", "gpt-4o")
    
    def _build_prompt(self, state: Dict[str, Any]) -> str:
        """Constrói o prompt para formatação da resposta"""
        
        pergunta = state.get('pergunta', '')
        analysis_summary = state.get('analysis_summary', '')
        statistics = state.get('statistics', {})
        insights = state.get('insights', [])
        recommendations = state.get('recommendations', [])
        visualizations = state.get('visualizations', [])
        row_count = state.get('row_count', 0)
        
        prompt = f"""Você é um assistente especializado em criar respostas elegantes e amigáveis para usuários de negócios.

**PERGUNTA ORIGINAL DO USUÁRIO:**
{pergunta}

**ANÁLISE TÉCNICA DISPONÍVEL:**

📊 **Resumo da Análise:**
{analysis_summary}

📈 **Estatísticas:**
```json
{json.dumps(statistics, indent=2, ensure_ascii=False)}
```

💡 **Insights Gerados ({len(insights)}):**
```json
{json.dumps(insights, indent=2, ensure_ascii=False)}
```

🎯 **Recomendações ({len(recommendations)}):**
```json
{json.dumps(recommendations, indent=2, ensure_ascii=False)}
```

📉 **Visualizações Sugeridas ({len(visualizations)}):**
```json
{json.dumps(visualizations, indent=2, ensure_ascii=False)}
```

**DADOS BRUTOS:**
- Total de registros: {row_count}

---

**SUA TAREFA:**

Componha uma resposta BONITA e AMIGÁVEL para o usuário que:

1. **Responda diretamente à pergunta** com os números principais em destaque
2. **Use emojis apropriados** para tornar a resposta mais visual e agradável
3. **Organize as informações hierarquicamente** (do mais importante ao detalhe)
4. **Use formatação Markdown** para deixar a resposta estruturada e fácil de ler
5. **Destaque os insights principais** que podem impactar decisões de negócio
6. **Apresente recomendações de forma acionável** (o que fazer com essas informações)
7. **Sugira visualizações relevantes** se aplicável
8. **Use linguagem de negócio**, evitando termos muito técnicos

**ESTRUTURA RECOMENDADA:**

```markdown
## 🎯 Resposta Direta
[Responda a pergunta de forma clara e direta, destacando o número principal]

## 📊 Análise Detalhada
[Apresente as estatísticas de forma visual e organizada]

## 💡 Principais Insights
[Liste os 3-5 insights mais relevantes com impacto de negócio]

## 🎯 Recomendações
[Liste ações práticas baseadas na análise]

## 📈 Visualizações Sugeridas
[Sugira gráficos que ajudariam a entender melhor os dados]
```

**FORMATO DE RESPOSTA (JSON):**
{{
  "response_text": "Resposta completa em Markdown formatado",
  "response_summary": "Resumo de 1-2 frases da resposta",
  "key_numbers": ["número1", "número2", "número3"],
  "formatting_style": "markdown_with_emojis",
  "user_friendly_score": 9.5
}}

Responda APENAS com o JSON, sem texto adicional."""
        
        return prompt
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa composição da resposta formatada
        
        Args:
            state: Estado completo com análise do Python Runtime
            
        Returns:
            Dict com resposta formatada
        """
        
        try:
            pergunta = state.get('pergunta', '')
            username = state.get('username', 'unknown')
            
            print(f"[RESPONSE_COMPOSER_AGENT] 🎨 Iniciando composição de resposta...")
            print(f"[RESPONSE_COMPOSER_AGENT]    Pergunta: {pergunta}")
            print(f"[RESPONSE_COMPOSER_AGENT]    Username: {username}")
            
            # Construir prompt
            prompt = self._build_prompt(state)
            
            # Chamar GPT-4o
            print(f"[RESPONSE_COMPOSER_AGENT] 🤖 Chamando GPT-4o para formatar resposta...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um especialista em comunicação de negócios. Crie respostas elegantes, amigáveis e visualmente agradáveis. Retorne SEMPRE um JSON válido."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,  # Mais criativo para respostas bonitas
                response_format={"type": "json_object"}
            )
            
            # Parsear resposta
            composed = json.loads(response.choices[0].message.content)
            
            print(f"[RESPONSE_COMPOSER_AGENT] ✅ Resposta composta!")
            print(f"[RESPONSE_COMPOSER_AGENT]    Tamanho: {len(composed.get('response_text', ''))} caracteres")
            print(f"[RESPONSE_COMPOSER_AGENT]    User-friendly score: {composed.get('user_friendly_score', 0)}")
            print(f"[RESPONSE_COMPOSER_AGENT]    Tokens usados: {response.usage.total_tokens}")
            
            # Retornar resposta formatada + dados originais da análise para metadata
            return {
                'response_text': composed.get('response_text', ''),
                'response_summary': composed.get('response_summary', ''),
                'key_numbers': composed.get('key_numbers', []),
                'formatting_style': composed.get('formatting_style', 'markdown_with_emojis'),
                'user_friendly_score': composed.get('user_friendly_score', 0.0),
                'tokens_used': response.usage.total_tokens,
                'model_used': self.model,
                'error': None,
                # Preservar dados da análise Python Runtime para metadata
                'analysis_summary': state.get('analysis_summary', ''),
                'statistics': state.get('statistics', {}),
                'insights': state.get('insights', []),
                'visualizations': state.get('visualizations', []),
                'recommendations': state.get('recommendations', [])
            }
            
        except Exception as e:
            print(f"[RESPONSE_COMPOSER_AGENT] ❌ Erro na composição: {e}")
            return {
                'response_text': '',
                'response_summary': '',
                'key_numbers': [],
                'formatting_style': 'plain_text',
                'user_friendly_score': 0.0,
                'tokens_used': 0,
                'model_used': self.model,
                'error': str(e),
                # Preservar dados da análise mesmo em caso de erro
                'analysis_summary': state.get('analysis_summary', ''),
                'statistics': state.get('statistics', {}),
                'insights': state.get('insights', []),
                'visualizations': state.get('visualizations', []),
                'recommendations': state.get('recommendations', [])
            }


if __name__ == '__main__':
    # Teste básico
    agent = ResponseComposerAgent()
    
    test_state = {
        'pergunta': 'Quantas vendas tivemos ontem?',
        'username': 'test_user',
        'row_count': 1,
        'analysis_summary': 'Foram registradas 150 vendas no dia anterior.',
        'statistics': {'total': 150, 'media': 150.0},
        'insights': [
            {
                'title': 'Volume alto de vendas',
                'description': 'O volume de 150 vendas está acima da média diária.',
                'impact': 'alto'
            }
        ],
        'recommendations': [
            {
                'action': 'Manter o estoque abastecido',
                'priority': 'alta'
            }
        ],
        'visualizations': []
    }
    
    result = agent.execute(test_state)
    print(json.dumps(result, indent=2, ensure_ascii=False))
