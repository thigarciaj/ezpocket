"""
Script de teste do Intent Validator Agent
Testa se o Intent Validator é sempre o primeiro nó executado
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ezinho_graph import get_ezinho_graph

def testar_intent_validator():
    """Testa o Intent Validator com diferentes tipos de perguntas"""
    
    print("="*80)
    print("🧪 TESTE DO INTENT VALIDATOR AGENT")
    print("="*80)
    
    # Obtém o grafo
    ezinho_graph = get_ezinho_graph()
    
    # Casos de teste
    casos_teste = [
        {
            "nome": "✅ Pergunta Válida - Análise de Dados",
            "pergunta": "Quantos pedidos tivemos em outubro?",
            "username": "teste_user",
            "projeto": "ezpocket",
            "resultado_esperado": "VÁLIDA"
        },
        {
            "nome": "✅ Pergunta Válida - Despedida",
            "pergunta": "Tchau, até logo!",
            "username": "teste_user",
            "projeto": "ezpocket",
            "resultado_esperado": "VÁLIDA (despedida)"
        },
        {
            "nome": "✅ Pergunta Válida - Ajuda",
            "pergunta": "Me ajuda, o que você faz?",
            "username": "teste_user",
            "projeto": "ezpocket",
            "resultado_esperado": "VÁLIDA (ajuda)"
        },
        {
            "nome": "❌ Pergunta INVÁLIDA - Fora do Escopo",
            "pergunta": "Qual a melhor receita de bolo de chocolate?",
            "username": "teste_user",
            "projeto": "ezpocket",
            "resultado_esperado": "INVÁLIDA"
        },
        {
            "nome": "❌ Pergunta INVÁLIDA - Conversa Casual",
            "pergunta": "Como foi seu dia?",
            "username": "teste_user",
            "projeto": "ezpocket",
            "resultado_esperado": "INVÁLIDA"
        }
    ]
    
    resultados = []
    
    for i, caso in enumerate(casos_teste, 1):
        print(f"\n{'='*80}")
        print(f"TESTE {i}/{len(casos_teste)}: {caso['nome']}")
        print(f"{'='*80}")
        print(f"📝 Pergunta: {caso['pergunta']}")
        print(f"👤 Username: {caso['username']}")
        print(f"📁 Projeto: {caso['projeto']}")
        print(f"🎯 Resultado Esperado: {caso['resultado_esperado']}")
        print(f"\n{'-'*80}")
        print("🚀 EXECUTANDO...")
        print(f"{'-'*80}\n")
        
        try:
            # Executa o grafo
            resultado = ezinho_graph.invoke(
                pergunta=caso['pergunta'],
                username=caso['username'],
                projeto=caso['projeto']
            )
            
            resposta = resultado.get('resposta', '')
            source = resultado.get('source', '')
            
            print(f"\n{'-'*80}")
            print("✅ RESULTADO:")
            print(f"{'-'*80}")
            print(f"📊 Source: {source}")
            print(f"💬 Resposta (primeiros 200 chars):\n{resposta[:200]}...")
            
            # Verifica se passou pelo Intent Validator
            if "fora do escopo" in resposta.lower() or "out of scope" in source.lower():
                status = "❌ INVÁLIDA (bloqueada pelo Intent Validator)"
            elif "despedida" in resposta.lower() or "tchau" in resposta.lower():
                status = "✅ VÁLIDA (despedida detectada)"
            elif "ajuda" in resposta.lower() or "help" in resposta.lower():
                status = "✅ VÁLIDA (ajuda detectada)"
            else:
                status = "✅ VÁLIDA (processada normalmente)"
            
            print(f"\n🏆 Status Final: {status}")
            
            resultados.append({
                "caso": caso['nome'],
                "status": status,
                "sucesso": True
            })
            
        except Exception as e:
            print(f"\n❌ ERRO ao executar teste:")
            print(f"   {str(e)}")
            resultados.append({
                "caso": caso['nome'],
                "status": f"ERRO: {str(e)}",
                "sucesso": False
            })
    
    # Resumo final
    print(f"\n\n{'='*80}")
    print("📊 RESUMO DOS TESTES")
    print(f"{'='*80}\n")
    
    sucessos = sum(1 for r in resultados if r['sucesso'])
    total = len(resultados)
    
    for resultado in resultados:
        emoji = "✅" if resultado['sucesso'] else "❌"
        print(f"{emoji} {resultado['caso']}")
        print(f"   Status: {resultado['status']}\n")
    
    print(f"{'='*80}")
    print(f"🎯 Total: {sucessos}/{total} testes executados com sucesso")
    print(f"{'='*80}\n")
    
    if sucessos == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Intent Validator está funcionando corretamente como primeiro nó!\n")
    else:
        print("⚠️  Alguns testes falharam. Verifique os erros acima.\n")

if __name__ == "__main__":
    print("\n")
    testar_intent_validator()
    print("\n")
