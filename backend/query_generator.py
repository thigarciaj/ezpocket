"""
Módulo de geração de queries SQL com IA
Refatorado de ezinho.py para melhor organização
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

class QueryGenerator:
    """Gera queries SQL usando OpenAI GPT"""
    
    def __init__(self, schema_manager):
        # Carrega variáveis de ambiente
        dotenv_path = os.path.join(os.path.dirname(__file__), "..", "config", ".env")
        load_dotenv(dotenv_path)
        
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.openai_api_key)
        self.schema_manager = schema_manager
        self.historico_conversa = []
    
    def limpar_resposta_sql(self, resposta):
        """Limpa a resposta SQL removendo marcadores desnecessários"""
        resposta = resposta.strip().strip("`").strip()
        if resposta.lower().startswith("sql"):
            resposta = resposta[3:].lstrip()
        return resposta
    
    def gerar_query(self, pergunta):
        """Gera uma query SQL baseada na pergunta do usuário"""
        tabela = self.schema_manager.identificar_tabela(pergunta)
        schema = self.schema_manager.get_schema(tabela)
        instrucao = self.schema_manager.get_instrucoes(tabela)
        
        schema_texto = self.schema_manager.formatar_schema_para_prompt(schema)
        instrucoes_texto = "\n".join(instrucao.get("instructions", []))
        regras_semanticas = "\n".join(instrucao.get("regras_semanticas", []))
        query_athena = "\n".join(instrucao.get("query_athena", []))
        
        exemplos = instrucao.get("examples") or instrucao.get("exemplos_queries") or []
        exemplos_texto = "\n".join([
            f"Pergunta: {ex['question']}\nQuery: {ex['query']}" if isinstance(ex, dict) and 'question' in ex and 'query' in ex else str(ex)
            for ex in exemplos
        ])
        
        # Regras críticas
        regras_criticas = [
            "RESPOSTA DEVE SER APENAS SQL PURO - SEM texto, comentários, explicações ou blocos ```sql",
            "NUNCA comece com 'Entendi', 'Aqui está', 'A query é' ou qualquer texto explicativo",
            "PRIMEIRA LINHA da resposta deve ser SELECT, WITH, ou outro comando SQL válido"
        ]
        
        # Carregar funções proibidas se existir
        funcoes_proibidas_info = instrucao.get("funcoes_proibidas", {})
        for funcao_info in funcoes_proibidas_info.get("athena_funcoes_proibidas", []):
            regras_criticas.append(f"NUNCA use {funcao_info['funcao']} - {funcao_info['motivo']}")
            regras_criticas.append(f"   Alternativa: {funcao_info['alternativa']}")
        
        regras_criticas_texto = "\n".join(regras_criticas)
        
        system_msg = {
            "role": "system",
            "content": f"""
REGRAS CRÍTICAS - LEIA PRIMEIRO:
{regras_criticas_texto}

Você é um assistente de dados que gera SQL para Amazon Athena.

Use apenas a tabela '{tabela}' do banco receivables_db.

🧾 Aqui está o schema da tabela (nome da coluna entre aspas):
{schema_texto}

{instrucoes_texto}

{regras_semanticas}

{query_athena}

Exemplos:
{exemplos_texto}

⚠️ Gere apenas a query SQL pura (sem comentários, explicações ou blocos de código).
""".strip()
        }
        
        mensagens = [system_msg] + self.historico_conversa[-6:] + [{"role": "user", "content": pergunta}]
        
        try:
            resposta = self.client.chat.completions.create(
                model="gpt-4o",
                messages=mensagens,
                temperature=0,
            )
            content = resposta.choices[0].message.content
            self.historico_conversa.append({"role": "user", "content": pergunta})
            self.historico_conversa.append({"role": "assistant", "content": content})
            return self.limpar_resposta_sql(content)
        except Exception as e:
            return f"❌ Erro ao gerar query com OpenAI: {e}"
    
    def resetar_historico(self):
        """Reseta o histórico de conversação"""
        self.historico_conversa.clear()
