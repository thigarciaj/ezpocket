"""
Plan Builder Agent
Gera um plano em linguagem natural para responder à pergunta do usuário
"""

import os
import time
from openai import OpenAI
from typing import Dict, Any

class PlanBuilderAgent:
    """
    Agente responsável por criar um plano de execução em linguagem natural
    que descreve como o sistema irá responder à pergunta do usuário.
    """
    
    def __init__(self):
        print("\n" + "="*80)
        print("📋 PLAN BUILDER AGENT - GERADOR DE PLANOS")
        print("="*80)
        print("✅ Agente inicializado")
        print("="*80 + "\n")
        
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Carregar roles.json ou roles_local.json
        import json
        from pathlib import Path
        from dotenv import load_dotenv
        
        # Carregar .env para verificar BD_REFERENCE
        project_env = Path(__file__).parent.parent.parent / ".env"
        load_dotenv(project_env)
        
        # Verificar qual roles usar baseado em BD_REFERENCE
        bd_reference = os.getenv("BD_REFERENCE", "Athena")
        
        if bd_reference == "Local":
            roles_file = "roles_local.json"
            print(f"   🔧 Plan Builder usando roles_local.json (PostgreSQL 15)")
        else:
            roles_file = "roles.json"
            print(f"   🔧 Plan Builder usando roles.json (AWS Athena)")
        
        roles_path = Path(__file__).parent / roles_file
        with open(roles_path, 'r', encoding='utf-8') as f:
            self.roles = json.load(f)
        
        self.model = self.roles.get('model_config', {}).get('model', 'gpt-4o')
    
    def build_plan(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera um plano em linguagem natural
        
        Args:
            state: Estado contendo:
                - pergunta: str
                - intent_category: str
                - username: str
                - projeto: str
                
        Returns:
            Estado atualizado com:
                - plan: str (plano em linguagem natural)
                - plan_steps: list (passos do plano)
                - estimated_complexity: str
        """
        
        pergunta = state.get("pergunta", "")
        intent_category = state.get("intent_category", "unknown")
        username = state.get("username", "")
        projeto = state.get("projeto", "")
        
        # Header
        print(f"\n{'='*80}")
        print(f"[PLAN_BUILDER] 📋 PLAN BUILDER AGENT - NÓ DE PLANEJAMENTO")
        print(f"{'='*80}")
        
        # Inputs
        print(f"[PLAN_BUILDER] 📥 INPUTS:")
        print(f"[PLAN_BUILDER]    📝 Pergunta: {pergunta}")
        print(f"[PLAN_BUILDER]    📂 Categoria: {intent_category}")
        print(f"[PLAN_BUILDER]    👤 Username: {username}")
        print(f"[PLAN_BUILDER]    📁 Projeto: {projeto}")
        
        print(f"\n[PLAN_BUILDER] ⚙️  PROCESSAMENTO:")
        
        start_time = time.time()
        
        try:
            # Construir prompt para o GPT usando roles.json
            import json
            system_prompt = f"""{self.roles['system_prompt_intro']} {self.roles['description']}

🎯 OBJETIVO:
{self.roles['objective']}

🔒 REGRAS DE SEGURANÇA:
{self.roles['security_rules']['directive']}

📊 CONTEXTO DO BANCO DE DADOS:
{json.dumps(self.roles['database_context'], indent=2, ensure_ascii=False)}

📋 REGRAS DE PLANEJAMENTO:
{json.dumps(self.roles['planning_rules'], indent=2, ensure_ascii=False)}

⚙️ DIRETRIZES DE COMPLEXIDADE:
{json.dumps(self.roles['complexity_guidelines'], indent=2, ensure_ascii=False)}

💡 EXEMPLOS:
{json.dumps(self.roles['examples'], indent=2, ensure_ascii=False)}

✓ CHECKLIST DE VALIDAÇÃO:
{json.dumps(self.roles['validation_checklist'], indent=2, ensure_ascii=False)}

RETORNE APENAS JSON válido no formato:
{json.dumps(self.roles['output_structure'], indent=2, ensure_ascii=False)}"""

            # Verificar se há contexto de conversa (projeto ativo)
            conversation_context = state.get("conversation_context", "")
            has_history = state.get("has_history", False)
            
            # Verificar se há sugestão do usuário vinda do user_proposed_plan
            user_proposed_plan = state.get("user_proposed_plan", "")
            
            if user_proposed_plan:
                print(f"[PLAN_BUILDER]    💡 Sugestão do usuário detectada: {user_proposed_plan[:100]}...")
                base_prompt = self.roles['user_prompt_with_suggestion'].format(
                    pergunta=pergunta,
                    intent_category=intent_category,
                    projeto=projeto,
                    user_proposed_plan=user_proposed_plan
                )
            else:
                base_prompt = self.roles['user_prompt_normal'].format(
                    pergunta=pergunta,
                    intent_category=intent_category,
                    projeto=projeto
                )
            
            # Injetar contexto ANTES do prompt se houver histórico
            if has_history and conversation_context:
                user_prompt = f"{conversation_context}\n\n{base_prompt}"
                print(f"[PLAN_BUILDER]    📚 Contexto adicionado: {len(conversation_context)} caracteres")
            else:
                user_prompt = base_prompt
                print(f"[PLAN_BUILDER]    💬 Sem contexto (chat geral ou primeira mensagem)")

            print(f"[PLAN_BUILDER]    🤖 Chamando {self.model} para gerar plano...")
            
            temperature = self.roles.get('model_config', {}).get('temperature', 0.3)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            print(f"[PLAN_BUILDER]    ✅ Resposta recebida do GPT-4o")
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON
            import json
            try:
                result = json.loads(result_text)
                print(f"[PLAN_BUILDER]    ✅ JSON parseado com sucesso")
            except json.JSONDecodeError as je:
                print(f"[PLAN_BUILDER]    ❌ Erro ao fazer parse do JSON: {je}")
                raise je
            
            plan = result.get("plan", "")
            steps = result.get("steps", [])
            complexity = result.get("estimated_complexity", "média")
            data_sources = result.get("data_sources", [])
            output_format = result.get("output_format", "texto")
            
            # Tokens usados
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else None
            
            # Calcula tempo de execução
            execution_time = time.time() - start_time
            
            # Output
            print(f"\n{'='*80}")
            print(f"[PLAN_BUILDER] 📤 OUTPUT:")
            print(f"[PLAN_BUILDER]    📋 Plano: {plan}")
            print(f"[PLAN_BUILDER]    📊 Passos ({len(steps)}):")
            for i, step in enumerate(steps, 1):
                print(f"[PLAN_BUILDER]       {i}. {step}")
            print(f"[PLAN_BUILDER]    ⚡ Complexidade: {complexity}")
            print(f"[PLAN_BUILDER]    💾 Fontes de dados: {', '.join(data_sources)}")
            print(f"[PLAN_BUILDER]    📈 Formato de saída: {output_format}")
            print(f"[PLAN_BUILDER]    ⏱️  Tempo de execução: {execution_time:.3f}s")
            print(f"{'='*80}\n")
            
            # Retornar campos processados (metadata será criado pelo history_preferences)
            return {
                "plan": plan,
                "plan_steps": steps,
                "estimated_complexity": complexity,
                "data_sources": data_sources,
                "output_format": output_format,
                "execution_time": execution_time,
                "tokens_used": tokens_used,
                "model_used": self.model,
                # Campos extras para metadata (serão usados pelo history_preferences)
                "prompt_length": len(system_prompt) + len(user_prompt),
                "response_length": len(json.dumps(result))
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            print(f"\n{'='*80}")
            print(f"[PLAN_BUILDER] ❌ ERRO NO PROCESSAMENTO:")
            print(f"[PLAN_BUILDER]    💥 {str(e)}")
            print(f"{'='*80}\n")
            
            return {
                "plan": f"Erro ao gerar plano: {str(e)}",
                "plan_steps": [],
                "estimated_complexity": "média",
                "data_sources": [],
                "output_format": "texto",
                "error_message": str(e),
                "execution_time": execution_time,
                "tokens_used": None,
                "model_used": self.model
            }
