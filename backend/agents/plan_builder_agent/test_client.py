#!/usr/bin/env python3
"""
Cliente de teste para o Plan Builder Test Endpoint
Facilita testes rápidos do nó sem precisar usar curl
"""

import requests
import json
import sys
from typing import Dict, Any


BASE_URL = "http://localhost:5009"


def test_plan_builder(pergunta: str, intent_category: str, username: str = "test_user", projeto: str = "test_project") -> Dict[str, Any]:
    """
    Testa o Plan Builder com uma pergunta
    
    Args:
        pergunta: Pergunta para construir plano
        intent_category: Categoria da intenção
        username: Username opcional
        projeto: Projeto opcional
        
    Returns:
        Resposta do endpoint
    """
    url = f"{BASE_URL}/test-plan-builder"
    
    payload = {
        "pergunta": pergunta,
        "intent_category": intent_category,
        "username": username,
        "projeto": projeto
    }
    
    try:
        print(f"\n{'='*80}")
        print(f"🧪 TESTANDO PLAN BUILDER")
        print(f"{'='*80}")
        print(f"📝 Pergunta: {pergunta}")
        print(f"🏷️  Categoria: {intent_category}")
        print(f"👤 Username: {username}")
        print(f"📁 Projeto: {projeto}")
        print(f"{'='*80}\n")
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ SUCESSO")
            print(f"\n{'='*80}")
            print(f"📋 PLANO DE EXECUÇÃO")
            print(f"{'='*80}")
            print(f"\n{result['output']['plan']}\n")
            
            print(f"{'='*80}")
            print(f"📊 PASSOS DO PLANO")
            print(f"{'='*80}")
            for i, step in enumerate(result['output']['plan_steps'], 1):
                print(f"{i}. {step}")
            
            print(f"\n{'='*80}")
            print(f"📈 ANÁLISE")
            print(f"{'='*80}")
            print(f"✓ Complexidade Estimada: {result['output']['estimated_complexity']}")
            print(f"✓ Fontes de Dados: {', '.join(result['output']['data_sources'])}")
            print(f"✓ Formato de Saída: {result['output']['output_format']}")
            
            print(f"\n{'='*80}")
            print(f"⚡ PERFORMANCE")
            print(f"{'='*80}")
            print(f"✓ Tempo de Execução: {result['output']['execution_time']:.3f}s")
            print(f"✓ Modelo Usado: {result['output']['model_used']}")
            print(f"✓ Tokens Usados: {result['output']['tokens_used']}")
            
            print(f"\n{'='*80}\n")
            
            return result
        else:
            print(f"❌ ERRO: {response.status_code}")
            print(response.json())
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERRO: Não foi possível conectar ao servidor em {BASE_URL}")
        print(f"💡 Certifique-se de que o servidor está rodando:")
        print(f"   python agents/plan_builder_agent/test_endpoint.py\n")
        return None
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}\n")
        return None


def get_health() -> bool:
    """Verifica se o servidor está rodando"""
    url = f"{BASE_URL}/test-plan-builder/health"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Servidor está rodando")
            print(f"   Status: {data['status']}")
            print(f"   Service: {data['service']}")
            print(f"   Version: {data['version']}\n")
            return True
        return False
    except:
        return False


def get_examples() -> None:
    """Obtém exemplos de uso do endpoint"""
    url = f"{BASE_URL}/test-plan-builder/examples"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n{'='*80}")
            print(f"📚 EXEMPLOS DE USO")
            print(f"{'='*80}\n")
            
            for i, example in enumerate(data['examples'], 1):
                print(f"{i}. {example['name']}")
                print(f"   Pergunta: \"{example['request']['pergunta']}\"")
                print(f"   Categoria: {example['request']['intent_category']}")
                print(f"   Complexidade esperada: {example['expected_result']['estimated_complexity']}")
                print(f"   Passos: {example['expected_result']['plan_steps_count']}\n")
            
            print(f"{'='*80}\n")
    except:
        print("❌ Não foi possível obter exemplos\n")


