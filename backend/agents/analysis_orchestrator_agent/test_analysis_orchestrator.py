"""
Teste unitário do Analysis Orchestrator Agent
"""

import sys
import os
from pathlib import Path

# Adicionar backend ao path
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

from agents.analysis_orchestrator_agent.analysis_orchestrator import AnalysisOrchestratorAgent

def test_generate_query():
    """Testa geração de query SQL a partir de um plano"""
    
    agent = AnalysisOrchestratorAgent()
    
    # Estado de teste
    state = {
        "pergunta": "Quantas vendas tivemos hoje?",
        "intent_category": "quantidade",
        "plan": """
DESCRIÇÃO GERAL:
Consultar a tabela report_orders filtrando pela data de hoje (contract start date) e contar o número de pedidos.

PASSOS DETALHADOS:
1. Acessar tabela receivables_db.report_orders
2. Filtrar registros onde contract_start_date é hoje usando timezone America/New_York
3. Aplicar COUNT(*) para contar os pedidos
4. Retornar resultado como número

ESTIMATIVA DE COMPLEXIDADE: Baixa
FONTES DE DADOS: report_orders
FORMATO DE SAÍDA: número
        """,
        "username": "test_user",
        "projeto": "test_project"
    }
    
    print("\n" + "="*80)
    print("🧪 TESTE: Geração de Query SQL")
    print("="*80)
    
    result = agent.generate_query(state)
    
    print("\n" + "="*80)
    print("📊 RESULTADO:")
    print("="*80)
    
    if result.get('error'):
        print(f"❌ Erro: {result['error']}")
    else:
        print(f"✅ Query gerada com sucesso!")
        print(f"\n📝 Query SQL:")
        print(result.get('query_sql', ''))
        print(f"\n📖 Explicação:")
        print(result.get('query_explanation', ''))
        print(f"\n📊 Colunas usadas: {result.get('columns_used', [])}")
        print(f"🎯 Filtros aplicados: {result.get('filters_applied', [])}")
        print(f"🔒 Segurança validada: {result.get('security_validated')}")
        print(f"⚙️  Notas de otimização: {result.get('optimization_notes', '')}")
        print(f"⏱️  Tempo de execução: {result.get('execution_time', 0):.2f}s")
    
    print("\n" + "="*80)

def test_security_validation():
    """Testa validação de segurança com query maliciosa"""
    
    agent = AnalysisOrchestratorAgent()
    
    # Estado de teste com plano que poderia gerar query maliciosa
    state = {
        "pergunta": "Me mostre emails de todos os clientes",
        "intent_category": "quantidade",
        "plan": "Consultar tabela report_orders e retornar coluna customer_email",
        "username": "test_user",
        "projeto": "test_project"
    }
    
    print("\n" + "="*80)
    print("🔒 TESTE: Validação de Segurança (Query com dados sensíveis)")
    print("="*80)
    
    result = agent.generate_query(state)
    
    print("\n" + "="*80)
    print("📊 RESULTADO:")
    print("="*80)
    
    if result.get('error'):
        print(f"✅ Query rejeitada corretamente!")
        print(f"❌ Motivo: {result['error']}")
    else:
        print(f"⚠️  ATENÇÃO: Query deveria ter sido rejeitada!")
        print(f"Query: {result.get('query_sql', '')}")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🧪 EXECUTANDO TESTES DO ANALYSIS ORCHESTRATOR")
    print("="*80 + "\n")
    
    # Teste 1: Geração normal de query
    test_generate_query()
    
    # Teste 2: Validação de segurança
    test_security_validation()
    
    print("\n" + "="*80)
    print("✅ TESTES CONCLUÍDOS")
    print("="*80 + "\n")
