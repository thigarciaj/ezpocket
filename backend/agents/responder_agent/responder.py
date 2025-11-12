"""
NÓ 3: RESPONDER AGENT
Responsável por:
- Executar SQL no Athena
- Formatar valores monetários
- Gerar resposta natural usando IA
- Extrair contexto temporal
"""
import os
import pandas as pd
from datetime import datetime, timedelta
import re
from openai import OpenAI
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from athena_executor import AthenaExecutor


class ResponderAgent:
    """Agente que executa queries e formata respostas naturais"""
    
    def __init__(self):
        dotenv_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", ".env")
        load_dotenv(dotenv_path)
        
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.openai_api_key)
        self.athena_executor = AthenaExecutor()
    
    def _formatar_valores_monetarios(self, df):
        """Formata colunas monetárias com símbolo $"""
        colunas_monetarias = [
            'order total paid', 'early purchase value', 'contract total value expected',
            'remaining total', 'value', 'amount', 'paid', 'expected', 
            'recebido', 'devido', 'pago', 'receber'
        ]
        
        if not df.empty:
            for col in df.columns:
                if any(m in col.lower() for m in colunas_monetarias) and pd.api.types.is_float_dtype(df[col]):
                    df[col] = df[col].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else x)
        
        return df
    
    def _extrair_contexto_temporal(self, pergunta, df):
        """Extrai informações temporais da pergunta e do resultado"""
        hoje = datetime.now().strftime('%d/%m/%Y')
        ontem = (datetime.now() - timedelta(days=1)).strftime('%d/%m/%Y')
        ano_atual = datetime.now().year
        nome_mes_atual = datetime.now().strftime('%B').capitalize()
        ano_passado = ano_atual - 1
        
        datas_expl = []
        if re.search(r'\bhoje\b', pergunta, re.IGNORECASE):
            datas_expl.append(f"Hoje, dia {hoje}")
        if re.search(r'\bontem\b', pergunta, re.IGNORECASE):
            datas_expl.append(f"Ontem, dia {ontem}")
        
        match_mes = re.search(r'm[eê]s(\s+atual)?', pergunta, re.IGNORECASE)
        if match_mes:
            datas_expl.append(f"no mês de {nome_mes_atual} de {ano_atual}")
        
        match_ano = re.search(r'ano\s+(\d{4})', pergunta, re.IGNORECASE)
        if match_ano:
            datas_expl.append(f"no ano de {match_ano.group(1)}")
        
        if re.search(r'ano', pergunta, re.IGNORECASE):
            datas_expl.append(f"(Ano atual: {ano_atual}, ano anterior: {ano_passado})")
        
        # Extrai período dos dados
        periodo = ""
        colunas_data = ["contract start date", "date order created", "early purchase date", 
                       "cancelled at", "finished at"]
        
        for col in colunas_data:
            if col in df.columns:
                datas = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
                datas = datas.dropna()
                if not datas.empty:
                    data_min = datas.min().strftime('%d/%m/%Y')
                    data_max = datas.max().strftime('%d/%m/%Y')
                    periodo += f"Período considerado para '{col}': {data_min} a {data_max}. "
        
        datas_expl_str = ' '.join(datas_expl)
        datas_expl_str += f" (Hoje é {hoje})"
        
        return periodo, datas_expl_str, ano_atual, ano_passado
    
    def _gerar_resposta_natural(self, pergunta, resultado_str, periodo="", datas_expl="", 
                               ano_atual=None, ano_passado=None, query_formatada=""):
        """Gera uma resposta natural usando LLM"""
        if ano_atual is None:
            ano_atual = datetime.now().year
        if ano_passado is None:
            ano_passado = ano_atual - 1
        
        prompt_resposta = f"""Pergunta do usuário: {pergunta}
{periodo}
{datas_expl}
Resultado da consulta:
{resultado_str}

Formule uma resposta clara, natural e amigável para o usuário, explicando o resultado de acordo com a pergunta. 
Sempre mencione explicitamente o(s) período(s) de análise considerado(s), o ano atual ({ano_atual}) e o ano anterior ({ano_passado}) se a pergunta envolver comparação de anos, e quaisquer datas, meses ou anos citados na pergunta, em formato dd/mm/aaaa. 
Use SEMPRE a data do sistema como referência para 'hoje'. 
Não inclua código SQL, apenas a resposta final."""
        
        try:
            resposta_llm = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Você é um assistente de dados que responde perguntas de forma clara, natural e amigável."},
                    {"role": "user", "content": prompt_resposta}
                ],
                temperature=0.2,
            )
            return resposta_llm.choices[0].message.content
        except Exception as e:
            return f"✅ Resultado encontrado:\n{resultado_str}\n\n⚠️ (A resposta não pôde ser formatada pela LLM: {e})"
    
    def _formatar_query(self, query):
        """Formata query SQL para exibição"""
        try:
            format_prompt = f"Formate a seguinte query SQL para exibição legível:\n\n{query.strip()}"
            format_resp = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Você é um assistente que formata queries SQL."},
                    {"role": "user", "content": format_prompt}
                ],
                temperature=0,
            )
            return format_resp.choices[0].message.content.strip()
        except Exception:
            return query.strip()
    
    def respond(self, state: dict) -> dict:
        """
        Executa SQL e gera resposta natural
        
        Retorna:
            dict com:
            - resposta_final: Resposta formatada
            - query: Query SQL formatada
            - source: Origem da resposta
        """
        pergunta = state["pergunta"]
        sql_query = state.get("sql_query")
        source = state.get("source", "UNKNOWN")
        
        print(f"[RESPONDER] 🔄 Executando SQL e formatando resposta")
        
        # Se veio de FAQ, pode já ter resultado processado
        if source == "FAQ_MATCH" and state.get("faq_match"):
            print(f"[RESPONDER] 📋 Processando resultado de FAQ Match")
        
        # Formata query para exibição
        query_formatada = self._formatar_query(sql_query)
        
        print("[RESPONDER] 📄 Query formatada:")
        for linha in query_formatada.split('\n'):
            print(f"    {linha}")
        
        # Executa no Athena
        df = self.athena_executor.executar_query(sql_query)
        
        if isinstance(df, str):
            # Erro na execução
            return {
                "resposta_final": df + "\nPor favor, reformule sua pergunta.",
                "query": query_formatada,
                "source": f"{source}_ERROR"
            }
        
        if df.empty:
            return {
                "resposta_final": "⚠️ Nenhum resultado encontrado.",
                "query": query_formatada,
                "source": f"{source}_NO_RESULTS"
            }
        
        # Formata valores monetários
        df = self._formatar_valores_monetarios(df)
        resultado_str = df.head(10).to_string(index=False)
        
        # Extrai contexto temporal e gera resposta
        periodo, datas_expl, ano_atual, ano_passado = self._extrair_contexto_temporal(pergunta, df)
        resposta_natural = self._gerar_resposta_natural(
            pergunta, resultado_str, periodo, datas_expl, ano_atual, ano_passado, query_formatada
        )
        
        print(f"[RESPONDER] ✅ Resposta gerada com sucesso")
        
        resultado = {
            "resposta_final": resposta_natural if not resposta_natural.startswith("✅ Resultado") else resposta_natural,
            "query": query_formatada,
            "source": f"{source}_SUCCESS" if not resposta_natural.startswith("⚠️") else source
        }
        
        # Adiciona metadata do FAQ se aplicável
        if source == "FAQ_MATCH" and state.get("faq_match"):
            resultado["faq_id"] = state["faq_match"].get("id")
            resultado["similarity"] = state["faq_match"].get("best_similarity")
        
        return resultado
