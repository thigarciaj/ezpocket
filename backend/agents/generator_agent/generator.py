"""
NÓ 2: GENERATOR AGENT
Responsável por:
- Gerar queries SQL usando IA (OpenAI GPT-4)
- Usar schema, regras e exemplos para criar SQL válida
- Manter histórico de conversação
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from query_generator import QueryGenerator
from schema_manager import SchemaManager


class GeneratorAgent:
    """Agente que gera queries SQL dinamicamente com IA"""
    
    def __init__(self):
        self.schema_manager = SchemaManager()
        self.query_generator = QueryGenerator(self.schema_manager)
    
    def generate(self, state: dict) -> dict:
        """
        Gera SQL query baseada na pergunta do usuário
        
        Retorna:
            dict com:
            - sql_query: Query SQL gerada
            - source: "AI_GENERATION"
        """
        pergunta = state["pergunta"]
        
        print(f"[GENERATOR] 🤖 Gerando SQL para: '{pergunta[:50]}...'")
        
        # Gera query usando IA
        query = self.query_generator.gerar_query(pergunta)
        
        if not query or query.startswith("❌"):
            print(f"[GENERATOR] ❌ Falha ao gerar query")
            return {
                "erro": True,
                "resposta_final": (query or "❓ Não consegui gerar uma query.") + "\nPor favor, reformule sua pergunta.",
                "query": query,
                "source": "AI_GENERATION_FAILED"
            }
        
        print(f"[GENERATOR] ✅ SQL gerada com sucesso")
        
        return {
            "sql_query": query,
            "source": "AI_GENERATION"
        }
    
    def reset_history(self):
        """Reseta o histórico de conversação"""
        self.query_generator.resetar_historico()
