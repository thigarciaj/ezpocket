#!/usr/bin/env python3
"""
Cliente de teste para o Intent Validator Test Endpoint
Facilita testes rápidos do nó sem precisar usar curl
"""

import requests
import json
import sys
from typing import Dict, Any


import os
from dotenv import load_dotenv

# Carrega variáveis do .env
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
load_dotenv(env_path)

BASE_URL = f"http://localhost:{os.getenv('INTENT_VALIDATOR_PORT', '5001')}"


def test_intent_validator(pergunta: str, username: str = "test_user", projeto: str = "test_project") -> Dict[str, Any]:
    """
    Testa o Intent Validator com uma pergunta
    
    Args:
        pergunta: Pergunta para validar
        username: Username opcional
        projeto: Projeto opcional
        
    Returns:
        Resposta do endpoint
    """
    url = f"{BASE_URL}/test-intent-validator"
    
    payload = {
        "pergunta": pergunta,
        "username": username,
        "projeto": projeto
    }
    
    try:
        print(f"\n{'='*80}")
        print(f"🧪 TESTANDO INTENT VALIDATOR")
        print(f"{'='*80}")
        print(f"📝 Pergunta: {pergunta}")
        print(f"👤 Username: {username}")
        print(f"📁 Projeto: {projeto}")
        print(f"{'='*80}\n")
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ SUCESSO")
            print(f"\n{'='*80}")
            print(f"📊 RESULTADO DA VALIDAÇÃO")
            print(f"{'='*80}")
            print(f"✓ Intent Válida: {result['output']['intent_valid']}")
            print(f"✓ Categoria: {result['output']['intent_category']}")
            print(f"✓ Razão: {result['output']['intent_reason']}")
            
            if result['output'].get('is_special_case'):
                print(f"✓ Caso Especial: {result['output']['special_type']}")
            
            print(f"\n{'='*80}")
            print(f"🔀 ROTEAMENTO")
            print(f"{'='*80}")
            print(f"→ Decisão: {result['route_decision']}")
            print(f"→ Próximo Nó: {result['next_node']}")
            
            if result.get('out_of_scope_response'):
                print(f"\n{'='*80}")
                print(f"❌ RESPOSTA PARA FORA DO ESCOPO")
                print(f"{'='*80}")
                print(result['out_of_scope_response'])
            
            print(f"\n{'='*80}\n")
            
            return result
        else:
            print(f"❌ ERRO: {response.status_code}")
            print(response.json())
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERRO: Não foi possível conectar ao servidor em {BASE_URL}")
        print(f"💡 Certifique-se de que o servidor está rodando:")
        print(f"   python agents/intent_validator_agent/test_endpoint.py\n")
        return None
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}\n")
        return None


def get_health() -> bool:
    """Verifica se o servidor está rodando"""
    url = f"{BASE_URL}/test-intent-validator/health"
    
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
    url = f"{BASE_URL}/test-intent-validator/examples"
    
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
                print(f"   Resultado esperado: {example['expected_result']['intent_category']}")
                print(f"   Próximo nó: {example['expected_result']['next_node']}\n")
            
            print(f"{'='*80}\n")
    except:
        print("❌ Não foi possível obter exemplos\n")


def run_all_examples() -> None:
    """Executa todos os exemplos"""
    url = f"{BASE_URL}/test-intent-validator/examples"
    
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
                
                test_intent_validator(
                    pergunta=example['request']['pergunta'],
                    username=example['request']['username'],
                    projeto=example['request']['projeto']
                )
                
                input("Pressione Enter para continuar...")
    except:
        print("❌ Não foi possível executar exemplos\n")


def interactive_mode() -> None:
    """Modo interativo para testar perguntas"""
    print(f"\n{'='*80}")
    print(f"🎮 MODO INTERATIVO - INTENT VALIDATOR")
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
            
            username = input("👤 Username (Enter para 'test_user'): ").strip() or "test_user"
            projeto = input("📁 Projeto (Enter para 'test_project'): ").strip() or "test_project"
            
            test_intent_validator(pergunta, username, projeto)
            
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
🧪 CLIENTE DE TESTE - INTENT VALIDATOR AGENT
{'='*80}

Uso:
  python test_client.py health              - Verificar se servidor está rodando
  python test_client.py examples            - Ver exemplos de uso
  python test_client.py run-examples        - Executar todos os exemplos
  python test_client.py interactive         - Modo interativo
  python test_client.py test "<pergunta>"   - Testar uma pergunta

Exemplos:
  python test_client.py health
  python test_client.py test "Quantos pedidos temos?"
  python test_client.py test "Qual a receita de bolo?" test_user projeto_abc
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
        if len(sys.argv) < 3:
            print("❌ Erro: Especifique a pergunta")
            print("Uso: python test_client.py test \"<pergunta>\" [username] [projeto]\n")
            sys.exit(1)
        
        if not get_health():
            print("❌ Servidor não está rodando. Inicie o servidor primeiro.\n")
            sys.exit(1)
        
        pergunta = sys.argv[2]
        username = sys.argv[3] if len(sys.argv) > 3 else "test_user"
        projeto = sys.argv[4] if len(sys.argv) > 4 else "test_project"
        
        test_intent_validator(pergunta, username, projeto)
    
    else:
        print(f"❌ Comando desconhecido: {command}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
