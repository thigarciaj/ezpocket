"""
Módulo de execução de queries no Amazon Athena
Refatorado de ezinho.py para melhor organização
"""
import awswrangler as wr
import boto3
import os
from dotenv import load_dotenv

class AthenaExecutor:
    """Executa queries SQL no Amazon Athena"""
    
    def __init__(self):
        # Carrega variáveis de ambiente
        dotenv_path = os.path.join(os.path.dirname(__file__), "..", "config", ".env")
        load_dotenv(dotenv_path)
        
        self.athena_output_s3 = os.getenv("ATHENA_OUTPUT_S3")
        self.aws_region = os.getenv("AWS_REGION")
        self.database = "receivables_db"
        
        # Sessão boto3
        self.boto3_session = boto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
            region_name=self.aws_region,
        )
    
    def executar_query(self, query):
        """Executa uma query no Athena e retorna o resultado como DataFrame"""
        try:
            print("\n🔄 Deixe-me analisar para você, um momento...\n")
            df = wr.athena.read_sql_query(
                sql=query,
                database=self.database,
                boto3_session=self.boto3_session,
                s3_output=self.athena_output_s3,
            )
            return df
        except Exception as e:
            return f"❌ Erro ao executar a query: {e}"
    
    def validar_query(self, query):
        """Valida uma query SQL antes de executar"""
        # Implementar validações básicas
        if not query or not query.strip():
            return False, "Query vazia"
        
        query_lower = query.lower().strip()
        
        # Verifica comandos perigosos
        comandos_perigosos = ['drop', 'delete', 'truncate', 'insert', 'update']
        for cmd in comandos_perigosos:
            if cmd in query_lower:
                return False, f"Comando '{cmd}' não é permitido"
        
        return True, "Query válida"
