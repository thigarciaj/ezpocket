#!/usr/bin/env python3
"""
Cliente de teste para o Graph Orchestrator Test Endpoint
Facilita testes rápidos do orquestrador sem precisar usar curl
"""

import requests
import json
import sys
import time
from typing import Dict, Any


BASE_URL = "http://localhost:5008"


def test_orchestrator(pergunta: str, username: str = "test_user", projeto: str = "test_project", module: str = "intent_validator") -> Dict[str, Any]:
    """
    Testa o Graph Orchestrator com uma pergunta
    
    Args:
        pergunta: Pergunta para processar
        username: Username opcional
        projeto: Projeto opcional
        module: Módulo inicial (default: intent_validator)
        
    Returns:
        Resposta do endpoint
    """
    url = f"{BASE_URL}/test-orchestrator"
    
    payload = {
        "pergunta": pergunta,
        "username": username,
        "projeto": projeto,
        "module": module
    }
    
    try:
        print(f"\n{'='*80}")
        print(f"🔄 TESTANDO GRAPH ORCHESTRATOR")
        print(f"{'='*80}")
        print(f"📝 Pergunta: {pergunta}")
        print(f"👤 Username: {username}")
        print(f"📁 Projeto: {projeto}")
        print(f"🎯 Módulo: {module}")
        print(f"{'='*80}\n")
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ SUCESSO - JOB SUBMETIDO")
            print(f"\n{'='*80}")
            print(f"📊 DETALHES DO JOB")
            print(f"{'='*80}")
            print(f"✓ Job ID: {result['job_id']}")
            print(f"✓ Módulo: {result['module']}")
            print(f"✓ Fluxo esperado: {result['expected_flow']}")
            
            print(f"\n{'='*80}")
            print(f"⏳ MONITORANDO STATUS")
            print(f"{'='*80}")
            
            # Monitora status por até 30s
            for i in range(30):
                time.sleep(1)
                status_result = get_job_status(result['job_id'], silent=True)
                
                if status_result:
                    status_info = status_result.get('status', {})
                    current_status = status_info.get('status', 'unknown')
                    
                    print(f"[{i+1}s] Status: {current_status}")
                    
                    if current_status == 'completed':
                        print(f"\n{'='*80}")
                        print(f"✅ JOB COMPLETADO COM SUCESSO")
                        print(f"{'='*80}")
                        print(json.dumps(status_info, indent=2, ensure_ascii=False))
                        print(f"{'='*80}\n")
                        return result
                    
                    if current_status == 'error':
                        print(f"\n{'='*80}")
                        print(f"❌ JOB FALHOU")
                        print(f"{'='*80}")
                        print(json.dumps(status_info, indent=2, ensure_ascii=False))
                        print(f"{'='*80}\n")
                        return None
            
            print(f"\n⚠️  Timeout: Job ainda em processamento após 30s")
            print(f"{'='*80}\n")
            
            return result
        else:
            print(f"❌ ERRO: {response.status_code}")
            print(response.json())
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERRO: Não foi possível conectar ao servidor em {BASE_URL}")
        print(f"💡 Certifique-se de que o servidor está rodando:")
        print(f"   python agents/graph_orchestrator/test_endpoint.py\n")
        return None
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}\n")
        return None


def get_job_status(job_id: str, silent: bool = False) -> Dict[str, Any]:
    """Consulta status de um job"""
    url = f"{BASE_URL}/test-orchestrator/status/{job_id}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if not silent:
                print(f"✅ Status obtido")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        return None
    except:
        return None


def get_health() -> bool:
    """Verifica se o servidor está rodando"""
    url = f"{BASE_URL}/test-orchestrator/health"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Servidor está rodando")
            print(f"   Status: {data['status']}")
            print(f"   Service: {data['service']}")
            print(f"   Version: {data['version']}")
            print(f"   Redis: {data['redis_status']}\n")
            return True
        return False
    except:
        return False


def get_examples() -> None:
    """Obtém exemplos de uso do endpoint"""
    url = f"{BASE_URL}/test-orchestrator/examples"
    
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
                print(f"   Fluxo esperado: {example['expected_result']['expected_flow']}\n")
            
            print(f"{'='*80}\n")
    except:
        print("❌ Não foi possível obter exemplos\n")


def run_all_examples() -> None:
    """Executa todos os exemplos"""
    url = f"{BASE_URL}/test-orchestrator/examples"
    
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
                
                test_orchestrator(
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
    print(f"🎮 MODO INTERATIVO - GRAPH ORCHESTRATOR")
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
            module = input("🎯 Módulo (Enter para 'intent_validator'): ").strip() or "intent_validator"
            
            test_orchestrator(pergunta, username, projeto, module)
            
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
🔄 CLIENTE DE TESTE - GRAPH ORCHESTRATOR
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
        
        test_orchestrator(pergunta, username, projeto)
    
    else:
        print(f"❌ Comando desconhecido: {command}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()

