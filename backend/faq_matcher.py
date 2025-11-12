"""
Módulo de matching de perguntas FAQ
Refatorado de match_question.py para melhor organização
"""
import json
import os
import math
from dotenv import load_dotenv
from openai import OpenAI

class FAQMatcher:
    """Sistema de matching de perguntas com FAQ pré-aprovadas"""
    
    def __init__(self):
        load_dotenv()
        
        self.faq_file = os.getenv("FAQ_FILE", os.path.join(os.path.dirname(__file__), "json", "faq_queries_index.json"))
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_embed_model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
        self.enable_faq_matching = os.getenv("ENABLE_FAQ_MATCHING", "true").lower() in ("true", "1", "yes")
        
        if not self.openai_api_key:
            raise ValueError("❌ OPENAI_API_KEY não encontrada no .env")
        
        self.client = OpenAI(api_key=self.openai_api_key)
    
    def _load_faq(self):
        """Carrega o arquivo de FAQ"""
        if not os.path.exists(self.faq_file):
            raise FileNotFoundError(f"Arquivo {self.faq_file} não encontrado.")
        with open(self.faq_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _gerar_embedding_texto(self, texto):
        """Gera embedding de um texto usando OpenAI"""
        resp = self.client.embeddings.create(
            model=self.openai_embed_model,
            input=texto.strip()
        )
        return resp.data[0].embedding
    
    def _cosine_similarity(self, v1, v2):
        """Calcula similaridade de cosseno entre dois vetores"""
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        return dot / (norm1 * norm2) if norm1 and norm2 else 0.0
    
    def _infer_intent(self, pergunta):
        """Infere a intenção da pergunta (heurística simples)"""
        p_low = pergunta.lower()
        
        # Métrica
        if "venda" in p_low or "vendeu" in p_low:
            metric = "qtd_vendas"
        elif "inadimpl" in p_low or "atras" in p_low:
            metric = "inadimplencia"
        else:
            metric = "desconhecido"
        
        # Janela de tempo
        if "hoje" in p_low or "agora" in p_low:
            time_window = "hoje"
        elif "ontem" in p_low:
            time_window = "ontem"
        elif "semana" in p_low:
            time_window = "ultima_semana"
        elif "mês" in p_low or "mes " in p_low or "mensal" in p_low:
            time_window = "mes_atual"
        else:
            time_window = "desconhecido"
        
        # Granularidade
        if "por dealer" in p_low or "por loja" in p_low or "por parceiro" in p_low:
            granularity = "por_dealer"
        elif "por dia" in p_low or "por data" in p_low:
            granularity = "por_dia"
        else:
            granularity = "total"
        
        return {
            "metric": metric,
            "time_window": time_window,
            "granularity": granularity
        }
    
    def _intents_match(self, user_intent, candidate_intent):
        """Verifica se duas intenções são compatíveis"""
        for field in ["metric", "time_window", "granularity"]:
            u_val = user_intent.get(field, "desconhecido")
            c_val = candidate_intent.get(field, "desconhecido")
            if u_val != "desconhecido" and c_val != "desconhecido":
                if u_val != c_val:
                    return False
        return True
    
    def buscar_pergunta_similar(self, pergunta_usuario, similarity_threshold=0.63):
        """Busca perguntas similares no FAQ"""
        # Verifica se o sistema está habilitado
        if not self.enable_faq_matching:
            print("⚠️ Sistema de FAQ Matching está DESABILITADO")
            return None
        
        faq_data = self._load_faq()
        user_vec = self._gerar_embedding_texto(pergunta_usuario)
        
        # Calcula similaridades
        scored = []
        for item in faq_data:
            cand_vec = item.get("embedding", [])
            if not cand_vec:
                continue
            sim = self._cosine_similarity(user_vec, cand_vec)
            scored.append((sim, item))
        
        if not scored:
            return None
        
        # Ordena por similaridade
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Pega top-3
        top3 = scored[:3]
        
        best_sim, best_item = top3[0]
        user_int = self._infer_intent(pergunta_usuario)
        cand_int = best_item.get("intent", {})
        same_intent = self._intents_match(user_int, cand_int)
        can_reuse = (best_sim >= similarity_threshold) and same_intent
        
        resultado = {
            "top3": [
                {
                    "id": item.get("id"),
                    "pergunta_texto": item.get("pergunta_texto"),
                    "similaridade": sim
                }
                for sim, item in top3
            ],
            "best_similarity": best_sim,
            "user_intent_inferida": user_int,
            "cand_intent": cand_int,
            "same_intent": same_intent,
            "can_reuse_query": can_reuse,
            "id": best_item.get("id"),
            "pergunta_original": best_item.get("pergunta_texto"),
            "sql_aprovada": best_item.get("sql_aprovada") if can_reuse else None,
            "owner": best_item.get("owner"),
            "ultima_validacao": best_item.get("ultima_validacao")
        }
        
        return resultado
