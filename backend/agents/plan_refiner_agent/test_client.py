"""
Cliente de teste para o Plan Refiner Agent
Testa o agente através do endpoint Flask
"""

import requests
import json
import sys
import time
from typing import Dict, Any

# URL do endpoint
BASE_URL = "http://localhost:5013"
ENDPOINT = f"{BASE_URL}/test-plan-refiner"


def test_plan_refiner(
    pergunta: str,
    original_plan: str,
    user_suggestion: str,
    intent_category: str = "unknown",
    username: str = "test_user",
    projeto: str = "test_project"
) -> Dict[str, Any]:
    """
    Testa o Plan Refiner Agent com os dados fornecidos
    
    Args:
        pergunta: Pergunta original do usuário
        original_plan: Plano original do PlanBuilder
        user_suggestion: Sugestão do usuário sobre o que modificar
        intent_category: Categoria da intenção
        username: Nome do usuário
        projeto: Nome do projeto
        
    Returns:
        Dicionário com resultado do teste
    """
    payload = {
        "pergunta": pergunta,
        "original_plan": original_plan,
        "user_suggestion": user_suggestion,
        "intent_category": intent_category,
        "username": username,
        "projeto": projeto
    }
    
    try:
        print(f"\n{'='*80}")
        print(f"📤 Enviando requisição...")
        print(f"   Pergunta: {pergunta}")
        print(f"   Plano Original: {original_plan[:80]}..." if len(original_plan) > 80 else f"   Plano Original: {original_plan}")
        print(f"   Sugestão: {user_suggestion[:80]}..." if len(user_suggestion) > 80 else f"   Sugestão: {user_suggestion}")
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


def run_interactive():
    """Modo interativo para refinar planos"""
    print("\n" + "="*80)
    print("🔧 MODO INTERATIVO - REFINAMENTO DE PLANOS")
    print("="*80)
    print("Digite as informações para refinar um plano")
    print("Digite 'sair' para encerrar")
    print("="*80 + "\n")
    
    while True:
        try:
            pergunta = input("📝 Pergunta original: ").strip()
            
            if pergunta.lower() == 'sair':
                print("\n👋 Encerrando modo interativo...")
                break
            
            if not pergunta:
                print("❌ Pergunta não pode estar vazia!\n")
                continue
            
            print("\n📋 Plano original (Enter em linha vazia para finalizar):")
            original_lines = []
            while True:
                line = input()
                if not line:
                    break
                original_lines.append(line)
            original_plan = '\n'.join(original_lines)
            
            if not original_plan:
                print("❌ Plano original não pode estar vazio!\n")
                continue
            
            user_suggestion = input("\n💡 O que você quer modificar no plano? ").strip()
            
            if not user_suggestion:
                print("❌ Sugestão não pode estar vazia!\n")
                continue
            
            intent_category = input("🏷️  Categoria (Enter para 'unknown'): ").strip() or "unknown"
            username = input("👤 Username (Enter para 'test_user'): ").strip() or "test_user"
            projeto = input("📁 Projeto (Enter para 'test_project'): ").strip() or "test_project"
            
            result = test_plan_refiner(
                pergunta=pergunta,
                original_plan=original_plan,
                user_suggestion=user_suggestion,
                intent_category=intent_category,
                username=username,
                projeto=projeto
            )
            
            if result and result.get('success'):
                print(f"\n✅ Plano refinado com sucesso!")
                if 'result' in result:
                    r = result['result']
                    print(f"\n🎯 PLANO REFINADO:")
                    print(f"{'='*80}")
                    print(r.get('refined_plan', 'N/A'))
                    print(f"{'='*80}")
            else:
                print(f"\n❌ Erro ao refinar plano")
            
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
        else:
            print(f"❌ Modo desconhecido: {mode}")
            print("Modo disponível: interactive")
    else:
        print("Uso: python test_client.py interactive")
        print("  interactive - Modo interativo")


if __name__ == "__main__":
    main()
