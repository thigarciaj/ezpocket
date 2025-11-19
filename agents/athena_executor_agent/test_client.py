#!/usr/bin/env python3
"""
Test Client Interativo - Cliente para testar Athena Executor Agent via terminal
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import json

# Adicionar paths
agents_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, agents_path)

# Carregar .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from agents.athena_executor_agent.athena_executor import AthenaExecutorAgent

def print_header(text):
    """Imprime cabeçalho formatado"""
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}\n")

def print_result(result):
    """Imprime resultado formatado"""
    print(f"\n{'='*80}")
    print(f"📊 RESULTADO DA EXECUÇÃO")
    print(f"{'='*80}")
    print(f"✅ Success: {result['success']}")
    print(f"📝 Query: {result['query_executed'][:100]}...")
    print(f"⏱️  Tempo: {result['execution_time_seconds']:.2f}s")
    
    if result['success']:
        print(f"📊 Linhas: {result['row_count']:,}")
        print(f"📋 Colunas: {result['column_count']}")
        print(f"💾 Tamanho: {result['data_size_mb']:.2f} MB")
        print(f"🏛️  Database: {result['database']}")
        print(f"🌎 Region: {result['region']}")
        
        if result['columns']:
            print(f"\n📋 Colunas retornadas:")
            for col in result['columns']:
                print(f"   • {col}")
        
        if result['results_preview']:
            print(f"\n📊 Preview dos dados (primeiras {min(5, len(result['results_preview']))} linhas):")
            for i, row in enumerate(result['results_preview'][:5], 1):
                print(f"\n   Linha {i}:")
                for key, value in row.items():
                    print(f"      {key}: {value}")
    else:
        print(f"❌ Erro: {result['error']}")
        if result.get('error_type'):
            print(f"🚨 Tipo: {result['error_type']}")
    
    print(f"{'='*80}\n")

def main():
    """Função principal do cliente interativo"""
    print_header("🎮 ATHENA EXECUTOR - CLIENTE INTERATIVO")
    
    # Inicializar executor
    try:
        executor = AthenaExecutorAgent()
    except Exception as e:
        print(f"❌ Erro ao inicializar executor: {str(e)}")
        print("\n💡 Verifique se as credenciais AWS estão configuradas no .env:")
        print("   - AWS_ACCESS_KEY")
        print("   - AWS_SECRET_KEY")
        print("   - AWS_REGION")
        print("   - ATHENA_OUTPUT_S3")
        return
    
    print(f"✅ Executor inicializado com sucesso")
    print(f"   Database: {executor.database}")
    print(f"   Region: {executor.aws_region}")
    
    # Queries de exemplo
    exemplos = [
        "SELECT * FROM orders LIMIT 10",
        "SELECT status, COUNT(*) as total FROM orders GROUP BY status",
        "SELECT customer_name, SUM(total) as total_spent FROM orders GROUP BY customer_name ORDER BY total_spent DESC LIMIT 10",
        "SELECT DATE(created_at) as date, COUNT(*) as orders FROM orders GROUP BY DATE(created_at) ORDER BY date DESC LIMIT 30"
    ]
    
    while True:
        print("\n" + "="*80)
        print("🎯 OPÇÕES")
        print("="*80)
        print("1) Executar query personalizada")
        print("2) Usar exemplo 1: SELECT * FROM orders LIMIT 10")
        print("3) Usar exemplo 2: Contagem por status")
        print("4) Usar exemplo 3: Top 10 clientes por valor")
        print("5) Usar exemplo 4: Pedidos por dia (últimos 30 dias)")
        print("6) Sair")
        print("="*80)
        
        opcao = input("\nEscolha uma opção (1-6): ").strip()
        
        if opcao == '6':
            print("\n👋 Até logo!")
            break
        
        # Determinar query
        if opcao == '1':
            print("\n📝 Digite sua query SQL:")
            query_sql = input("> ").strip()
            if not query_sql:
                print("❌ Query vazia!")
                continue
        elif opcao in ['2', '3', '4', '5']:
            idx = int(opcao) - 2
            query_sql = exemplos[idx]
            print(f"\n📝 Query selecionada:\n{query_sql}")
        else:
            print("❌ Opção inválida!")
            continue
        
        # Solicitar username e projeto
        print("\n👤 Username (Enter para 'test_user'):")
        username = input("> ").strip() or 'test_user'
        
        print("\n📁 Projeto (Enter para 'test_project'):")
        projeto = input("> ").strip() or 'test_project'
        
        # Executar
        print("\n🔄 Executando query...")
        try:
            result = executor.execute(
                query_sql=query_sql,
                username=username,
                projeto=projeto
            )
            
            print_result(result)
            
            # Salvar resultado?
            salvar = input("\n💾 Deseja salvar o resultado em arquivo JSON? (s/n): ").strip().lower()
            if salvar == 's':
                filename = f"result_{username}_{projeto}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False, default=str)
                print(f"✅ Resultado salvo em: {filename}")
            
        except Exception as e:
            print(f"\n❌ Erro durante execução: {str(e)}")
            print(f"🚨 Tipo: {type(e).__name__}")
        
        # Continuar?
        continuar = input("\n🔄 Executar outra query? (s/n): ").strip().lower()
        if continuar != 's':
            print("\n👋 Até logo!")
            break

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrompido pelo usuário. Até logo!")
    except Exception as e:
        print(f"\n❌ Erro fatal: {str(e)}")
