#!/usr/bin/env python3
"""
Script administrativo para gerenciar usuários do EZPOCKET-AI
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import create_user, list_users, toggle_user_status
import getpass

def show_menu():
    print("\n" + "="*50)
    print("   EZPOCKET-AI - Administração de Usuários")
    print("="*50)
    print("1. Criar novo usuário")
    print("2. Listar usuários")
    print("3. Ativar/Desativar usuário")
    print("4. Sair")
    print("-"*50)

def create_new_user():
    print("\n--- Criar Novo Usuário ---")
    username = input("Nome de usuário: ").strip()
    
    if not username:
        print("❌ Nome de usuário não pode estar vazio!")
        return
    
    password = getpass.getpass("Senha: ")
    if not password:
        print("❌ Senha não pode estar vazia!")
        return
    
    confirm_password = getpass.getpass("Confirme a senha: ")
    if password != confirm_password:
        print("❌ Senhas não coincidem!")
        return
    
    success, message = create_user(username, password)
    
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")

def list_all_users():
    print("\n--- Lista de Usuários ---")
    users = list_users()
    
    if not users:
        print("Nenhum usuário encontrado.")
        return
    
    print(f"{'ID':<4} {'Usuário':<20} {'Criado em':<20} {'Último Login':<20} {'Status':<10}")
    print("-" * 80)
    
    for user in users:
        user_id, username, created_at, last_login, is_active = user
        status = "✅ Ativo" if is_active else "❌ Inativo"
        last_login_str = last_login[:19] if last_login else "Nunca"
        created_str = created_at[:19] if created_at else "N/A"
        
        print(f"{user_id:<4} {username:<20} {created_str:<20} {last_login_str:<20} {status:<10}")

def toggle_user():
    print("\n--- Ativar/Desativar Usuário ---")
    list_all_users()
    
    username = input("\nDigite o nome do usuário para alterar status: ").strip()
    
    if not username:
        print("❌ Nome de usuário não pode estar vazio!")
        return
    
    if toggle_user_status(username):
        print(f"✅ Status do usuário '{username}' alterado com sucesso!")
    else:
        print(f"❌ Erro ao alterar status do usuário '{username}'")

def main():
    print("Inicializando sistema de administração...")
    
    while True:
        show_menu()
        choice = input("Escolha uma opção (1-4): ").strip()
        
        if choice == '1':
            create_new_user()
        elif choice == '2':
            list_all_users()
        elif choice == '3':
            toggle_user()
        elif choice == '4':
            print("\n👋 Saindo do sistema administrativo...")
            break
        else:
            print("❌ Opção inválida! Escolha entre 1-4.")
        
        input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    main()
