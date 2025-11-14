"""
Cliente de teste para o User Proposed Plan Agent
Testa o agente através do endpoint Flask
"""

import requests
import json
import sys
import time
from typing import Dict, Any

# URL do endpoint
BASE_URL = "http://localhost:5011"
ENDPOINT = f"{BASE_URL}/test-user-proposed-plan"


def test_user_proposed_plan(
    pergunta: str,
    user_proposed_plan: str,
    username: str = "test_user",
    projeto: str = "test_project"
) -> Dict[str, Any]:
    """
    Testa o User Proposed Plan Agent com os dados fornecidos
    
    Args:
        pergunta: Pergunta do usuário
        user_proposed_plan: Sugestão do usuário sobre o que fazer
        username: Nome do usuário
        projeto: Nome do projeto
        
    Returns:
        Dicionário com resultado do teste
    """
    payload = {
        "pergunta": pergunta,
        "user_proposed_plan": user_proposed_plan,
        "username": username,
        "projeto": projeto
    }
    
    try:
        print(f"\n{'='*80}")
        print(f"📤 Enviando requisição...")
        print(f"   Pergunta: {pergunta}")
        print(f"   Sugestão: {user_proposed_plan[:80]}..." if len(user_proposed_plan) > 80 else f"   Sugestão: {user_proposed_plan}")
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
            "name": "Exemplo 1: Sugestão simples",
            "pergunta": "Quantos pedidos tivemos este mês?",
            "user_proposed_plan": "Consultar a tabela report_orders e contar os pedidos do mês atual"
        },
        {
            "name": "Exemplo 2: Sugestão com SQL",
            "pergunta": "Qual o valor total de receita?",
            "user_proposed_plan": "SELECT SUM(amount) FROM report_orders WHERE status = 'paid'"
        },
        {
            "name": "Exemplo 3: Sugestão detalhada",
            "pergunta": "Quem são os clientes inadimplentes?",
            "user_proposed_plan": "Buscar na tabela report_orders todos os registros com status = 'overdue', agrupar por cliente e mostrar nome e valor devido"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{'='*80}")
        print(f"📝 {example['name']}")
        print(f"{'='*80}")
        
        result = test_user_proposed_plan(
            pergunta=example['pergunta'],
            user_proposed_plan=example['user_proposed_plan']
        )
        
        if result and result.get('success'):
            print(f"✅ Teste {i} passou!")
        else:
            print(f"❌ Teste {i} falhou!")
        
        if i < len(examples):
            print("\n⏳ Aguardando 2 segundos antes do próximo teste...")
            time.sleep(2)
    
    print(f"\n{'='*80}")
    print(f"✅ Todos os exemplos foram executados!")
    print(f"{'='*80}\n")


def run_interactive():
    """Modo interativo para sugerir o que fazer"""
    print("\n" + "="*80)
    print("🔧 MODO INTERATIVO")
    print("="*80)
    print("Digite o que você quer que a IA faça")
    print("Digite 'sair' para encerrar")
    print("="*80 + "\n")
    
    while True:
        try:
            user_plan = input("💡 O que você quer que a IA faça? ").strip()
            
            if user_plan.lower() == 'sair':
                print("\n👋 Encerrando modo interativo...")
                break
            
            if not user_plan:
                print("❌ Sugestão não pode estar vazia!\n")
                continue
            
            pergunta = input("📝 Contexto/Pergunta original (opcional): ").strip() or "Requisição do usuário"
            
            username = input("👤 Username (Enter para 'test_user'): ").strip() or "test_user"
            projeto = input("📁 Projeto (Enter para 'test_project'): ").strip() or "test_project"
            
            result = test_user_proposed_plan(
                pergunta=pergunta,
                user_proposed_plan=user_plan,
                username=username,
                projeto=projeto
            )
            
            if result and result.get('success'):
                print(f"\n✅ Sugestão registrada com sucesso!")
            else:
                print(f"\n❌ Erro ao registrar sugestão")
            
            print("\n" + "-"*80 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Encerrando modo interativo...")
            break
        except Exception as e:
            print(f"\n❌ Erro: {e}\n")


def main():
    """Função principal"""
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "interactive" or mode == "i":
            run_interactive()
        elif mode == "examples" or mode == "e":
            run_examples()
        else:
            print(f"❌ Modo desconhecido: {mode}")
            print("Modos disponíveis: interactive, examples")
    else:
        print("Uso: python test_client.py [interactive|examples]")
        print("  interactive - Modo interativo")
        print("  examples    - Executa exemplos pré-definidos")


if __name__ == "__main__":
    main()
