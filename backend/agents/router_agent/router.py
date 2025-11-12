"""
NÓ 1: ROUTER AGENT
Responsável por:
- Detectar casos especiais (despedidas, ajuda, reset)
- Tentar match com FAQ (usando embeddings)
- Decidir se usa FAQ ou gera nova query
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from faq_matcher import FAQMatcher


class RouterAgent:
    """Agente que roteia a pergunta para FAQ ou geração de query"""
    
    def __init__(self):
        dotenv_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", ".env")
        load_dotenv(dotenv_path)
        
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.openai_api_key)
        self.enable_faq_matching = os.getenv("ENABLE_FAQ_MATCHING", "true").lower() in ("true", "1", "yes")
        
        # Inicializa FAQ Matcher
        self.faq_matcher = FAQMatcher() if self.enable_faq_matching else None
        
        # Lista de despedidas
        self.despedidas = [
            'tchau', 'até logo', 'até mais', 'até breve', 'adeus', 'valeu', 'obrigado', 'obrigada', 
            'grato', 'grata', 'bom dia', 'boa tarde', 'boa noite', 'see you', 'bye', 'thanks', 
            'thank you', 'bye bye', 'goodbye', 'obg', 'vlw', 'flw', 'abraço', 'abç'
        ]
    
    def route(self, state: dict) -> dict:
        """
        Método principal que decide o roteamento
        
        Retorna:
            dict com:
            - route: "special" | "faq" | "generate"
            - tipo: tipo de caso especial (se aplicável)
            - faq_match: dados do match (se aplicável)
            - sql_query: SQL pré-aprovada (se FAQ match)
        """
        pergunta = state["pergunta"]
        
        # 1. Verifica comando reset
        if pergunta.strip() == "#resetar":
            return {
                "route": "special",
                "tipo": "reset",
                "resposta_final": "🔄 Memória do assistente foi resetada com sucesso!",
                "query": None,
                "source": "RESET"
            }
        
        # 2. Verifica despedidas
        texto = pergunta.strip().lower()
        if any(desp in texto for desp in self.despedidas):
            return {
                "route": "special",
                "tipo": "despedida"
            }
        
        # 3. Verifica ajuda sobre colunas
        if any(x in pergunta.lower() for x in ["significa", "explica", "o que é", "pra que serve"]):
            return {
                "route": "special",
                "tipo": "help",
                "pergunta": pergunta
            }
        
        # 4. Tenta FAQ matching
        if self.faq_matcher:
            try:
                print(f"[ROUTER] Buscando FAQ match para: '{pergunta}'")
                resultado_match = self.faq_matcher.buscar_pergunta_similar(pergunta)
                
                if resultado_match and resultado_match.get('can_reuse_query', False):
                    similaridade = resultado_match.get('best_similarity', 0)
                    print(f"[ROUTER] ✅ FAQ Match encontrado! Similaridade: {similaridade:.4f}")
                    
                    return {
                        "route": "faq",
                        "faq_match": resultado_match,
                        "sql_query": resultado_match.get('sql_aprovada'),
                        "source": "FAQ_MATCH"
                    }
                else:
                    print(f"[ROUTER] ❌ Nenhum FAQ match - seguindo para geração")
                    
            except Exception as e:
                print(f"[ROUTER] ⚠️ Erro no FAQ matching: {e}")
        
        # 5. Sem match - precisa gerar nova query
        return {
            "route": "generate",
            "source": "AI_GENERATION"
        }
    
    def handle_special(self, state: dict) -> dict:
        """Processa casos especiais (despedida, ajuda, reset)"""
        tipo = state.get("tipo")
        
        if tipo == "reset":
            # Reset já foi tratado no route()
            return state
        
        if tipo == "despedida":
            print(f"[ROUTER] 👋 Gerando despedida")
            
            prompt = (
                "O usuário está se despedindo, agradecendo ou encerrando a conversa. "
                "Responda de forma simpática, natural, breve e personalizada, agradecendo o contato, "
                "desejando algo positivo e se colocando à disposição para futuras dúvidas. "
                "Inclua obrigatoriamente na resposta algum trocadilho, menção criativa ou referência "
                "divertida a iPhones, iPads ou Apple Watches, que são os produtos vendidos pela EZPAG. "
                "Seja criativo, use emojis e varie as respostas."
            )
            
            resposta_llm = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Você é um assistente de dados simpático, educado e amigável."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
            )
            
            return {
                "resposta_final": resposta_llm.choices[0].message.content.strip(),
                "query": None,
                "source": "GOODBYE"
            }
        
        if tipo == "help":
            print(f"[ROUTER] ❓ Processando ajuda de coluna")
            pergunta = state["pergunta"]
            
            # Importa schema manager
            from schema_manager import SchemaManager
            schema_manager = SchemaManager()
            schemas = schema_manager.schemas
            
            tabela = "report_orders"
            for coluna in schemas.get(tabela, {}):
                if coluna.lower() in pergunta.lower():
                    descricao = schemas[tabela][coluna].get('description', 'Sem descrição')
                    return {
                        "resposta_final": f"🔎 *{coluna}*: {descricao}",
                        "query": None,
                        "source": "COLUMN_HELP"
                    }
            
            return {
                "resposta_final": "❓ Não encontrei essa coluna na tabela. Por favor, forneça mais detalhes.",
                "query": None,
                "source": "COLUMN_HELP"
            }
        
        return state
