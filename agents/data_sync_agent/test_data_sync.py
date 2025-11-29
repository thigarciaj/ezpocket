#!/usr/bin/env python3
"""
Teste do Data Sync Agent
Executa uma sincronização manual para testar a funcionalidade
"""

import sys
import os
import asyncio

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_sync_agent import DataSyncAgent

async def test_sync():
    """Testar sincronização manual"""
    print("🧪 Iniciando teste do Data Sync Agent")
    
    try:
        # Criar instância do agente
        agent = DataSyncAgent()
        
        # Executar sincronização
        success = agent.perform_sync()
        
        if success:
            print("✅ Teste de sincronização concluído com sucesso!")
        else:
            print("❌ Teste de sincronização falhou!")
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")

def test_schedule():
    """Testar verificação de schedule"""
    print("🧪 Testando verificação de schedule")
    
    try:
        agent = DataSyncAgent()
        
        should_run = agent.should_run_now()
        next_run = agent.get_next_run_time()
        
        print(f"📅 Deve executar agora: {should_run}")
        print(f"⏰ Próxima execução: {next_run.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"🔧 Schedule configurado: {agent.sync_config['schedule']}")
        
    except Exception as e:
        print(f"❌ Erro no teste de schedule: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Testar Data Sync Agent')
    parser.add_argument('--sync', action='store_true', help='Executar teste de sincronização')
    parser.add_argument('--schedule', action='store_true', help='Testar verificação de schedule')
    
    args = parser.parse_args()
    
    if args.sync:
        asyncio.run(test_sync())
    elif args.schedule:
        test_schedule()
    else:
        print("Uso: python test_data_sync.py --sync | --schedule")
        print("  --sync: Executar teste de sincronização")
        print("  --schedule: Testar verificação de schedule")