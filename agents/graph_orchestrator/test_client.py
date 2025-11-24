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


import os
from dotenv import load_dotenv

# Carrega variáveis do .env
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
load_dotenv(env_path)

BASE_URL = f"http://localhost:{os.getenv('GRAPH_ORCHESTRATOR_PORT', '5008')}"

# Emojis e títulos para cada módulo
MODULE_DISPLAY = {
    'intent_validator': {
        'emoji': '🛡️',
        'title': 'INTENT VALIDATOR',
        'color': '\033[94m'  # Azul
    },
    'plan_builder': {
        'emoji': '📋',
        'title': 'PLAN BUILDER',
        'color': '\033[92m'  # Verde
    },
    'plan_confirm': {
        'emoji': '✅',
        'title': 'PLAN CONFIRM',
        'color': '\033[96m'  # Ciano
    },
    'history_preferences': {
        'emoji': '🧠',
        'title': 'HISTORY & PREFERENCES',
        'color': '\033[95m'  # Magenta
    },
    'router': {
        'emoji': '🔀',
        'title': 'ROUTER',
        'color': '\033[93m'  # Amarelo
    },
    'generator': {
        'emoji': '⚙️',
        'title': 'QUERY GENERATOR',
        'color': '\033[96m'  # Ciano
    },
    'analysis_orchestrator': {
        'emoji': '🔧',
        'title': 'ANALYSIS ORCHESTRATOR',
        'color': '\033[93m'  # Amarelo
    },
    'sql_validator': {
        'emoji': '🔍',
        'title': 'SQL VALIDATOR',
        'color': '\033[96m'  # Ciano
    },
    'auto_correction': {
        'emoji': '🔧',
        'title': 'AUTO CORRECTION',
        'color': '\033[93m'  # Amarelo
    },
    'athena_executor': {
        'emoji': '⚡',
        'title': 'ATHENA EXECUTOR',
        'color': '\033[95m'  # Magenta
    },
    'python_runtime': {
        'emoji': '🐍',
        'title': 'PYTHON RUNTIME',
        'color': '\033[92m'  # Verde
    },
    'response_composer': {
        'emoji': '🎨',
        'title': 'RESPONSE COMPOSER',
        'color': '\033[94m'  # Azul
    },
    'user_feedback': {
        'emoji': '📊',
        'title': 'USER FEEDBACK',
        'color': '\033[96m'  # Ciano
    }
}

RESET_COLOR = '\033[0m'


