"""
Cliente de teste para o Auto Correction Agent
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

BASE_URL = f"http://localhost:{os.getenv('AUTO_CORRECTION_PORT', '5015')}"
ENDPOINT = f"{BASE_URL}/test-auto-correction"


def test_auto_correction(
    query_original: str,
    validation_issues: list,
    username: str = "test_user",
    projeto: str = "test_project"
) -> Dict[str, Any]:
    """
    Testa o Auto Correction Agent com a query fornecida
    
    Args:
        query_original: Query SQL original (inválida)
        validation_issues: Lista de problemas encontrados
        username: Nome do usuário
        projeto: Nome do projeto
        
    Returns:
        Dicionário com resultado da correção
    """
    payload = {
        "query_original": query_original,
        "validation_issues": validation_issues,
        "username": username,
        "projeto": projeto
    }
    
    try:
        print(f"\n{'='*80}")
        print(f"📤 Enviando requisição...")
        print(f"   Query: {query_original[:100]}..." if len(query_original) > 100 else f"   Query: {query_original}")
        print(f"   Issues: {len(validation_issues)} problemas")
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
    print("🧪 BATERIA DE TESTES - AUTO CORRECTION AGENT")
    print("="*80)
    
    tests = [
        {
            "name": "Correção de operação INSERT proibida",
            "query": "INSERT INTO orders (id, amount) VALUES (1, 100)",
            "issues": ["Operação proibida detectada: INSERT"]
        },
        {
            "name": "Correção de múltiplas queries (SQL injection)",
            "query": "SELECT * FROM orders; DROP TABLE orders;",
            "issues": ["Múltiplas queries detectadas (não permitido)", "Operação proibida detectada: DROP"]
        },
        {
            "name": "Correção de coluna sensível (CPF)",
            "query": "SELECT cpf, name FROM customers WHERE cpf = '12345678900'",
            "issues": ["🔒 ACESSO NEGADO: Coluna sensível detectada 'cpf'"]
        },
        {
            "name": "Correção de função incompatível (NOW())",
            "query": "SELECT * FROM orders WHERE date > NOW()",
            "issues": ["Função incompatível detectada: NOW()"]
        },
        {
            "name": "Correção de sintaxe SQL (aspas incorretas)",
            "query": "SELECT 'customer name' FROM orders WHERE date >= '2025-01-01'",
            "issues": ["Sintaxe incorreta: use aspas duplas para colunas"]
        },
        {
            "name": "Correção combinada (múltiplos erros)",
            "query": """
                INSERT INTO orders (id, cpf, amount) VALUES (1, '12345', 100);
                SELECT * FROM orders WHERE date > NOW();
            """,
            "issues": [
                "Operação proibida detectada: INSERT",
                "Coluna sensível detectada: cpf",
                "Múltiplas queries detectadas",
                "Função incompatível: NOW()"
            ]
        }
    ]
    
    results = []
    for i, test in enumerate(tests, 1):
        print(f"\n{'='*80}")
        print(f"🧪 Teste {i}/{len(tests)}: {test['name']}")
        print(f"{'='*80}")
        
        result = test_auto_correction(
            query_original=test['query'],
            validation_issues=test['issues']
        )
        
        results.append({
            'test': test['name'],
            'passed': result is not None and 'result' in result,
            'success': result.get('result', {}).get('success', False) if result else False,
            'corrections': result.get('result', {}).get('corrections_count', 0) if result else 0
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
            print(f"   Success: {result['success']}, Corrections: {result['corrections']}")
    
    print(f"{'='*80}\n")


def run_interactive():
    """Modo interativo para corrigir queries"""
    print("\n" + "="*80)
    print("🔧 MODO INTERATIVO - CORREÇÃO DE QUERIES SQL")
    print("="*80)
    print("Digite a query SQL inválida para corrigir")
    print("Digite 'sair' para encerrar")
    print("Digite 'tests' para rodar bateria de testes")
    print("="*80 + "\n")
    
    while True:
        try:
            print("🔧 Digite a query SQL inválida (ou 'sair'/'tests'):")
            query = input("> ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['sair', 'exit', 'quit']:
                print("\n👋 Encerrando...\n")
                break
            
            if query.lower() == 'tests':
                run_tests()
                continue
            
            print("\n⚠️  Digite os problemas detectados (um por linha, linha vazia para finalizar):")
            issues = []
            while True:
                issue = input("> ").strip()
                if not issue:
                    break
                issues.append(issue)
            
            if not issues:
                print("⚠️  Nenhum problema informado, usando exemplo padrão")
                issues = ["Sintaxe SQL inválida"]
            
            result = test_auto_correction(
                query_original=query,
                validation_issues=issues
            )
            
            if result and 'result' in result:
                res = result['result']
                print(f"\n{'='*80}")
                print("📋 RESULTADO DA CORREÇÃO")
                print(f"{'='*80}")
                print(f"✓ Success: {'✅' if res['success'] else '❌'} {res['success']}")
                print(f"✓ Correções Aplicadas: {res['corrections_count']}")
                print(f"✓ Query Original (100 chars): {res['query_original'][:100]}...")
                print(f"✓ Query Corrigida (100 chars): {res['query_corrected'][:100]}...")
                print(f"✓ Explicação: {res['correction_explanation'][:200]}...")
                print(f"✓ Tokens Usados: {res['tokens_used']}")
                print(f"✓ Tempo: {res['execution_time']:.2f}s")
                
                if res['corrections_applied']:
                    print(f"\n💡 CORREÇÕES APLICADAS:")
                    for correction in res['corrections_applied']:
                        print(f"   • {correction}")
                
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
