#!/usr/bin/env python3
"""
Database Executor Agent - Executa queries SQL no AWS Athena ou PostgreSQL Local
Este agente NÃO usa IA, apenas executa a query final no banco configurado
Verifica a variável BD_REFERENCE para decidir qual banco usar
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import awswrangler as wr
import boto3
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Adicionar paths necessários
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

class AthenaExecutorAgent:
    """
    Executa queries SQL no AWS Athena ou PostgreSQL Local
    - Recebe query final (validada ou corrigida)
    - Verifica BD_REFERENCE para decidir qual banco usar
    - Executa no Athena (BD_REFERENCE=Athena) ou PostgreSQL (BD_REFERENCE=Local)
    - Retorna resultados ou erro
    - NÃO usa IA
    """
    
    def __init__(self):
        """Inicializa o executor do banco de dados"""
        # Carregar variáveis de ambiente
        credentials_path = Path(__file__).parent / "credentials.env"
        load_dotenv(credentials_path)
        
        # Carregar .env do projeto (com override para garantir reload)
        project_env = Path(__file__).parent.parent.parent / ".env"
        load_dotenv(project_env)
        
        # Verificar qual banco usar
        self.bd_reference = os.getenv("BD_REFERENCE", "Athena")
        
        # Configurações Athena
        self.athena_output_s3 = os.getenv("ATHENA_OUTPUT_S3")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.athena_database = os.getenv("ATHENA_DATABASE", "receivables_db")
        
        # Configurações PostgreSQL
        self.postgres_host = os.getenv("POSTGRES_HOST", "localhost")
        self.postgres_port = os.getenv("POSTGRES_PORT", "5546")
        self.postgres_db = os.getenv("POSTGRES_DB", "ezpocket_logs")
        self.postgres_user = os.getenv("POSTGRES_USER", "ezpocket_user")
        self.postgres_password = os.getenv("POSTGRES_PASSWORD", "ezpocket_pass_2025")
        
        # Se Athena, inicializar boto3
        if self.bd_reference == "Athena":
            aws_access_key = os.getenv("AWS_ACCESS_KEY")
            aws_secret_key = os.getenv("AWS_SECRET_KEY")
            
            self.boto3_session = boto3.Session(
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=self.aws_region,
            )
            
            print(f"✅ Database Executor inicializado - Modo: AWS ATHENA")
            print(f"   Database: {self.athena_database}")
            print(f"   Region: {self.aws_region}")
            print(f"   S3 Output: {self.athena_output_s3}")
        else:
            print(f"✅ Database Executor inicializado - Modo: POSTGRESQL LOCAL")
            print(f"   Host: {self.postgres_host}")
            print(f"   Port: {self.postgres_port}")
            print(f"   Database: {self.postgres_db}")
    
    def _format_results_message(self, df, row_count: int, column_count: int) -> str:
        """
        Formata os resultados do DataFrame em uma mensagem legível
        """
        if row_count == 0:
            return "   ℹ️  Nenhum resultado encontrado."
        
        # Para queries de agregação (COUNT, SUM, AVG, etc.)
        if row_count == 1 and column_count == 1:
            col_name = df.columns[0]
            value = df.iloc[0, 0]
            return f"   🎯 Resultado: {col_name} = {value:,}" if isinstance(value, (int, float)) else f"   🎯 Resultado: {col_name} = {value}"
        
        # Para queries com poucas linhas (até 10), mostrar tudo
        if row_count <= 10:
            lines = ["   📊 Resultados encontrados:\n"]
            for idx, row in df.iterrows():
                lines.append(f"   [{idx+1}] {dict(row)}")
            return "\n".join(lines)
        
        # Para queries com muitas linhas, mostrar resumo + primeiras 5
        lines = [f"   📊 {row_count:,} resultados encontrados. Mostrando os primeiros 5:\n"]
        for idx, row in df.head(5).iterrows():
            lines.append(f"   [{idx+1}] {dict(row)}")
        lines.append(f"\n   ℹ️  Use 'results_full' para ver todos os {row_count:,} resultados.")
        return "\n".join(lines)
    
    def _execute_postgresql(self, query_sql: str) -> pd.DataFrame:
        """Executa query no PostgreSQL e retorna DataFrame"""
        conn = psycopg2.connect(
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
            user=self.postgres_user,
            password=self.postgres_password
        )
        
        try:
            df = pd.read_sql_query(query_sql, conn)
            return df
        finally:
            conn.close()
    
    def _execute_athena(self, query_sql: str) -> pd.DataFrame:
        """Executa query no Athena e retorna DataFrame"""
        return wr.athena.read_sql_query(
            sql=query_sql,
            database=self.athena_database,
            boto3_session=self.boto3_session,
            s3_output=self.athena_output_s3,
        )
    
    def execute(self,
                query_sql: str,
                username: str,
                projeto: str) -> Dict[str, Any]:
        """
        Executa query SQL no banco configurado (Athena ou PostgreSQL)
        
        Args:
            query_sql: Query SQL final a ser executada
            username: Usuário que solicitou
            projeto: Projeto do usuário
            
        Returns:
            Dict com resultado da execução
        """
        database_name = "AWS ATHENA" if self.bd_reference == "Athena" else "POSTGRESQL LOCAL"
        
        print(f"\n{'='*80}")
        print(f"🚀 DATABASE EXECUTOR AGENT - EXECUÇÃO DE QUERY")
        print(f"{'='*80}")
        print(f"📥 INPUTS:")
        print(f"   🎯 Banco de Dados: {database_name}")
        print(f"   👤 Username: {username}")
        print(f"   📁 Projeto: {projeto}")
        print(f"   📝 Query (primeiros 200 chars): {query_sql[:200]}...")
        print(f"{'='*80}\n")
        
        start_time = datetime.now()
        
        try:
            print("⚙️  PROCESSAMENTO:")
            print(f"   🔄 Executando query no {database_name}...")
            print(f"   🔍 DEBUG: BD_REFERENCE = '{self.bd_reference}'")
            print(f"   🔍 DEBUG: Condição (self.bd_reference == 'Athena'): {self.bd_reference == 'Athena'}")
            
            # Executar query no banco correto
            if self.bd_reference == "Athena":
                print(f"   ➡️  EXECUTANDO NO ATHENA")
                df = self._execute_athena(query_sql)
            else:
                print(f"   ➡️  EXECUTANDO NO POSTGRESQL")
                print(f"   📍 Host: {self.postgres_host}:{self.postgres_port}")
                print(f"   📍 Database: {self.postgres_db}")
                df = self._execute_postgresql(query_sql)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Informações sobre o resultado
            row_count = len(df)
            column_count = len(df.columns)
            columns = df.columns.tolist()
            
            # Converter DataFrame para formato JSON serializable
            results_preview = df.head(100).to_dict('records')  # Primeiras 100 linhas
            results_full = df.to_dict('records')  # Todos os resultados
            
            # Calcular tamanho estimado dos dados
            data_size_bytes = df.memory_usage(deep=True).sum()
            data_size_mb = data_size_bytes / (1024 * 1024)
            
            # Gerar mensagem amigável com os resultados
            result_message = self._format_results_message(df, row_count, column_count)
            
            result = {
                'success': True,
                'query_executed': query_sql,
                'execution_time_seconds': execution_time,
                'row_count': row_count,
                'column_count': column_count,
                'columns': columns,
                'results_preview': results_preview,
                'results_full': results_full,  # Todos os resultados
                'results_message': result_message,  # Mensagem formatada
                'data_size_mb': round(data_size_mb, 2),
                'database': self.athena_database if self.bd_reference == "Athena" else self.postgres_db,
                'database_type': self.bd_reference,
                'region': self.aws_region if self.bd_reference == "Athena" else None,
                'error': None
            }
            
            print(f"\n{'='*80}")
            print(f"📤 OUTPUT:")
            print(f"   ✅ Execução bem-sucedida no {database_name}")
            print(f"   📊 Linhas retornadas: {row_count:,}")
            print(f"   📋 Colunas: {column_count} - {columns}")
            print(f"   💾 Tamanho dos dados: {data_size_mb:.2f} MB")
            print(f"   ⏱️  Tempo de execução: {execution_time:.2f}s")
            print(f"   🏛️  Database: {result['database']}")
            print(f"\n📋 RESULTADOS:")
            print(result_message)
            print(f"{'='*80}\n")
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            print(f"\n{'='*80}")
            print(f"📤 OUTPUT:")
            print(f"   ❌ Erro na execução")
            print(f"   🚨 Erro: {error_msg}")
            print(f"   ⏱️  Tempo de execução: {execution_time:.2f}s")
            print(f"{'='*80}\n")
            
            return {
                'success': False,
                'query_executed': query_sql,
                'execution_time_seconds': execution_time,
                'row_count': 0,
                'column_count': 0,
                'columns': [],
                'results_preview': [],
                'data_size_mb': 0,
                'database': self.athena_database if self.bd_reference == "Athena" else self.postgres_db,
                'database_type': self.bd_reference,
                'region': self.aws_region if self.bd_reference == "Athena" else None,
                'error': error_msg,
                'error_type': type(e).__name__
            }


# Para testes standalone
if __name__ == '__main__':
    executor = AthenaExecutorAgent()
    
    # Teste simples
    test_query = "SELECT * FROM orders LIMIT 10"
    result = executor.execute(
        query_sql=test_query,
        username='test_user',
        projeto='test_project'
    )
    
    print("\n🧪 Resultado do teste:")
    print(f"Success: {result['success']}")
    print(f"Rows: {result['row_count']}")
    print(f"Columns: {result['columns']}")
