"""
Assistente Ezinho - Versão Orientada a Objetos
Classe principal que orquestra todo o sistema de IA para responder perguntas
"""
import os
import pandas as pd
from datetime import datetime, timedelta
import re
from openai import OpenAI
from dotenv import load_dotenv

# Importa as classes criadas
from schema_manager import SchemaManager
from query_generator import QueryGenerator
from athena_executor import AthenaExecutor
from faq_matcher import FAQMatcher


class EzinhoAssistant:
    """
    Assistente principal que processa perguntas dos usuários e gera respostas inteligentes.
    Integra: FAQ Matching, Geração de SQL com IA, Execução no Athena e Formatação de Respostas.
    """
    
    def __init__(self):
        # Carrega variáveis de ambiente
        dotenv_path = os.path.join(os.path.dirname(__file__), "..", "config", ".env")
        load_dotenv(dotenv_path)
        
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.openai_api_key)
        self.enable_faq_matching = os.getenv("ENABLE_FAQ_MATCHING", "true").lower() in ("true", "1", "yes")
        
        # Inicializa componentes
        self.schema_manager = SchemaManager()
        self.query_generator = QueryGenerator(self.schema_manager)
        self.athena_executor = AthenaExecutor()
        self.faq_matcher = FAQMatcher() if self.enable_faq_matching else None
        
        # Lista de despedidas
        self.despedidas = [
            'tchau', 'até logo', 'até mais', 'até breve', 'adeus', 'valeu', 'obrigado', 'obrigada', 
            'grato', 'grata', 'bom dia', 'boa tarde', 'boa noite', 'tenha um bom dia', 
            'tenha uma boa tarde', 'tenha uma boa noite', 'see you', 'bye', 'thanks', 
            'thank you', 'bye bye', 'goodbye', 'see ya', 'see u', 'see you later',
            'obg', 'vlw', 'flw', 'abraço', 'abç', 'até amanhã', 'até segunda', 
            'até semana que vem', 'até mais tarde', 'até a próxima', 'até já', 
            'até daqui a pouco', 'até logo mais', 'até logo então'
        ]
    
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
                               ano_atual=None, ano_passado=None):
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
    
    def _processar_faq_match(self, pergunta):
        """Processa match com FAQ se disponível"""
        if not self.faq_matcher:
            return None
        
        try:
            print(f"[DEBUG] Sistema de FAQ Matching ATIVO - Buscando match para: '{pergunta}'")
            resultado_match = self.faq_matcher.buscar_pergunta_similar(pergunta)
            
            if resultado_match and resultado_match.get('can_reuse_query', False):
                similaridade = resultado_match.get('best_similarity', 0)
                print(f"[DEBUG] Match encontrado! Similaridade: {similaridade:.4f}")
                
                sql_aprovada = resultado_match.get('sql_aprovada', '')
                if sql_aprovada:
                    df = self.athena_executor.executar_query(sql_aprovada)
                    
                    if not isinstance(df, str):
                        if df.empty:
                            return {
                                "resposta": "⚠️ Nenhum resultado encontrado para a consulta pré-aprovada.",
                                "query": sql_aprovada,
                                "source": "FAQ_MATCH"
                            }
                        
                        # Formata valores monetários
                        df = self._formatar_valores_monetarios(df)
                        resultado_str = df.head(10).to_string(index=False)
                        
                        # Gera resposta natural
                        hoje = datetime.now().strftime('%d/%m/%Y')
                        resposta_natural = self._gerar_resposta_natural(
                            pergunta, resultado_str, 
                            datas_expl=f"Hoje é {hoje}"
                        )
                        
                        print(f"\n\033[92m🎯 QUERY MATCHING SYSTEM - SUCESSO!\033[0m")
                        print(f"\033[92m   ├── FAQ ID: {resultado_match.get('id', 'N/A')}\033[0m")
                        print(f"\033[92m   ├── Similaridade: {similaridade:.4f}\033[0m")
                        print(f"\033[92m   └── Executando SQL pré-aprovada\033[0m\n")
                        
                        return {
                            "resposta": f"✅ {resposta_natural}",
                            "query": sql_aprovada,
                            "source": "FAQ_MATCH",
                            "faq_id": resultado_match.get('id', 'N/A'),
                            "similarity": f"{similaridade:.4f}"
                        }
            else:
                print(f"\n\033[94m🤖 AI GENERATION SYSTEM - Nenhum match encontrado\033[0m")
                
        except Exception as e:
            print(f"\n\033[91m❌ MATCHING ERROR: {e}\033[0m")
        
        return None
    
    def _processar_despedida(self):
        """Processa despedidas do usuário"""
        print(f"\n\033[95m👋 DESPEDIDA DETECTADA\033[0m")
        
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
            "resposta": resposta_llm.choices[0].message.content.strip(),
            "query": None,
            "source": "GOODBYE"
        }
    
    def _processar_ajuda_coluna(self, pergunta):
        """Processa solicitações de ajuda sobre colunas"""
        print(f"\n\033[93m❓ AJUDA DE COLUNA SOLICITADA\033[0m")
        
        schemas = self.schema_manager.schemas
        tabela = "report_orders"  # Tabela padrão
        
        for coluna in schemas.get(tabela, {}):
            if coluna.lower() in pergunta.lower():
                print(f"\033[93m   └── Coluna encontrada: {coluna}\033[0m\n")
                descricao = schemas[tabela][coluna].get('description', 'Sem descrição')
                return {
                    "resposta": f"🔎 *{coluna}*: {descricao}",
                    "query": None,
                    "source": "COLUMN_HELP"
                }
        
        print(f"\033[93m   └── Coluna não encontrada\033[0m\n")
        return {
            "resposta": "❓ Não encontrei essa coluna na tabela. Por favor, forneça mais detalhes.",
            "query": None,
            "source": "COLUMN_HELP"
        }
    
    def responder(self, pergunta: str) -> dict:
        """
        Método principal que processa perguntas e retorna respostas.
        
        Args:
            pergunta: Pergunta do usuário
            
        Returns:
            dict: {'resposta': str, 'query': str|None, 'source': str, ...}
        """
        # 1. Verifica comando de reset
        if pergunta.strip() == "#resetar":
            print(f"\n\033[96m🔄 COMANDO RESET EXECUTADO\033[0m\n")
            self.query_generator.resetar_historico()
            return {
                "resposta": "🔄 Memória do assistente foi resetada com sucesso!",
                "query": None,
                "source": "RESET"
            }
        
        # 2. Verifica despedidas
        texto = pergunta.strip().lower()
        if any(desp in texto for desp in self.despedidas):
            return self._processar_despedida()
        
        # 3. Verifica ajuda sobre colunas
        if any(x in pergunta.lower() for x in ["significa", "explica", "o que é", "pra que serve"]):
            return self._processar_ajuda_coluna(pergunta)
        
        # 4. Tenta FAQ matching
        resultado_faq = self._processar_faq_match(pergunta)
        if resultado_faq:
            return resultado_faq
        
        # 5. Gera query com IA
        print(f"\n\033[94m🤖 AI GENERATION SYSTEM\033[0m\n")
        query = self.query_generator.gerar_query(pergunta)
        
        if not query or query.startswith("❌"):
            print(f"\n\033[91m❌ AI GENERATION FAILED\033[0m\n")
            return {
                "resposta": (query or "❓ Não consegui gerar uma query.") + "\nPor favor, reformule sua pergunta.",
                "query": query,
                "source": "AI_GENERATION_FAILED"
            }
        
        print(f"\n\033[92m🤖 AI GENERATION SYSTEM - SUCESSO!\033[0m")
        
        # Formata query para exibição
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
            query_formatada = format_resp.choices[0].message.content.strip()
        except Exception:
            query_formatada = query.strip()
        
        print("\n\033[91m📄 Query gerada:\033[0m")
        for linha in query_formatada.split('\n'):
            print(f"\033[91m    {linha}\033[0m")
        
        # 6. Executa query
        df = self.athena_executor.executar_query(query)
        
        if isinstance(df, str):
            return {
                "resposta": df + "\nPor favor, reformule sua pergunta.",
                "query": query_formatada,
                "source": "AI_GENERATION_ERROR"
            }
        
        if df.empty:
            return {
                "resposta": "⚠️ Nenhum resultado encontrado.",
                "query": query_formatada,
                "source": "AI_GENERATION_NO_RESULTS"
            }
        
        # 7. Formata resultado
        df = self._formatar_valores_monetarios(df)
        resultado_str = df.head(10).to_string(index=False)
        
        # 8. Extrai contexto temporal e gera resposta natural
        periodo, datas_expl, ano_atual, ano_passado = self._extrair_contexto_temporal(pergunta, df)
        resposta_natural = self._gerar_resposta_natural(
            pergunta, resultado_str, periodo, datas_expl, ano_atual, ano_passado
        )
        
        return {
            "resposta": resposta_natural,
            "query": query_formatada,
            "source": "AI_GENERATION_SUCCESS"
        }


# Mantém compatibilidade com código legado
def responder(pergunta: str) -> dict:
    """
    Função wrapper para manter compatibilidade com código existente.
    Cria uma instância do assistente e processa a pergunta.
    """
    assistant = EzinhoAssistant()
    return assistant.responder(pergunta)
