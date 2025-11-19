"""
Script para submeter jobs ao sistema de filas
"""

from graph_orchestrator import submit, status, visualize
import time
import json

def main():
    # Visualizar grafo
    visualize()
    
    # Submeter job
    print("\n📤 Submetendo job...")
    job_id = submit(
        start_module='intent_validator',
        username='joao',
        projeto='ezpag',
        pergunta='quantos pedidos tivemos hoje?'
    )
    
    print(f"\n✅ Job submetido: {job_id}")
    print("\n⏳ Aguardando processamento...")
    
    # Monitorar status
    for i in range(10):
        time.sleep(1)
        job_status = status(job_id)
        
        if job_status:
            current_status = job_status.get('status')
            current_module = job_status.get('current_module')
            chain_length = len(job_status.get('execution_chain', []))
            
            print(f"   [{i+1}s] Status: {current_status} | Módulo: {current_module} | Executados: {chain_length}")
            
            if current_status == 'completed':
                print("\n✅ Job completo!")
                print("\n📊 Resultado:")
                print(json.dumps(job_status, indent=2, ensure_ascii=False))
                break
            
            elif current_status == 'failed':
                print(f"\n❌ Job falhou: {job_status.get('error')}")
                break
    else:
        print("\n⏱️  Timeout - verifique os workers")
        print(f"\nConsulte status manualmente:")
        print(f"  from graph_orchestrator import status")
        print(f"  status('{job_id}')")

if __name__ == '__main__':
    main()