def print_formatted_result(status_info: Dict[str, Any]) -> None:
    """Formata e imprime o resultado com títulos bonitos para cada módulo"""
    
    execution_chain = status_info.get('execution_chain', [])
    branch_details = status_info.get('branch_details', [])
    
    print(f"\n📊 RESUMO DA EXECUÇÃO:")
    print(f"   Job ID: {status_info.get('job_id')}")
    print(f"   Pergunta: {status_info.get('data', {}).get('pergunta', 'N/A')}")
    print(f"   Username: {status_info.get('username')}")
    print(f"   Projeto: {status_info.get('projeto')}")
    
    if branch_details:
        print(f"\n🔀 BRANCHES PARALELAS: {len(branch_details)}")
        for branch in branch_details:
            status_emoji = '✅' if branch['status'] == 'completed' else '⏳'
            print(f"   {status_emoji} {branch['module']} (Job ID: {branch['job_id'][:8]}...)")
    
    print(f"\n{'='*80}")
    print(f"📜 EXECUTION CHAIN ({len(execution_chain)} etapas)")
    print(f"{'='*80}\n")
    
    for i, step in enumerate(execution_chain, 1):
        module = step.get('module', 'unknown')
        module_info = MODULE_DISPLAY.get(module, {
            'emoji': '❓',
            'title': module.upper(),
            'color': '\033[97m'
        })
        
        print(f"\n{'─'*80}")
        print(f"{module_info['emoji']}  ETAPA {i}: {module_info['title']}")
        print(f"{'─'*80}")
        
        # Tempo de execução
        exec_time = step.get('execution_time', 0)
        print(f"⏱️  Tempo: {exec_time:.3f}s")
        print(f"✓ Sucesso: {step.get('success', False)}")
        print(f"🕐 Timestamp: {step.get('timestamp', 'N/A')}")
        
        # Output principal
        output = step.get('output', {})
        
        if module == 'intent_validator':
            print(f"\n📤 OUTPUT:")
            print(f"   ✓ Intent Válida: {output.get('intent_valid', False)}")
            print(f"   📂 Categoria: {output.get('intent_category', 'N/A')}")
            print(f"   💬 Razão: {output.get('intent_reason', 'N/A')}")
            print(f"   🔒 Violação de Segurança: {output.get('security_violation', False)}")
            print(f"   🪙 Tokens: {output.get('tokens_used', 0)}")
            
        elif module == 'plan_builder':
            print(f"\n📤 OUTPUT:")
            print(f"   📋 Plano: {output.get('plan', 'N/A')}")
            steps = output.get('plan_steps', [])
            if steps:
                print(f"   📊 Passos ({len(steps)}):")
                for j, step_text in enumerate(steps, 1):
                    print(f"      {j}. {step_text}")
            print(f"   ⚡ Complexidade: {output.get('estimated_complexity', 'N/A')}")
            print(f"   💾 Fontes: {', '.join(output.get('data_sources', []))}")
            print(f"   📈 Formato: {output.get('output_format', 'N/A')}")
            print(f"   🪙 Tokens: {output.get('tokens_used', 0)}")
            
        elif module == 'plan_confirm':
            print(f"\n📤 OUTPUT:")
            print(f"   ✅ Confirmado: {output.get('confirmed', False)}")
            print(f"   📝 Método: {output.get('confirmation_method', 'N/A')}")
            print(f"   💬 Feedback: {output.get('user_feedback', 'N/A')}")
            print(f"   ✓ Plano Aceito: {output.get('plan_accepted', False)}")
            
        elif module == 'history_preferences':
            print(f"\n📤 OUTPUT:")
            print(f"   💾 Context Loaded: {output.get('context_loaded', False)}")
            print(f"   ✅ Interaction Saved: {output.get('interaction_saved', False)}")
            if output.get('interaction_id'):
                print(f"   🆔 Interaction ID: {output.get('interaction_id')}")
            print(f"   ⏱️  Execution Time: {output.get('execution_time', 0)}s")
        
        else:
            # Módulo desconhecido - mostrar output genérico
            print(f"\n📤 OUTPUT:")
            for key, value in output.items():
                if key not in ['username', 'projeto', 'pergunta', 'previous_module']:
                    print(f"   • {key}: {value}")
    
    print(f"\n{'='*80}")


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
            
            print(f"\n{'='*80}")
            print(f"⏳ MONITORANDO STATUS")
            print(f"{'='*80}")
            
            username = payload.get('username', 'test_user')
            projeto = payload.get('projeto', 'test_project')
            confirmation_checked = False
            
            # Monitora status por até 5 minutos (300s)
            for i in range(300):
                time.sleep(1)
                
                # Checar se há confirmação pendente ou sugestão do usuário a cada 2 segundos
                if i > 3 and i % 2 == 0:
                    try:
                        import redis
                        redis_port = int(os.getenv('REDIS_PORT', 6493))
                        redis_client = redis.Redis(host='localhost', port=redis_port, decode_responses=True)
                        
                        # Verificar plan_confirm
                        if not confirmation_checked:
                            pending_key = f"plan_confirm:pending:{username}:{projeto}"
                            response_key = f"plan_confirm:response:{username}:{projeto}"
                            
                            if redis_client.exists(pending_key):
                                confirmation_checked = True
                                
                                # Ler dados do plano do Redis
                                plan_data = redis_client.hgetall(pending_key)
                                
                                print(f"\n{'='*80}")
                                print(f"⏸️  CONFIRMAÇÃO NECESSÁRIA!")
                                print(f"{'='*80}")
                                print(f"📋 Plano: {plan_data.get('plan', '')}")
                                print(f"\n📊 Passos:")
                                
                                plan_steps = json.loads(plan_data.get('plan_steps', '[]'))
                                for idx, step in enumerate(plan_steps, 1):
                                    print(f"   {idx}. {step}")
                                
                                print(f"\n{'='*80}")
                                print(f"🤔 Deseja prosseguir com este plano? (s/n): ", end='', flush=True)
                                
                                # Ler resposta do usuário
                                user_response = input().strip().lower()
                                confirmed = user_response in ['s', 'sim', 'y', 'yes']
                                
                                # Salvar resposta no Redis
                                redis_client.set(response_key, str(confirmed).lower(), ex=60)
                                
                                status_msg = "✅ APROVADO" if confirmed else "❌ REJEITADO"
                                print(f"{status_msg} - Continuando processamento...")
                                print(f"{'='*80}\n")
                        
                        # Verificar user_feedback (sempre verificar)
                        feedback_key = f"user_feedback:pending:{username}:{projeto}"
                        feedback_response_key = f"user_feedback:response:{username}:{projeto}"
                        
                        if redis_client.exists(feedback_key):
                            # Ler dados do feedback do Redis
                            feedback_data = redis_client.hgetall(feedback_key)
                            
                            print(f"\n{'='*80}")
                            print(f"📊 AVALIAÇÃO DA RESPOSTA")
                            print(f"{'='*80}")
                            print(f"❓ Pergunta: {feedback_data.get('pergunta', '')}")
                            print(f"\n💬 Resposta:")
                            print(f"{feedback_data.get('response_text', '')}")
                            print(f"\n{'='*80}")
                            print(f"⭐ Como você avalia esta resposta?")
                            print(f"   1 = Péssima")
                            print(f"   2 = Ruim")
                            print(f"   3 = Regular")
                            print(f"   4 = Boa")
                            print(f"   5 = Excelente")
                            
                            # Ler rating do usuário
                            while True:
                                try:
                                    rating_input = input("\nDigite o rating (1-5): ").strip()
                                    rating = int(rating_input)
                                    if 1 <= rating <= 5:
                                        break
                                    print("❌ Rating deve ser entre 1 e 5")
                                except ValueError:
                                    print("❌ Digite um número válido")
                            
                            # Pedir comentário opcional
                            comment = input("\n💭 Comentário (Enter para pular): ").strip()
                            
                            # Salvar resposta no Redis
                            feedback_response = {
                                'rating': rating,
                                'comment': comment
                            }
                            redis_client.set(feedback_response_key, json.dumps(feedback_response), ex=60)
                            
                            print(f"\n✅ Feedback registrado!")
                            print(f"{'='*80}\n")
                        
                        # Verificar user_proposed_plan (sempre verificar, pode acontecer múltiplas vezes)
                        user_plan_key = f"user_proposed_plan:pending:{username}:{projeto}"
                        user_plan_response_key = f"user_proposed_plan:response:{username}:{projeto}"
                        
                        if redis_client.exists(user_plan_key):
                            # Ler contexto
                            user_plan_data = redis_client.hgetall(user_plan_key)
                            
                            print(f"\n{'='*80}")
                            print(f"💡 SUGESTÃO DO USUÁRIO NECESSÁRIA!")
                            print(f"{'='*80}")
                            print(f"📝 Pergunta original: {user_plan_data.get('pergunta', '')}")
                            print(f"❌ O plano anterior foi rejeitado")
                            print(f"\n{'='*80}")
                            print(f"💬 O que você quer que a IA faça? ", end='', flush=True)
                            
                            # Ler sugestão do usuário
                            user_suggestion = input().strip()
                            
                            # Salvar sugestão no Redis
                            redis_client.set(user_plan_response_key, user_suggestion, ex=300)
                            
                            print(f"✅ Sugestão registrada e será processada pelo PlanRefinerAgent.")
                            print(f"{'='*80}\n")
                            
                            # Resetar flag de confirmação para permitir nova confirmação do plano refinado
                            confirmation_checked = False
                            
                    except Exception as e:
                        print(f"\n❌ Erro ao processar interação: {e}\n")
                
                status_result = get_job_status(result['job_id'], silent=True)
                
                if status_result:
                    status_info = status_result.get('status', {})
                    current_status = status_info.get('status', 'unknown')
                    consolidated_status = status_info.get('consolidated_status', current_status)
                    
                    # Mostrar status consolidado se houver branches
                    if 'branches_count' in status_info and status_info['branches_count'] > 0:
                        print(f"[{i+1}s] Status: {consolidated_status} ({status_info['branches_count']} branches)")
                    else:
                        print(f"[{i+1}s] Status: {current_status}")
                    
                    # Considerar completo quando todas as branches terminarem
                    if consolidated_status == 'completed':
                        # Aguarda mais 2 segundos para garantir que branches aninhadas terminem
                        print(f"[{i+1}s] Aguardando branches aninhadas...")
                        time.sleep(2)
                        print(f"\n{'='*80}")
                        print(f"✅ JOB COMPLETADO COM SUCESSO")
                        print(f"{'='*80}")
                        
                        # Formatar saída com títulos bonitos para cada módulo
                        try:
                            print_formatted_result(status_info)
                        except Exception as e:
                            print(f"\n⚠️  Erro ao formatar resultado: {e}")
                            print(f"Mostrando JSON bruto:\n")
                            print(json.dumps(status_info, indent=2, ensure_ascii=False))
                        
                        print(f"{'='*80}\n")
                        return result
                    
                    if consolidated_status in ['error', 'failed', 'partial_failure']:
                        print(f"\n{'='*80}")
                        print(f"❌ JOB FALHOU")
                        print(f"{'='*80}")
                        print(json.dumps(status_info, indent=2, ensure_ascii=False))
                        print(f"{'='*80}\n")
                        return None
            
            print(f"\n⚠️  Timeout: Job ainda em processamento após 5 minutos")
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
                print(f"   Pergunta: \"{example['request']['pergunta']}\"\n")
            
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

