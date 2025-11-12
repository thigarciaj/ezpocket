import json
import os
import math
from dotenv import load_dotenv
from openai import OpenAI

# =========================
# Config / Setup
# =========================

load_dotenv()

FAQ_FILE = os.getenv("FAQ_FILE", os.path.join(os.path.dirname(__file__), "json", "faq_queries_index.json"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
ENABLE_FAQ_MATCHING = os.getenv("ENABLE_FAQ_MATCHING", "true").lower() in ("true", "1", "yes")

if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY não encontrada no .env")

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# Utilidades
# =========================

def load_faq():
    if not os.path.exists(FAQ_FILE):
        raise FileNotFoundError(f"Arquivo {FAQ_FILE} não encontrado.")
    with open(FAQ_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def gerar_embedding_texto_livre(texto: str) -> list[float]:
    resp = client.embeddings.create(
        model=OPENAI_EMBED_MODEL,
        input=texto.strip()
    )
    return resp.data[0].embedding

def cosine_similarity(v1, v2):
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    return dot / (norm1 * norm2) if norm1 and norm2 else 0.0

# =========================
# Inferência de intenção (heurística MVP)
# =========================

def infer_intent_from_question(q: str) -> dict:
    q_low = q.lower()

    # Métrica
    if "venda" in q_low or "vendeu" in q_low:
        metric = "qtd_vendas"
    elif "inadimpl" in q_low or "atras" in q_low:
        metric = "inadimplencia"
    else:
        metric = "desconhecido"

    # Janela de tempo
    if "hoje" in q_low or "agora" in q_low:
        time_window = "hoje"
    elif "ontem" in q_low:
        time_window = "ontem"
    elif "semana" in q_low:
        time_window = "ultima_semana"
    elif "mês" in q_low or "mes " in q_low or "mensal" in q_low:
        time_window = "mes_atual"
    else:
        time_window = "desconhecido"

    # Granularidade
    if "por dealer" in q_low or "por loja" in q_low or "por parceiro" in q_low:
        granularity = "por_dealer"
    elif "por dia" in q_low or "por data" in q_low:
        granularity = "por_dia"
    else:
        granularity = "total"

    return {
        "metric": metric,
        "time_window": time_window,
        "granularity": granularity
    }

def intents_match(user_intent: dict, candidate_intent: dict) -> bool:
    for field in ["metric", "time_window", "granularity"]:
        u_val = user_intent.get(field, "desconhecido")
        c_val = candidate_intent.get(field, "desconhecido")
        if u_val != "desconhecido" and c_val != "desconhecido":
            if u_val != c_val:
                return False
    return True

# =========================
# Core: buscar pergunta similar
# =========================

def buscar_pergunta_similar(pergunta_usuario: str, similarity_threshold: float = 0.63):
    # Verifica se o sistema de matching está habilitado
    if not ENABLE_FAQ_MATCHING:
        print("⚠️ Sistema de FAQ Matching está DESABILITADO (ENABLE_FAQ_MATCHING=false)")
        return None
    
    faq_data = load_faq()
    user_vec = gerar_embedding_texto_livre(pergunta_usuario)

    # calcular similaridades
    scored = []
    for item in faq_data:
        cand_vec = item.get("embedding", [])
        if not cand_vec:
            continue
        sim = cosine_similarity(user_vec, cand_vec)
        scored.append((sim, item))

    if not scored:
        return None

    # ordenar por similaridade
    scored.sort(key=lambda x: x[0], reverse=True)

    # pegar top-3
    top3 = scored[:3]

    best_sim, best_item = top3[0]
    user_int = infer_intent_from_question(pergunta_usuario)
    cand_int = best_item.get("intent", {})
    same_intent = intents_match(user_int, cand_int)
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

# =========================
# Execução CLI
# =========================

if __name__ == "__main__":
    pergunta_usuario = input("💬 Pergunta do usuário: ").strip()
    resultado = buscar_pergunta_similar(pergunta_usuario)

    if not resultado:
        print("❌ Nenhum candidato encontrado (sem embeddings válidos).")
    else:
        print("\n=== RESULTADO DA BUSCA ===")
        print(f"🆔 Melhor ID: {resultado['id']}")
        print(f"📘 Pergunta oficial: {resultado['pergunta_original']}")
        print(f"📊 Similaridade (melhor): {resultado['best_similarity']:.4f}")

        print("\n--- 🔝 TOP 3 SIMILARIDADES ---")
        for rank, item in enumerate(resultado["top3"], start=1):
            print(f"{rank}. {item['id']}: {item['pergunta_texto']}  →  {item['similaridade']:.4f}")

        print("\n--- INTENÇÕES ---")
        print(f"🔹 Usuário:   {resultado['user_intent_inferida']}")
        print(f"🔹 Candidato: {resultado['cand_intent']}")
        print(f"🤝 Intenção compatível? {'✅ Sim' if resultado['same_intent'] else '❌ Não'}")

        print(f"\n⚙️ Pode reutilizar query pronta? {'✅ Sim' if resultado['can_reuse_query'] else '⚠️ Não'}")

        if resultado["can_reuse_query"]:
            print("\n--- SQL APROVADA ---")
            print(resultado["sql_aprovada"])
        else:
            print("\n⚠️ Esse caso deve seguir para geração de SQL nova.")