def run_all_examples() -> None:
    """Executa todos os exemplos"""
    url = f"{BASE_URL}/test-plan-builder/examples"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n{'='*80}")
            print(f"🚀 EXECUTANDO TODOS OS EXEMPLOS")
            print(f"{'='*80}\n")
            
            for i, example in enumerate(data['examples'], 1):
                print(f"\n{'='*80}")
                print(f"EXEMPLO {i}: {example['name']}")
                print(f"{'='*80}")
                
                test_plan_builder(
                    pergunta=example['request']['pergunta'],
                    intent_category=example['request']['intent_category'],
                    username=example['request']['username'],
                    projeto=example['request']['projeto']
                )
                
                input("Pressione Enter para continuar...")
    except:
        print("❌ Não foi possível executar exemplos\n")


def interactive_mode() -> None:
    """Modo interativo para testar perguntas"""
    print(f"\n{'='*80}")
    print(f"🎮 MODO INTERATIVO - PLAN BUILDER")
    print(f"{'='*80}")
    print(f"Digite 'sair' para encerrar\n")
    
    categories = ["quantidade", "conhecimentos_gerais", "analise_estatistica", "comparacao"]
    
    while True:
        try:
            pergunta = input("📝 Digite a pergunta: ").strip()
            
            if pergunta.lower() in ['sair', 'exit', 'quit']:
                print("\n👋 Até logo!\n")
                break
            
            if not pergunta:
                print("⚠️  Pergunta não pode estar vazia\n")
                continue
            
            print(f"\n🏷️  Categorias disponíveis:")
            for i, cat in enumerate(categories, 1):
                print(f"   {i}. {cat}")
            
            cat_choice = input(f"\nEscolha a categoria (1-{len(categories)} ou nome): ").strip()
            
            # Tenta converter para número
            try:
                cat_idx = int(cat_choice) - 1
                if 0 <= cat_idx < len(categories):
                    intent_category = categories[cat_idx]
                else:
                    intent_category = cat_choice
            except ValueError:
                intent_category = cat_choice
            
            username = input("👤 Username (Enter para 'test_user'): ").strip() or "test_user"
            projeto = input("📁 Projeto (Enter para 'test_project'): ").strip() or "test_project"
            
            test_plan_builder(pergunta, intent_category, username, projeto)
            
        except KeyboardInterrupt:
            print("\n\n👋 Até logo!\n")
            break
        except Exception as e:
            print(f"\n❌ Erro: {str(e)}\n")


def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print(f"""
{'='*80}
🧪 CLIENTE DE TESTE - PLAN BUILDER AGENT
{'='*80}

Uso:
  python test_client.py health                    - Verificar se servidor está rodando
  python test_client.py examples                  - Ver exemplos de uso
  python test_client.py run-examples              - Executar todos os exemplos
  python test_client.py interactive               - Modo interativo
  python test_client.py test "<pergunta>" <cat>   - Testar uma pergunta

Exemplos:
  python test_client.py health
  python test_client.py test "Quantos pedidos temos?" quantidade
  python test_client.py test "O que é EZPocket?" conhecimentos_gerais test_user projeto_abc
  python test_client.py interactive

{'='*80}
        """)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'health':
        if not get_health():
            print("❌ Servidor não está rodando\n")
            sys.exit(1)
    
    elif command == 'examples':
        get_examples()
    
    elif command == 'run-examples':
        if not get_health():
            print("❌ Servidor não está rodando. Inicie o servidor primeiro.\n")
            sys.exit(1)
        run_all_examples()
    
    elif command == 'interactive':
        if not get_health():
            print("❌ Servidor não está rodando. Inicie o servidor primeiro.\n")
            sys.exit(1)
        interactive_mode()
    
    elif command == 'test':
        if len(sys.argv) < 4:
            print("❌ Erro: Especifique a pergunta e categoria")
            print("Uso: python test_client.py test \"<pergunta>\" <categoria> [username] [projeto]\n")
            sys.exit(1)
        
        if not get_health():
            print("❌ Servidor não está rodando. Inicie o servidor primeiro.\n")
            sys.exit(1)
        
        pergunta = sys.argv[2]
        intent_category = sys.argv[3]
        username = sys.argv[4] if len(sys.argv) > 4 else "test_user"
        projeto = sys.argv[5] if len(sys.argv) > 5 else "test_project"
        
        test_plan_builder(pergunta, intent_category, username, projeto)
    
    else:
        print(f"❌ Comando desconhecido: {command}\n")
        main()


if __name__ == '__main__':
    main()
