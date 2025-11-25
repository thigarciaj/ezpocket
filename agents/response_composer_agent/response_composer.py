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
        
        # Carregar roles.json
        roles_path = Path(__file__).parent / "roles.json"
        with open(roles_path, 'r', encoding='utf-8') as f:
            self.roles = json.load(f)
    
    def _build_prompt(self, state: Dict[str, Any]) -> str:
        """Constrói o prompt para formatação da resposta"""
        
        pergunta = state.get('pergunta', '')
        analysis_summary = state.get('analysis_summary', '')
        statistics = state.get('statistics', {})
        insights = state.get('insights', [])
        recommendations = state.get('recommendations', [])
        visualizations = state.get('visualizations', [])
        row_count = state.get('row_count', 0)
        results = state.get('results', [])
        
        # Limitar dados brutos para evitar tokens excessivos (max 50 registros)
        results_sample = results[:50] if isinstance(results, list) else []
        
        prompt = f"""{self.roles['prompt_intro']}

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

**DADOS BRUTOS (amostra de até 50 registros):**
- Total de registros: {row_count}
- Dados disponíveis:
```json
{json.dumps(results_sample, indent=2, ensure_ascii=False)}
```

---

**DIRETRIZES DO AGENTE (roles.json):**

**Responsibilities:**
{json.dumps(self.roles.get('responsibilities', []), indent=2, ensure_ascii=False)}

**Formatting Guidelines:**
```json
{json.dumps(self.roles.get('formatting_guidelines', {}), indent=2, ensure_ascii=False)}
```

**SUA TAREFA:**
{self.roles['response_instructions'].get('follow_all_guidelines', 'Componha uma resposta seguindo TODAS as diretrizes')}

**FORMATO DE RESPOSTA (JSON):**
{json.dumps(self.roles.get('output_format', {}), indent=2, ensure_ascii=False)}

{self.roles['response_instructions'].get('format', 'Retorne JSON válido')}"""
        
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
                        "role": self.roles['system_message']['role'],
                        "content": self.roles['system_message']['content']
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
