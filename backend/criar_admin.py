#!/usr/bin/env python3
"""
Script para criar o primeiro usuário administrador do EZPOCKET-AI
Execute este script apenas UMA VEZ para criar o usuário inicial
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import create_user

def create_admin_user():
    print("="*50)
    print("   EZPOCKET-AI - Criar Usuário Administrador")
    print("="*50)
    print()
    print("Este script criará o primeiro usuário administrador.")
    print("Execute apenas uma vez para configuração inicial.")
    print()
    
    # Usuário padrão: admin / admin123
    username = "brenopessoa"
    password = "brenopessoa2025!@"
    
    print(f"Criando usuário: {username}")
    print(f"Senha padrão: {password}")
    print()
    print("⚠️  IMPORTANTE: Altere a senha após o primeiro login!")
    print()
    
    success, message = create_user(username, password)
    
    if success:
        print("✅ Usuário administrador criado com sucesso!")
        print()
        print("Dados de acesso:")
        print(f"  Usuário: {username}")
        print(f"  Senha: {password}")
        print()
        print("🚀 Agora você pode iniciar o sistema e fazer login!")
    else:
        print(f"❌ Erro: {message}")
        if "já existe" in message:
            print()
            print("O usuário administrador já foi criado anteriormente.")
            print("Use o script admin.py para gerenciar usuários.")

if __name__ == "__main__":
    create_admin_user()
    input("\nPressione Enter para sair...")
