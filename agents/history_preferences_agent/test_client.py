#!/usr/bin/env python3
"""
Cliente de teste para History and Preferences Agent
Permite testar o agente via linha de comando
"""

import requests
import json
import sys
from typing import Dict, Optional

import os
from dotenv import load_dotenv

# Carrega variáveis do .env
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
load_dotenv(env_path)

BASE_URL = f"http://localhost:{os.getenv('HISTORY_PREFERENCES_PORT', '5002')}"

class Colors:
    """Cores ANSI para output colorido"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Imprime cabeçalho colorido"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")

def print_success(text: str):
    """Imprime mensagem de sucesso"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str):
    """Imprime mensagem de erro"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text: str):
    """Imprime informação"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def print_json(data: Dict):
    """Imprime JSON formatado"""
    print(json.dumps(data, indent=2, ensure_ascii=False))

def check_health() -> bool:
    """Verifica se o servidor está rodando"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success("Servidor está rodando!")
            print_info(f"Porta: {data.get('port', 5002)}")
            print_info(f"Database: {data.get('database', 'N/A')}")
            return True
        else:
            print_error(f"Servidor retornou status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Não foi possível conectar ao servidor")
        print_info("Certifique-se de que o servidor está rodando: python test_endpoint.py")
        return False
    except Exception as e:
        print_error(f"Erro ao verificar health: {e}")
        return False

def test_load_context(username: str, projeto: str, pergunta: str = ""):
    """Testa carregamento de contexto"""
    print_header("🧠 TEST: LOAD CONTEXT")
    
    payload = {
        "username": username,
        "projeto": projeto,
        "pergunta": pergunta
    }
    
    print_info(f"Username: {username}")
    print_info(f"Projeto: {projeto}")
    if pergunta:
        print_info(f"Pergunta: {pergunta}")
    
    try:
        response = requests.post(f"{BASE_URL}/test-load-context", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Contexto carregado com sucesso!")
            print(f"\n{Colors.BOLD}Resultado:{Colors.END}")
            print_json(data)
        else:
            print_error(f"Erro {response.status_code}: {response.text}")
    
    except Exception as e:
        print_error(f"Erro na requisição: {e}")

def test_save_interaction(username: str, projeto: str, pergunta: str, 
                         category: str = "quantidade"):
    """Testa salvamento de interação"""
    print_header("🧠 TEST: SAVE INTERACTION")
    
    payload = {
        "username": username,
        "projeto": projeto,
        "pergunta": pergunta,
        "intent_category": category
    }
    
    print_info(f"Username: {username}")
    print_info(f"Projeto: {projeto}")
    print_info(f"Pergunta: {pergunta}")
    print_info(f"Categoria: {category}")
    
    try:
        response = requests.post(f"{BASE_URL}/test-save-interaction", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('interaction_saved'):
                print_success("Interação salva com sucesso!")
            else:
                print_error("Falha ao salvar interação")
            print(f"\n{Colors.BOLD}Resultado:{Colors.END}")
            print_json(data)
        else:
            print_error(f"Erro {response.status_code}: {response.text}")
    
    except Exception as e:
        print_error(f"Erro na requisição: {e}")

def get_user_history(username: str, projeto: str, limit: int = 10):
    """Obtém histórico do usuário"""
    print_header("📜 GET: USER HISTORY")
    
    print_info(f"Username: {username}")
    print_info(f"Projeto: {projeto}")
    print_info(f"Limit: {limit}")
    
    try:
        response = requests.get(f"{BASE_URL}/user-history/{username}/{projeto}?limit={limit}")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Histórico obtido: {data.get('history_count', 0)} interações")
            print(f"\n{Colors.BOLD}Histórico:{Colors.END}")
            print_json(data)
        else:
            print_error(f"Erro {response.status_code}: {response.text}")
    
    except Exception as e:
        print_error(f"Erro na requisição: {e}")

def get_user_preferences(username: str, projeto: str):
    """Obtém preferências do usuário"""
    print_header("⚙️  GET: USER PREFERENCES")
    
    print_info(f"Username: {username}")
    print_info(f"Projeto: {projeto}")
    
    try:
        response = requests.get(f"{BASE_URL}/user-preferences/{username}/{projeto}")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Preferências obtidas: {data.get('preferences_count', 0)} categorias")
            print(f"\n{Colors.BOLD}Preferências:{Colors.END}")
            print_json(data)
        else:
            print_error(f"Erro {response.status_code}: {response.text}")
    
    except Exception as e:
        print_error(f"Erro na requisição: {e}")

def update_user_preferences(username: str, projeto: str, category: str, 
                           preferences: Dict, confidence: float = 1.0):
    """Atualiza preferências do usuário"""
    print_header("⚙️  UPDATE: USER PREFERENCES")
    
    payload = {
        "category": category,
        "preferences": preferences,
        "confidence": confidence
    }
    
    print_info(f"Username: {username}")
    print_info(f"Projeto: {projeto}")
    print_info(f"Category: {category}")
    print_info(f"Confidence: {confidence}")
    
    try:
        response = requests.post(f"{BASE_URL}/user-preferences/{username}/{projeto}", 
                               json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success("Preferências atualizadas com sucesso!")
            else:
                print_error("Falha ao atualizar preferências")
            print(f"\n{Colors.BOLD}Resultado:{Colors.END}")
            print_json(data)
        else:
            print_error(f"Erro {response.status_code}: {response.text}")
    
    except Exception as e:
        print_error(f"Erro na requisição: {e}")

def get_examples():
    """Mostra exemplos de uso"""
    print_header("📚 EXAMPLES")
    
    try:
        response = requests.get(f"{BASE_URL}/examples")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Exemplos disponíveis:")
            print_json(data)
        else:
            print_error(f"Erro {response.status_code}: {response.text}")
    
    except Exception as e:
        print_error(f"Erro na requisição: {e}")

def run_interactive_mode():
    """Modo interativo"""
    print_header("🧠 HISTORY AND PREFERENCES AGENT - MODO INTERATIVO")
    
    if not check_health():
        return
    
    username = input(f"\n{Colors.BOLD}Username:{Colors.END} ").strip()
    if not username:
        username = "teste_user"
        print_info(f"Usando username padrão: {username}")
    
    projeto = input(f"{Colors.BOLD}Projeto:{Colors.END} ").strip()
    if not projeto:
        projeto = "ezpag"
        print_info(f"Usando projeto padrão: {projeto}")
    
    while True:
        print(f"\n{Colors.BOLD}Opções:{Colors.END}")
        print("1. Salvar interação")
        print("2. Carregar contexto")
        print("3. Ver histórico")
        print("4. Ver preferências")
        print("5. Atualizar preferências")
        print("6. Sair")
        
        choice = input(f"\n{Colors.BOLD}Escolha:{Colors.END} ").strip()
        
        if choice == "1":
            pergunta = input(f"{Colors.BOLD}Pergunta:{Colors.END} ").strip()
            category = input(f"{Colors.BOLD}Categoria (quantidade/conhecimentos_gerais/analise_estatistica):{Colors.END} ").strip()
            if not category:
                category = "quantidade"
            test_save_interaction(username, projeto, pergunta, category)
        
        elif choice == "2":
            pergunta = input(f"{Colors.BOLD}Pergunta (opcional):{Colors.END} ").strip()
            test_load_context(username, projeto, pergunta)
        
        elif choice == "3":
            limit = input(f"{Colors.BOLD}Limite (default 10):{Colors.END} ").strip()
            limit = int(limit) if limit else 10
            get_user_history(username, projeto, limit)
        
        elif choice == "4":
            get_user_preferences(username, projeto)
        
        elif choice == "5":
            category = input(f"{Colors.BOLD}Categoria (visualization/analysis/reporting/communication):{Colors.END} ").strip()
            key = input(f"{Colors.BOLD}Chave:{Colors.END} ").strip()
            value = input(f"{Colors.BOLD}Valor:{Colors.END} ").strip()
            update_user_preferences(username, projeto, category, {key: value})
        
        elif choice == "6":
            print_info("Saindo...")
            break
        
        else:
            print_error("Opção inválida!")

def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print(f"\n{Colors.BOLD}Uso:{Colors.END}")
        print(f"  python test_client.py health              - Verifica se servidor está rodando")
        print(f"  python test_client.py interactive          - Modo interativo")
        print(f"  python test_client.py examples             - Mostra exemplos de uso")
        print(f"  python test_client.py save <user> <proj> <pergunta> [categoria]")
        print(f"  python test_client.py load <user> <proj> [pergunta]")
        print(f"  python test_client.py history <user> <proj> [limit]")
        print(f"  python test_client.py preferences <user> <proj>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "health":
        check_health()
    
    elif command == "interactive":
        run_interactive_mode()
    
    elif command == "examples":
        get_examples()
    
    elif command == "save":
        if len(sys.argv) < 5:
            print_error("Uso: python test_client.py save <username> <projeto> <pergunta> [categoria]")
            sys.exit(1)
        username = sys.argv[2]
        projeto = sys.argv[3]
        pergunta = sys.argv[4]
        category = sys.argv[5] if len(sys.argv) > 5 else "quantidade"
        test_save_interaction(username, projeto, pergunta, category)
    
    elif command == "load":
        if len(sys.argv) < 4:
            print_error("Uso: python test_client.py load <username> <projeto> [pergunta]")
            sys.exit(1)
        username = sys.argv[2]
        projeto = sys.argv[3]
        pergunta = sys.argv[4] if len(sys.argv) > 4 else ""
        test_load_context(username, projeto, pergunta)
    
    elif command == "history":
        if len(sys.argv) < 4:
            print_error("Uso: python test_client.py history <username> <projeto> [limit]")
            sys.exit(1)
        username = sys.argv[2]
        projeto = sys.argv[3]
        limit = int(sys.argv[4]) if len(sys.argv) > 4 else 10
        get_user_history(username, projeto, limit)
    
    elif command == "preferences":
        if len(sys.argv) < 4:
            print_error("Uso: python test_client.py preferences <username> <projeto>")
            sys.exit(1)
        username = sys.argv[2]
        projeto = sys.argv[3]
        get_user_preferences(username, projeto)
    
    else:
        print_error(f"Comando desconhecido: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
