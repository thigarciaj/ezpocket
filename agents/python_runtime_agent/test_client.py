"""
Test Client para Python Runtime Agent
"""
import os
import json
import requests
from dotenv import load_dotenv
from pathlib import Path

# Carregar .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# URL base
BASE_URL = f"http://localhost:{os.getenv('PYTHON_RUNTIME_PORT', '5018')}"

def test_health():
    """Testa health check"""
    print("\n" + "="*80)
    print("🏥 Testando Health Check...")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

def test_quick():
    """Testa endpoint de teste rápido"""
    print("\n" + "="*80)
    print("⚡ Testando Endpoint de Teste Rápido...")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/test", timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n📊 ANÁLISE:")
            print(f"Sucesso: {result.get('success')}")
            print(f"Tem análise: {result.get('has_analysis')}")
            print(f"\nResumo: {result.get('analysis_summary')}")
            print(f"\nEstatísticas:")
            print(json.dumps(result.get('statistics', {}), indent=2, ensure_ascii=False))
            print(f"\nInsights:")
            for insight in result.get('insights', []):
                print(f"  • {insight}")
            return True
        else:
            print(f"❌ Erro: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

def test_analyze_custom():
    """Testa análise com dados customizados"""
    print("\n" + "="*80)
    print("🔬 Testando Análise Customizada...")
    print("="*80)
    
    payload = {
        'pergunta': 'Qual o valor total de vendas por vendedor?',
        'username': 'test_user',
        'projeto': 'test_project',
        'query_results': {
            'success': True,
            'row_count': 5,
            'column_count': 2,
            'columns': ['vendedor', 'total_vendas'],
            'results_full': [
                {'vendedor': 'João Silva', 'total_vendas': 125000},
                {'vendedor': 'Maria Santos', 'total_vendas': 98000},
                {'vendedor': 'Pedro Costa', 'total_vendas': 156000},
                {'vendedor': 'Ana Lima', 'total_vendas': 87000},
                {'vendedor': 'Carlos Souza', 'total_vendas': 143000}
            ],
            'results_preview': [
                {'vendedor': 'João Silva', 'total_vendas': 125000},
                {'vendedor': 'Maria Santos', 'total_vendas': 98000},
                {'vendedor': 'Pedro Costa', 'total_vendas': 156000}
            ],
            'results_message': '5 vendedores encontrados'
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/analyze",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n📊 ANÁLISE:")
            print(f"Sucesso: {result.get('success')}")
            print(f"\n📝 Resumo:")
            print(f"{result.get('analysis_summary')}")
            print(f"\n📈 Estatísticas:")
            print(json.dumps(result.get('statistics', {}), indent=2, ensure_ascii=False))
            print(f"\n💡 Insights:")
            for i, insight in enumerate(result.get('insights', []), 1):
                print(f"  {i}. {insight}")
            print(f"\n📊 Visualizações Sugeridas:")
            for viz in result.get('visualizations', []):
                print(f"  • {viz}")
            print(f"\n🎯 Recomendações:")
            for rec in result.get('recommendations', []):
                print(f"  • {rec}")
            return True
        else:
            print(f"❌ Erro: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🧪 PYTHON RUNTIME AGENT - TEST CLIENT")
    print("="*80)
    print(f"🌐 URL Base: {BASE_URL}")
    
    # Executar testes
    results = []
    
    results.append(("Health Check", test_health()))
    results.append(("Teste Rápido", test_quick()))
    results.append(("Análise Customizada", test_analyze_custom()))
    
    # Resumo
    print("\n" + "="*80)
    print("📊 RESUMO DOS TESTES")
    print("="*80)
    
    for name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, s in results if s)
    print(f"\n📈 Total: {passed}/{total} testes passaram")
    print("="*80 + "\n")
