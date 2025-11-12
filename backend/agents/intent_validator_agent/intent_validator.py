"""
Intent Validator Agent - Nó 0
Valida a intenção e escopo da pergunta do usuário antes de processar.
"""

import os
import json
from openai import OpenAI
from typing import Dict, Any

class IntentValidatorAgent:
    """
    Agente responsável por validar se a pergunta do usuário está dentro do escopo
    do sistema (análise de dados financeiros e operacionais da EZPocket).
    
    Este é o primeiro nó do grafo e atua como um filtro inicial.
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"
        
        # Carrega definições de categorias do roles.json
        roles_path = os.path.join(os.path.dirname(__file__), 'roles.json')
        with open(roles_path, 'r', encoding='utf-8') as f:
            self.roles = json.load(f)
    
    def _build_system_prompt(self) -> str:
        """Constrói o system prompt a partir do roles.json"""
        categories = self.roles['categories']
        rules = self.roles['classification_rules']
        security = self.roles['security_rules']
        
        prompt = """Você é um validador de intenções para um sistema de análise de dados da EZPocket.
A EZPocket é uma plataforma de antecipação de recebíveis e gestão financeira.

"""
        
        # Adiciona regras de segurança NO TOPO (prioridade máxima)
        prompt += f"⚠️ {security['directive']}\n\n"
        prompt += "DADOS SENSÍVEIS PROIBIDOS (NUNCA permitir acesso):\n"
        for item in security['forbidden_data']:
            prompt += f"  ❌ {item}\n"
        prompt += "\nEXEMPLOS DE PERGUNTAS PROIBIDAS:\n"
        for keyword in security['forbidden_keywords']:
            prompt += f"  ❌ \"{keyword}\"\n"
        prompt += f"\n🔒 AÇÃO: {security['action']}\n"
        prompt += "\n" + "="*80 + "\n\n"
        
        prompt += """Seu trabalho é determinar se a pergunta do usuário está DENTRO DO ESCOPO do sistema e classificá-la em uma das 3 categorias.

CATEGORIAS VÁLIDAS (retorne valid=true):

"""
        
        # Adiciona cada categoria
        for i, (cat_key, cat_data) in enumerate([
            ('quantidade', categories['quantidade']),
            ('conhecimentos_gerais', categories['conhecimentos_gerais']),
            ('analise_estatistica', categories['analise_estatistica'])
        ], 1):
            prompt += f"{i}. **{cat_data['name']}**: {cat_data['description']}\n"
            prompt += f"   IMPORTANTE: {cat_data['important']}\n"
            prompt += f"   PALAVRAS-CHAVE: {', '.join(cat_data['keywords'])}\n"
            prompt += f"   EXEMPLOS:\n"
            for example in cat_data['examples']:
                prompt += f"   - \"{example['question']}\" → {example['expected_answer']}\n"
            prompt += "\n"
        
        # Adiciona regras de fora do escopo
        prompt += """FORA DO ESCOPO (retorne valid=false):
- ⚠️ QUALQUER pergunta que solicite DADOS SENSÍVEIS (CPF, RG, senhas, documentos pessoais, etc)
"""
        for item in categories['fora_escopo']['examples']:
            prompt += f"- {item}\n"
        
        # Adiciona regras de classificação
        prompt += """
REGRAS DE CLASSIFICAÇÃO (APLICAR NESTA ORDEM):
0. 🔒 PRIORIDADE MÁXIMA: Pergunta solicita DADOS SENSÍVEIS? → fora_escopo (segurança e privacidade)
"""
        for rule in rules['order']:
            prompt += f"{rule}\n"
        
        # Adiciona exemplos de desambiguação
        prompt += """
EXEMPLOS DE CLASSIFICAÇÃO CORRETA:
"""
        for example in rules['disambiguation_examples']:
            prompt += f"- \"{example['question']}\" → {example['correct_category']} ({example['reason']})\n"
        
        prompt += """
