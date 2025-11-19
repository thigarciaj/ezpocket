"""
Cliente de teste para o SQL Validator Agent
Testa o agente através do endpoint Flask
"""

import requests
import json
import sys
import time
from typing import Dict, Any

# URL do endpoint
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
load_dotenv(env_path)

BASE_URL = f"http://localhost:{os.getenv('SQL_VALIDATOR_PORT', '5014')}"
ENDPOINT = f"{BASE_URL}/test-sql-validator"


def test_sql_validator(
    query_sql: str,
    estimated_complexity: str = "média",
    username: str = "test_user",
    projeto: str = "test_project"
) -> Dict[str, Any]:
    """
    Testa o SQL Validator Agent com a query fornecida
    
    Args:
        query_sql: Query SQL a ser validada
        estimated_complexity: Complexidade estimada (baixa/média/alta)
        username: Nome do usuário
        projeto: Nome do projeto
        
    Returns:
        Dicionário com resultado da validação
    """
    payload = {
        "query_sql": query_sql,
        "estimated_complexity": estimated_complexity,
        "username": username,
        "projeto": projeto
    }
    
    try:
        print(f"\n{'='*80}")
        print(f"📤 Enviando requisição...")
        print(f"   Query: {query_sql[:100]}..." if len(query_sql) > 100 else f"   Query: {query_sql}")
        print(f"   Complexidade: {estimated_complexity}")
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


def run_tests():
    """Executa bateria de testes"""
    print("\n" + "="*80)
    print("🧪 BATERIA DE TESTES - SQL VALIDATOR AGENT")
    print("="*80)
    
    tests = [
        {
            "name": "Query SELECT válida simples",
            "query": "SELECT COUNT(*) FROM receivables_db.report_orders WHERE date >= current_date",
            "complexity": "baixa"
        },
        {
            "name": "Query com JOIN e agregação",
            "query": """
                SELECT o.order_id, SUM(o.amount) as total, c.customer_name
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                WHERE o.date >= current_date - interval '30' day
                GROUP BY o.order_id, c.customer_name
                ORDER BY total DESC
                LIMIT 10
            """,
            "complexity": "média"
        },
        {
            "name": "Query com operação proibida (INSERT)",
            "query": "INSERT INTO orders (id, amount) VALUES (1, 100)",
            "complexity": "baixa"
        },
        {
            "name": "Query com operação proibida (DELETE)",
            "query": "DELETE FROM orders WHERE id = 1",
            "complexity": "baixa"
        },
        {
            "name": "Query com SQL injection (múltiplas queries)",
            "query": "SELECT * FROM orders; DROP TABLE orders;",
            "complexity": "baixa"
        },
        {
            "name": "Query complexa com múltiplos JOINs",
            "query": """
                SELECT a.*, b.*, c.*
                FROM large_table a
                JOIN another_table b ON a.id = b.id
                JOIN third_table c ON b.id = c.id
                WHERE a.date >= '2025-01-01'
                GROUP BY a.id, b.id, c.id
            """,
            "complexity": "alta"
        }
    ]
    
    results = []
    for i, test in enumerate(tests, 1):
        print(f"\n{'='*80}")
        print(f"🧪 Teste {i}/{len(tests)}: {test['name']}")
        print(f"{'='*80}")
        
        result = test_sql_validator(
            query_sql=test['query'],
            estimated_complexity=test['complexity']
        )
        
        results.append({
            'test': test['name'],
            'passed': result is not None and 'result' in result,
            'valid': result.get('result', {}).get('valid', False) if result else False,
            'risk_level': result.get('result', {}).get('risk_level', 'unknown') if result else 'unknown',
            'cost': result.get('result', {}).get('estimated_cost_usd', 0) if result else 0
        })
        
        time.sleep(1)  # Pequena pausa entre testes
    
    # Resumo
    print(f"\n{'='*80}")
    print("📊 RESUMO DOS TESTES")
    print(f"{'='*80}")
    
    total = len(results)
    passed = sum(1 for r in results if r['passed'])
    
    print(f"Total de testes: {total}")
    print(f"Testes executados: {passed}")
    print(f"Testes falhados: {total - passed}")
    print()
    
    for i, result in enumerate(results, 1):
        status = "✅" if result['passed'] else "❌"
        print(f"{status} {i}. {result['test']}")
        if result['passed']:
            print(f"   Valid: {result['valid']}, Risk: {result['risk_level']}, Cost: ${result['cost']}")
    
    print(f"{'='*80}\n")


def run_interactive():
    """Modo interativo para validar queries"""
    print("\n" + "="*80)
    print("🔍 MODO INTERATIVO - VALIDAÇÃO DE QUERIES SQL")
    print("="*80)
    print("Digite a query SQL para validar")
    print("Digite 'sair' para encerrar")
    print("Digite 'tests' para rodar bateria de testes")
    print("="*80 + "\n")
    
    while True:
        try:
            print("🔍 Digite a query SQL (ou 'sair'/'tests'):")
            query = input("> ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['sair', 'exit', 'quit']:
                print("\n👋 Encerrando...\n")
                break
            
            if query.lower() == 'tests':
                run_tests()
                continue
            
            print("\n📊 Complexidade (baixa/média/alta) [média]:")
            complexity = input("> ").strip() or "média"
            
            result = test_sql_validator(
                query_sql=query,
                estimated_complexity=complexity
            )
            
            if result and 'result' in result:
                res = result['result']
                print(f"\n{'='*80}")
                print("📋 RESULTADO DA VALIDAÇÃO")
                print(f"{'='*80}")
                print(f"✓ Válida: {'✅' if res['valid'] else '❌'} {res['valid']}")
                print(f"✓ Sintaxe: {res['syntax_valid']}")
                print(f"✓ Athena Compatible: {res['athena_compatible']}")
                print(f"✓ Security Issues: {len(res['security_issues'])}")
                print(f"✓ Warnings: {len(res['warnings'])}")
                print(f"✓ Suggestions: {len(res['optimization_suggestions'])}")
                print(f"✓ Scan: {res['estimated_scan_size_gb']} GB")
                print(f"✓ Cost: ${res['estimated_cost_usd']} USD")
                print(f"✓ Time: {res['estimated_execution_time_seconds']}s")
                print(f"✓ Risk Level: {res['risk_level'].upper()}")
                
                if res['security_issues']:
                    print(f"\n⚠️  SECURITY ISSUES:")
                    for issue in res['security_issues']:
                        print(f"   • {issue}")
                
                if res['warnings']:
                    print(f"\n⚠️  WARNINGS:")
                    for warning in res['warnings']:
                        print(f"   • {warning}")
                
                if res['optimization_suggestions']:
                    print(f"\n💡 OPTIMIZATION SUGGESTIONS:")
                    for suggestion in res['optimization_suggestions']:
                        print(f"   • {suggestion}")
                
                print(f"{'='*80}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Encerrando...\n")
            break
        except Exception as e:
            print(f"\n❌ Erro: {e}\n")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'tests':
        run_tests()
    else:
        run_interactive()
