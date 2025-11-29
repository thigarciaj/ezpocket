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
        
        # Carregar .env para verificar BD_REFERENCE
        from dotenv import load_dotenv
        from pathlib import Path
        project_env = Path(__file__).parent.parent.parent / ".env"
        load_dotenv(project_env)
        
        # Verificar qual roles usar baseado em BD_REFERENCE
        bd_reference = os.getenv("BD_REFERENCE", "Athena")
        
        if bd_reference == "Local":
            roles_file = "roles_local.json"
            print(f"   🔧 Plan Refiner usando roles_local.json (PostgreSQL 15)")
        else:
            roles_file = "roles.json"
            print(f"   🔧 Plan Refiner usando roles.json (AWS Athena)")
        
        # Carrega roles
        roles_path = os.path.join(os.path.dirname(__file__), roles_file)
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
        return f"""{self.roles['system_prompt_intro']}

ROLE: {self.roles['role']}
DESCRIÇÃO: {self.roles['description']}

OBJETIVO: {self.roles['objective']}

REGRAS DE REFINAMENTO:
{chr(10).join(f"- {rule}" for rule in self.roles['refinement_rules'])}

PROCESSO DE REFINAMENTO:
{chr(10).join(f"{step}: {desc}" for step, desc in self.roles['refinement_process'].items())}

VERIFICAÇÕES DE QUALIDADE:
{chr(10).join(f"- {check}" for check in self.roles['quality_checks'])}

{self.roles['system_prompt_output']}
"""
    
    def _build_user_prompt(
        self,
        pergunta: str,
        original_plan: str,
        user_suggestion: str,
        intent_category: str
    ) -> str:
        """Constrói prompt do usuário"""
        return self.roles['user_prompt_template'].format(
            pergunta=pergunta,
            intent_category=intent_category,
            original_plan=original_plan,
            user_suggestion=user_suggestion
        )


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
