"""
Cliente de teste para o Analysis Orchestrator Agent
Testa o agente através do endpoint Flask
"""

import requests
import json
import sys
import time
from typing import Dict, Any


# URL do endpoint
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
load_dotenv(env_path)

BASE_URL = f"http://localhost:{os.getenv('ANALYSIS_ORCHESTRATOR_PORT', '5012')}"
ENDPOINT = f"{BASE_URL}/test-analysis-orchestrator"


def test_analysis_orchestrator(
    plan: str,
    pergunta: str = "",
    username: str = "test_user",
    projeto: str = "test_project"
) -> Dict[str, Any]:
    """
    Testa o Analysis Orchestrator Agent com um plano
    
    Args:
        plan: Plano de análise em linguagem natural
        pergunta: Pergunta original do usuário (opcional)
        username: Nome do usuário
        projeto: Nome do projeto
        
    Returns:
        Dicionário com resultado do teste
    """
    payload = {
        "pergunta": pergunta or plan,
        "plan": plan,
        "username": username,
        "projeto": projeto
    }
    
    try:
        print(f"\n{'='*80}")
        print(f"📤 Enviando plano para análise...")
        print(f"   Plano: {plan[:80]}..." if len(plan) > 80 else f"   Plano: {plan}")
        print(f"{'='*80}\n")
        
        response = requests.post(ENDPOINT, json=payload, timeout=60)
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
            "name": "Exemplo 1: Vendas hoje",
            "plan": "Gostaria de saber quantas vendas tivemos hoje. Por favor, conte os pedidos criados na data de hoje."
        },
        {
            "name": "Exemplo 2: Top 5 produtos mais vendidos",
            "plan": "Mostre os 5 produtos mais vendidos, ordenados pela quantidade de vendas."
        },
        {
            "name": "Exemplo 3: Total recebido",
            "plan": "Qual o valor total que já recebemos de todos os pedidos?"
        },
        {
            "name": "Exemplo 4: Inadimplentes",
            "plan": "Quantos clientes estão inadimplentes (status default N1 a N7)?"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{'='*80}")
        print(f"📝 {example['name']}")
        print(f"{'='*80}")
        
        result = test_analysis_orchestrator(plan=example['plan'])
        
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
    """Modo interativo para testar planos de análise"""
    print("\n" + "="*80)
    print("🔧 MODO INTERATIVO")
    print("="*80)
    print("Digite o plano de análise que você quer transformar em SQL")
    print("Digite 'sair' para encerrar")
    print("="*80 + "\n")
    
    while True:
        try:
            pergunta = input("❓ Pergunta do usuário: ").strip()
            
            if pergunta.lower() == 'sair':
                print("\n👋 Encerrando modo interativo...")
                break
            
            if not pergunta:
                print("❌ Pergunta não pode estar vazia!\n")
                continue
            
            plan = input("📋 Plano de análise (Enter para usar a pergunta): ").strip() or pergunta
            
            username = input("👤 Username (Enter para 'test_user'): ").strip() or "test_user"
            projeto = input("📁 Projeto (Enter para 'test_project'): ").strip() or "test_project"
            
            result = test_analysis_orchestrator(
                pergunta=pergunta,
                plan=plan,
                username=username,
                projeto=projeto
            )
            
            if result and result.get('success'):
                print(f"\n✅ Query gerada com sucesso!")
                if 'query_sql' in result.get('data', {}):
                    print(f"\n📊 SQL Gerado:")
                    print(f"{'='*80}")
                    print(result['data']['query_sql'])
                    print(f"{'='*80}")
            else:
                print(f"\n❌ Erro ao gerar query")
            
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