Retorne APENAS um JSON válido no formato:
{
    "valid": true/false,
    "category": "quantidade|conhecimentos_gerais|analise_estatistica|fora_escopo",
    "reason": "breve explicação da validação"
}"""
        
        return prompt
        
    def validate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida a intenção e escopo da pergunta do usuário.
        
        Args:
            state: Estado contendo 'pergunta', 'username', 'projeto'
            
        Returns:
            Estado atualizado com:
            - 'intent_valid': bool (se a pergunta está no escopo)
            - 'intent_reason': str (motivo da validação)
            - 'intent_category': str (categoria da intenção)
        """
        pergunta = state.get("pergunta", "")
        username = state.get("username", "")
        projeto = state.get("projeto", "")
        
        # Header bonito
        print(f"\n{'='*80}")
        print(f"🛡️  INTENT VALIDATOR AGENT - NÓ 0")
        print(f"{'='*80}")
        
        # Inputs
        print(f"📥 INPUTS:")
        print(f"   📝 Pergunta: {pergunta}")
        print(f"   👤 Username: {username}")
        print(f"   📁 Projeto: {projeto}")
        print(f"{'='*80}")
        
        # Processamento
        print(f"\n⚙️  PROCESSAMENTO:")
        print(f"   🔄 Carregando regras do roles.json...")
        
        # Constrói o prompt dinamicamente do roles.json
        system_prompt = self._build_system_prompt()
        print(f"   ✅ Prompt construído ({len(system_prompt)} caracteres)")
        
        # Verificações de segurança
        if "pilares" in system_prompt.lower():
            print(f"   ✅ Palavras-chave de conhecimentos_gerais carregadas")
        if "🔒" in system_prompt:
            print(f"   ✅ Regras de segurança ativadas")

        user_prompt = f"""Pergunta do usuário: "{pergunta}"
Projeto/contexto: "{projeto if projeto else 'Geral'}"

Valide a intenção e escopo."""

        print(f"   🤖 Chamando GPT-4o (modelo: {self.model})...")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500,  # Aumentado para acomodar resposta completa
                response_format={"type": "json_object"}  # Força resposta em JSON
            )
            
            print(f"   ✅ Resposta recebida do GPT-4o")
            result_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks se existir
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            # Parse JSON response
            import json
            try:
                result = json.loads(result_text)
                print(f"   ✅ JSON parseado com sucesso")
            except json.JSONDecodeError as je:
                print(f"   ❌ ERRO ao fazer parse do JSON: {je}")
                print(f"   📄 Texto recebido: {result_text[:200]}...")
                # Tenta extrair JSON usando regex
                import re
                json_match = re.search(r'\{[^{}]*\}', result_text)
                if json_match:
                    result = json.loads(json_match.group())
                    print(f"   ✅ JSON extraído com regex")
                else:
                    raise je
            
            is_valid = result.get("valid", False)
            category = result.get("category", "fora_escopo")
            reason = result.get("reason", "Validação não especificada")
            
            # Output
            print(f"{'='*80}")
            print(f"📤 OUTPUT:")
            print(f"   {'✅' if is_valid else '❌'} Intent Válida: {is_valid}")
            print(f"   📂 Categoria: {category}")
            print(f"   💬 Razão: {reason}")
            print(f"{'='*80}\n")
            
            # Atualiza o estado
            state["intent_valid"] = is_valid
            state["intent_category"] = category
            state["intent_reason"] = reason
            
            return state
            
        except Exception as e:
            print(f"{'='*80}")
            print(f"❌ ERRO NO PROCESSAMENTO:")
            print(f"   💥 {str(e)}")
            print(f"{'='*80}\n")
            # Em caso de erro, assume válido para não bloquear o sistema
            state["intent_valid"] = True
            state["intent_category"] = "quantidade"
            state["intent_reason"] = f"Erro na validação: {str(e)}"
            return state
    
    def generate_out_of_scope_response(self, state: Dict[str, Any]) -> str:
        """
        Gera uma resposta educada quando a pergunta está fora do escopo.
        
        Args:
            state: Estado contendo informações da validação
            
        Returns:
            Mensagem educada explicando o escopo do sistema
        """
        out_of_scope_data = self.roles['out_of_scope']
        
        response = f"""{out_of_scope_data['response_template']}

**O que eu posso fazer por você:**

"""
        
        # Adiciona exemplos de cada categoria
        for category in out_of_scope_data['categories_help']:
            response += f"{category['icon']} **{category['title']}**:\n"
            for example in category['examples']:
                response += f"- \"{example}\"\n"
            response += "\n"
        
        response += "Por favor, faça uma pergunta relacionada a uma dessas categorias. Se precisar de ajuda, digite \"help\"."

        return response
