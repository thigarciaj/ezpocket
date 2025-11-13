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
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"
    
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
            # Construir prompt para o GPT
            system_prompt = """Você é um assistente especializado em criar planos de execução para análise de dados financeiros da EZPocket.

🎯 OBJETIVO:
Gerar um plano detalhado e estruturado em linguagem natural que descreva EXATAMENTE como o sistema irá processar e responder à pergunta do usuário.

📊 CONTEXTO DO SISTEMA EZPOCKET:
- Sistema de análise financeira e transacional
- Base de dados: Amazon Athena (receivables_db)
- **TABELA ÚNICA**: report_orders (contém TODOS os dados de pedidos e transações)
- Capacidades: consultas SQL, agregações, análises estatísticas, filtros temporais, window functions
- Não há JOINs: todos os dados estão desnormalizados em report_orders

🏗️ ESTRUTURA DO PLANO:
Um plano deve conter:
1. DESCRIÇÃO GERAL: Resumo em 2-3 frases do que será feito
2. PASSOS DETALHADOS: Lista ordenada e específica de ações
3. ESTIMATIVA DE COMPLEXIDADE: Análise realista baseada em operações necessárias
4. FONTES DE DADOS: Tabelas/views específicas que serão consultadas
5. FORMATO DE SAÍDA: Como o resultado será apresentado

📋 CATEGORIAS E SEUS PADRÕES:

QUANTIDADE (queries simples de contagem/soma):
- Passos típicos: 1) Acessar tabela report_orders, 2) Aplicar filtros WHERE, 3) Executar agregação, 4) Formatar resultado
- Complexidade: Baixa (filtros simples) ou Média (múltiplas condições/agregações)
- Fonte: report_orders
- Saída comum: número, tabela simples

CONHECIMENTOS_GERAIS (FAQ, informações da empresa):
- Passos típicos: 1) Identificar tópico, 2) Buscar em FAQ/documentação, 3) Formatar resposta contextualizada
- Complexidade: Baixa
- Fontes comuns: faq_database, knowledge_base, documentation
- Saída comum: texto explicativo

ANALISE_ESTATISTICA (tendências, comparações, insights):
- Passos típicos: 1) Consultar report_orders com filtros temporais, 2) Aplicar agregações e GROUP BY, 3) Calcular métricas, 4) Identificar padrões, 5) Gerar insights
- Complexidade: Média a Alta
- Fonte: report_orders (com agregações complexas e window functions)
- Saída comum: gráfico, tabela comparativa, texto com insights

⚙️ CRITÉRIOS DE COMPLEXIDADE:

BAIXA:
- Consulta simples em report_orders
- Filtros básicos (1-2 condições WHERE)
- Uma agregação simples (COUNT, SUM, AVG)
- Sem GROUP BY ou GROUP BY simples (1 campo)
- 2-3 passos no total

MÉDIA:
- Consulta em report_orders com múltiplos filtros
- GROUP BY com 2-3 campos
- Múltiplas agregações (COUNT, SUM, AVG no mesmo query)
- Cálculos intermediários ou expressões CASE
- Filtros complexos (BETWEEN, IN, múltiplos AND/OR)
- 4-5 passos no total

ALTA:
- Consulta em report_orders com agregações encadeadas
- GROUP BY complexo com HAVING
- Window functions (ROW_NUMBER, RANK, LAG, LEAD)
- Subqueries ou CTEs (WITH)
- Múltiplas agregações com cálculos derivados
- Análises estatísticas (percentuais, variações, médias móveis)
- 6+ passos no total

🎨 FORMATOS DE SAÍDA:

- número: Valores únicos (total, contagem, média)
- tabela: Listagens, rankings, comparações linha a linha
- gráfico: Tendências temporais, distribuições, comparações visuais
- texto: Explicações, FAQs, resumos narrativos
- json: Dados estruturados para consumo por API

📝 REGRAS PARA ESCREVER PASSOS:

1. Use verbos de ação: "Consultar", "Filtrar", "Calcular", "Agregar", "Comparar"
2. Seja específico: "Filtrar pedidos de outubro de 2024" em vez de "Filtrar dados"
3. Sempre mencione report_orders: "Consultar tabela report_orders" 
4. Indique operações SQL: "Aplicar GROUP BY cliente", "Usar WHERE status = 'completed'"
5. Descreva transformações: "Calcular total somando coluna amount"
6. Explique o output: "Formatar resultado como número com 2 casas decimais"
7. Lembre: TODOS os dados estão em report_orders (não há outras tabelas)

💡 EXEMPLOS DE BONS PLANOS:

Pergunta: "Quantos pedidos tivemos em outubro?"
{
    "plan": "Consultar a tabela report_orders aplicando filtro temporal para o mês de outubro e contar o número total de registros. Resultado será apresentado como número único.",
    "steps": [
        "Consultar tabela 'report_orders' no Athena (receivables_db)",
        "Aplicar filtro WHERE para outubro de 2024",
        "Executar agregação COUNT(*) para contar pedidos",
        "Retornar resultado como número inteiro"
    ],
    "estimated_complexity": "baixa",
    "data_sources": ["report_orders"],
    "output_format": "número"
}

Pergunta: "Compare as vendas dos últimos 3 meses"
{
    "plan": "Buscar dados de vendas dos últimos 3 meses na tabela report_orders, agregar por mês usando GROUP BY, calcular totais mensais e variações percentuais. Análise requer agregação temporal e cálculos de variação.",
    "steps": [
        "Consultar tabela 'report_orders' com filtro dos últimos 3 meses",
        "Aplicar GROUP BY month para agregar por período",
        "Calcular SUM(amount) para cada mês",
        "Calcular variação percentual entre meses consecutivos usando window functions",
        "Gerar tabela comparativa com meses, totais e variações",
        "Formatar resultado como gráfico de linha temporal"
    ],
    "estimated_complexity": "média",
    "data_sources": ["report_orders"],
    "output_format": "gráfico"
}

Pergunta: "Quais são os top 5 clientes por receita este ano?"
{
    "plan": "Extrair dados de clientes e receitas de report_orders para o ano atual, agregar receita total por cliente, ordenar em ordem decrescente e retornar os 5 primeiros. Utiliza GROUP BY e ORDER BY com LIMIT.",
    "steps": [
        "Consultar tabela 'report_orders' filtrando ano atual",
        "Aplicar GROUP BY customer_name para agregar por cliente",
        "Calcular SUM(amount) como receita total de cada cliente",
        "Ordenar resultados por receita DESC usando ORDER BY",
        "Aplicar LIMIT 5 para retornar apenas top 5",
        "Formatar como tabela com colunas: cliente, receita total"
    ],
    "estimated_complexity": "baixa",
    "data_sources": ["report_orders"],
    "output_format": "tabela"
}

Retorne APENAS um JSON válido no formato:
{
    "plan": "Descrição detalhada do plano em 2-3 frases completas",
    "steps": [
        "Passo 1: Ação específica com detalhes (sempre mencione report_orders)",
        "Passo 2: Próxima ação específica",
        "Passo 3: ...",
        "(quantos passos forem necessários)"
    ],
    "estimated_complexity": "baixa|média|alta",
    "data_sources": ["report_orders"],
    "output_format": "número|tabela|gráfico|texto|json"
}

IMPORTANTE: data_sources será SEMPRE ["report_orders"] pois é a única tabela disponível no sistema."""

            user_prompt = f"""Pergunta do usuário: "{pergunta}"
Categoria: {intent_category}
Projeto: {projeto}

Crie um plano de execução para responder esta pergunta."""

            print(f"[PLAN_BUILDER]    🤖 Chamando GPT-4o para gerar plano...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
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
            
            # Metadata adicional
            metadata = {
                "gpt_model": self.model,
                "prompt_length": len(system_prompt) + len(user_prompt),
                "response_length": len(json.dumps(result)),
                "steps_count": len(steps),
                "data_sources_count": len(data_sources)
            }
            
            # Retornar apenas campos processados
            return {
                "plan": plan,
                "plan_steps": steps,
                "estimated_complexity": complexity,
                "data_sources": data_sources,
                "output_format": output_format,
                "execution_time": execution_time,
                "tokens_used": tokens_used,
                "model_used": self.model,
                "metadata": metadata
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            print(f"\n{'='*80}")
            print(f"[PLAN_BUILDER] ❌ ERRO NO PROCESSAMENTO:")
            print(f"[PLAN_BUILDER]    💥 {str(e)}")
            print(f"{'='*80}\n")
            
            metadata = {
                "error_type": type(e).__name__,
                "gpt_model": self.model
            }
            
            return {
                "plan": f"Erro ao gerar plano: {str(e)}",
                "plan_steps": [],
                "estimated_complexity": "média",
                "data_sources": [],
                "output_format": "texto",
                "error_message": str(e),
                "execution_time": execution_time,
                "tokens_used": None,
                "model_used": self.model,
                "metadata": metadata
            }
