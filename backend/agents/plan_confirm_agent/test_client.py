"""
Cliente de teste para o Plan Confirm Agent
Testa o agente através do endpoint Flask
"""

import requests
import json
import sys
import time
from typing import Dict, Any

# URL do endpoint
BASE_URL = "http://localhost:5010"
ENDPOINT = f"{BASE_URL}/test-plan-confirm"


def test_plan_confirm(
    pergunta: str,
    plan: str,
    username: str = "test_user",
    projeto: str = "test_project",
    intent_category: str = None,
    plan_steps: list = None,
    estimated_complexity: str = None,
    data_sources: list = None,
    output_format: str = None
) -> Dict[str, Any]:
    """
    Testa o Plan Confirm Agent com os dados fornecidos
    
    Args:
        pergunta: Pergunta do usuário
        plan: Plano gerado pelo PlanBuilderAgent
        username: Nome do usuário
        projeto: Nome do projeto
        intent_category: Categoria da intenção
        plan_steps: Lista de passos do plano
        estimated_complexity: Complexidade estimada
        data_sources: Fontes de dados utilizadas
        output_format: Formato de saída esperado
        
    Returns:
        Dicionário com resultado do teste
    """
    payload = {
        "pergunta": pergunta,
        "plan": plan,
        "username": username,
        "projeto": projeto
    }
    
    if intent_category:
        payload["intent_category"] = intent_category
    if plan_steps:
        payload["plan_steps"] = plan_steps
    if estimated_complexity:
        payload["estimated_complexity"] = estimated_complexity
    if data_sources:
        payload["data_sources"] = data_sources
    if output_format:
        payload["output_format"] = output_format
    
    try:
        print(f"\n{'='*80}")
        print(f"📤 Enviando requisição...")
        print(f"   Pergunta: {pergunta}")
        print(f"   Plan: {plan[:80]}..." if len(plan) > 80 else f"   Plan: {plan}")
        print(f"{'='*80}\n")
        
        response = requests.post(ENDPOINT, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        print(f"{'='*80}")
        print(f"📥 Resposta recebida:")
        print(f"{'='*80}")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"{'='*80}\n")
        
        return result
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Erro: Não foi possível conectar ao servidor em {BASE_URL}")
        print(f"   Certifique-se de que o servidor está rodando:")
        print(f"   ./run_test.sh server")
        return None
        
    except requests.exceptions.Timeout:
        print(f"\n❌ Erro: Timeout ao aguardar resposta do servidor")
        return None
        
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ Erro HTTP: {e}")
        try:
            error_data = response.json()
            print(f"   Detalhes: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"   Response: {response.text}")
        return None
        
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        return None


def run_examples():
    """Executa exemplos pré-definidos"""
    print("\n" + "="*80)
    print("📚 EXECUTANDO EXEMPLOS PRÉ-DEFINIDOS")
    print("="*80)
    
    examples = [
        {
            "name": "Exemplo 1: Contagem de pedidos",
            "pergunta": "Quantos pedidos tivemos este mês?",
            "plan": "Consultar tabela report_orders filtrando por data >= início do mês atual e contar registros",
            "intent_category": "quantidade",
            "plan_steps": [
                "1. Identificar data de início do mês atual",
                "2. Consultar tabela report_orders",
                "3. Filtrar por created_at >= início do mês",
                "4. Contar número de pedidos",
                "5. Retornar resultado"
            ],
            "estimated_complexity": "baixa",
            "data_sources": ["report_orders"],
            "output_format": "Número simples com unidade (ex: '150 pedidos')"
        },
        {
            "name": "Exemplo 2: Valor total de receita",
            "pergunta": "Qual o valor total de receita em outubro?",
            "plan": "Somar valores da coluna amount na tabela report_orders para pedidos de outubro",
            "intent_category": "quantidade",
            "plan_steps": [
                "1. Filtrar pedidos de outubro (WHERE MONTH(created_at) = 10)",
                "2. Somar coluna amount",
                "3. Formatar valor em reais"
            ],
            "estimated_complexity": "baixa",
            "data_sources": ["report_orders"],
            "output_format": "Valor monetário em R$ (ex: 'R$ 50.000,00')"
        },
        {
            "name": "Exemplo 3: Clientes inadimplentes",
            "pergunta": "Quantos clientes estão inadimplentes?",
            "plan": "Consultar report_orders onde status = 'overdue' e contar clientes únicos",
            "intent_category": "quantidade",
            "plan_steps": [
                "1. Filtrar pedidos com status = 'overdue'",
                "2. Contar clientes distintos (COUNT DISTINCT customer_id)",
                "3. Retornar resultado"
            ],
            "estimated_complexity": "média",
            "data_sources": ["report_orders"],
            "output_format": "Número simples com unidade (ex: '23 clientes')"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{'='*80}")
        print(f"📝 {example['name']}")
        print(f"{'='*80}")
        
        result = test_plan_confirm(
            pergunta=example["pergunta"],
            plan=example["plan"],
            intent_category=example.get("intent_category"),
            plan_steps=example.get("plan_steps"),
            estimated_complexity=example.get("estimated_complexity"),
            data_sources=example.get("data_sources"),
            output_format=example.get("output_format")
        )
        
        if result and result.get("success"):
            output = result.get("output", {})
            print(f"\n✅ Teste {i} concluído:")
            print(f"   Plan Confirmed: {output.get('plan_confirmed')}")
            print(f"   Message: {output.get('confirmation_message')}")
        else:
            print(f"\n❌ Teste {i} falhou")
        
        if i < len(examples):
            print(f"\nAguardando 2 segundos antes do próximo teste...")
            time.sleep(2)
    
    print(f"\n{'='*80}")
    print(f"✅ Todos os exemplos foram executados")
    print(f"{'='*80}\n")


def run_interactive_direct():
    """Modo interativo chamando o agente diretamente (sem servidor)"""
    import sys
    import os
    
    # Adiciona path do backend
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    
    from agents.plan_confirm_agent.plan_confirm import PlanConfirmAgent
    
    agent = PlanConfirmAgent()
    
    print(f"\n{'='*80}")
    print(f"🎮 MODO INTERATIVO - PLAN CONFIRM")
    print(f"{'='*80}")
    print(f"Digite 'sair' para encerrar\n")
    
    while True:
        try:
            pergunta = input("📝 Digite a pergunta: ").strip()
            
            if pergunta.lower() in ['sair', 'exit', 'quit']:
                print("\n👋 Até logo!\n")
                break
            
            if not pergunta:
                print("⚠️  Pergunta não pode estar vazia\n")
                continue
            
            plan = input("📋 Digite o plano: ").strip()
            
            if not plan:
                print("⚠️  Plano não pode estar vazio\n")
                continue
            
            username = input("👤 Username (Enter para 'test_user'): ").strip() or "test_user"
            projeto = input("📁 Projeto (Enter para 'test_project'): ").strip() or "test_project"
            
            # Chama o agente diretamente
            state = {
                'pergunta': pergunta,
                'plan': plan,
                'username': username,
                'projeto': projeto,
                'plan_steps': [],
                'estimated_complexity': 'média'
            }
            
            result = agent.confirm_plan(state)
            
            print(f"\n{'='*80}")
            print(f"📊 RESULTADO:")
            print(f"{'='*80}")
            print(f"✓ Confirmado: {result['confirmed']}")
            print(f"✓ Método: {result['confirmation_method']}")
            print(f"✓ Feedback: {result['user_feedback']}")
            print(f"{'='*80}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Até logo!\n")
            break
        except Exception as e:
            print(f"\n❌ Erro: {str(e)}\n")


def run_interactive():
    """Modo interativo via servidor (para teste de API)"""
    print(f"\n{'='*80}")
    print(f"🎮 MODO INTERATIVO - PLAN CONFIRM (via API)")
    print(f"{'='*80}")
    print(f"⚠️  Este modo requer o servidor rodando em outro terminal!")
    print(f"   Execute: ./run_test.sh server")
    print(f"{'='*80}")
    print(f"Digite 'sair' para encerrar\n")
    
    while True:
        try:
            pergunta = input("📝 Digite a pergunta: ").strip()
            
            if pergunta.lower() in ['sair', 'exit', 'quit']:
                print("\n👋 Até logo!\n")
                break
            
            if not pergunta:
                print("⚠️  Pergunta não pode estar vazia\n")
                continue
            
            plan = input("📋 Digite o plano: ").strip()
            
            if not plan:
                print("⚠️  Plano não pode estar vazio\n")
                continue
            
            username = input("👤 Username (Enter para 'test_user'): ").strip() or "test_user"
            projeto = input("📁 Projeto (Enter para 'test_project'): ").strip() or "test_project"
            
            test_plan_confirm(pergunta, plan, username, projeto)
            
        except KeyboardInterrupt:
            print("\n\n👋 Até logo!\n")
            break
        except Exception as e:
            print(f"\n❌ Erro: {str(e)}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode in ['examples', 'e']:
            run_examples()
        elif mode in ['interactive', 'i']:
            run_interactive_direct()  # Modo direto por padrão
        elif mode in ['api']:
            run_interactive()  # Modo via API
        else:
            print(f"❌ Modo desconhecido: {mode}")
            print("Modos disponíveis: examples, interactive, api")
    else:
        # Modo padrão: exemplos
        run_examples()
