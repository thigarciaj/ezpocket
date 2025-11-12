import os
from dotenv import load_dotenv
from openai import OpenAI

# Carrega o .env com as variáveis de ambiente
load_dotenv()

# Lê a chave da variável de ambiente
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("❌ OPENAI_API_KEY não encontrada. Verifique seu .env")

# Instancia cliente OpenAI
client = OpenAI(api_key=api_key)

# Testa chamada
models = client.models.list()
print("✅ Modelos disponíveis:", [m.id for m in models.data])
