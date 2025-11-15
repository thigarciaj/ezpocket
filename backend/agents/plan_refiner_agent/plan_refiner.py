"""
Plan Refiner Agent
Refina planos de análise baseado na sugestão do usuário
"""

import os
import json
import time
from openai import OpenAI
from typing import Dict, Any, List

class PlanRefinerAgent:
    """
    Agente que refina planos de análise baseado em sugestões do usuário.
    Combina o plano original do PlanBuilder com a entrada do UserProposedPlan.
    """
    
    def __init__(self):
        """Inicializa o Plan Refiner Agent"""
        print("\n" + "="*80)
        print("🔧 PLAN REFINER AGENT - REFINADOR DE PLANOS")
        print("="*80)
        
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4o"
        
        print("✅ Agente inicializado")
        print("="*80)
        print()
        self.temperature = 0.3  # Mais determinístico para refinar planos
        
        # Carrega roles
        roles_path = os.path.join(os.path.dirname(__file__), 'roles.json')
        with open(roles_path, 'r', encoding='utf-8') as f:
            self.roles = json.load(f)
        
        print("✅ Agente inicializado")
        print("="*80 + "\n")
    
    def refine_plan(
        self,
        pergunta: str,
        original_plan: str,
        user_suggestion: str,
        intent_category: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Refina um plano baseado na sugestão do usuário
        
        Args:
            pergunta: Pergunta original do usuário
            original_plan: Plano gerado pelo PlanBuilder
            user_suggestion: Sugestão do usuário do UserProposedPlan
            intent_category: Categoria da intenção
            
        Returns:
            Dict com plano refinado e metadados
        """
        start = time.time()
        
        try:
            print(f"🔍 Refinando plano...")
            print(f"   Pergunta: {pergunta[:80]}...")
            print(f"   Plano original: {len(original_plan)} chars")
            print(f"   Sugestão: {user_suggestion[:80]}...")
            
            # Construir prompt
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(
                pergunta, original_plan, user_suggestion, intent_category
            )
            
            # Chamar OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            execution_time = time.time() - start
            
            output = {
                'refined_plan': result.get('refined_plan', ''),
                'plan_steps': result.get('plan_steps', []),
                'refinement_summary': result.get('refinement_summary', ''),
                'changes_applied': result.get('changes_applied', []),
                'user_suggestions_incorporated': result.get('user_suggestions_incorporated', []),
                'improvements_made': result.get('improvements_made', []),
                'validation_notes': result.get('validation_notes', ''),
                'execution_time': execution_time,
                'model_used': self.model,
                'success': True
            }
            
            print(f"✅ Plano refinado com sucesso!")
            print(f"   Tempo: {execution_time:.2f}s")
            print(f"   Passos: {len(output['plan_steps'])}")
            print(f"   Mudanças: {len(output['changes_applied'])}")
            
            return output
            
        except Exception as e:
            execution_time = time.time() - start
            print(f"❌ Erro ao refinar plano: {e}")
            
            return {
                'refined_plan': original_plan,  # Fallback para plano original
                'plan_steps': [],
                'refinement_summary': f"Erro ao refinar: {str(e)}",
                'changes_applied': [],
                'user_suggestions_incorporated': [],
                'improvements_made': [],
                'validation_notes': f"Erro: {str(e)}",
                'execution_time': execution_time,
                'model_used': self.model,
                'success': False,
                'error': str(e)
            }
    
    def _build_system_prompt(self) -> str:
        """Constrói prompt de sistema"""
        return f"""Você é um agente especializado em REFINAR PLANOS DE ANÁLISE baseado em sugestões de usuários.

ROLE: {self.roles['role']}
DESCRIÇÃO: {self.roles['description']}

OBJETIVO: {self.roles['objective']}

REGRAS DE REFINAMENTO:
{chr(10).join(f"- {rule}" for rule in self.roles['refinement_rules'])}

PROCESSO DE REFINAMENTO:
{chr(10).join(f"{step}: {desc}" for step, desc in self.roles['refinement_process'].items())}

VERIFICAÇÕES DE QUALIDADE:
{chr(10).join(f"- {check}" for check in self.roles['quality_checks'])}

FORMATO DE SAÍDA (JSON):
{{
  "refined_plan": "Plano refinado completo em texto estruturado",
  "plan_steps": ["passo 1", "passo 2", "passo 3", ...],
  "refinement_summary": "Resumo das principais mudanças",
  "changes_applied": ["mudança 1", "mudança 2", ...],
  "user_suggestions_incorporated": ["sugestão 1 aceita", ...],
  "improvements_made": ["melhoria 1", "melhoria 2", ...],
  "validation_notes": "Notas sobre validações realizadas"
}}

IMPORTANTE:
- SEMPRE retorne um plano refinado válido e completo
- SEMPRE inclua plan_steps como lista de strings (passos numerados e detalhados)
- SEMPRE justifique mudanças significativas
- SEMPRE valide que o plano atende à pergunta original
- Mantenha a estrutura clara e os passos bem definidos
"""
    
    def _build_user_prompt(
        self,
        pergunta: str,
        original_plan: str,
        user_suggestion: str,
        intent_category: str
    ) -> str:
        """Constrói prompt do usuário"""
        return f"""TAREFA: Refinar o plano de análise incorporando a sugestão do usuário.

PERGUNTA ORIGINAL:
{pergunta}

CATEGORIA: {intent_category}

PLANO ORIGINAL (gerado pelo PlanBuilder):
{original_plan}

SUGESTÃO DO USUÁRIO (do UserProposedPlan):
{user_suggestion}

Por favor, refine o plano original incorporando a sugestão do usuário de forma inteligente.
Retorne o resultado em formato JSON conforme especificado.
"""


if __name__ == "__main__":
    # Teste simples
    agent = PlanRefinerAgent()
    
    result = agent.refine_plan(
        pergunta="Quantas vendas tivemos este mês?",
        original_plan="""
DESCRIÇÃO GERAL:
Consultar tabela report_orders e contar pedidos do mês atual

PASSOS:
1. Acessar receivables_db.report_orders
2. Filtrar por contract_start_date do mês atual
3. Contar registros com COUNT(*)

COMPLEXIDADE: Baixa
""",
        user_suggestion="Quero ver separado por produto",
        intent_category="quantidade"
    )
    
    print("\n" + "="*80)
    print("RESULTADO:")
    print("="*80)
    print(json.dumps(result, indent=2, ensure_ascii=False))
