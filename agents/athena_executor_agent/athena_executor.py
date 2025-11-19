#!/usr/bin/env python3
"""
Athena Executor Agent - Executa queries SQL no AWS Athena
Este agente NÃO usa IA, apenas executa a query final no Athena
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import awswrangler as wr
import boto3
from dotenv import load_dotenv

# Adicionar paths necessários
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

class AthenaExecutorAgent:
    """
    Executa queries SQL no AWS Athena
    - Recebe query final (validada ou corrigida)
    - Executa no Athena
    - Retorna resultados ou erro
    - NÃO usa IA
    """
    
    def __init__(self):
        """Inicializa o executor do Athena"""
        # Carregar credenciais do credentials.env
        credentials_path = Path(__file__).parent / "credentials.env"
        load_dotenv(credentials_path)
        
        self.athena_output_s3 = os.getenv("ATHENA_OUTPUT_S3")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.database = os.getenv("DATABASE", "receivables_db")
        
        aws_access_key = os.getenv("AWS_ACCESS_KEY")
        aws_secret_key = os.getenv("AWS_SECRET_KEY")
        
        # Sessão boto3
        self.boto3_session = boto3.Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=self.aws_region,
        )
        
        print(f"✅ Athena Executor inicializado")
        print(f"   Database: {self.database}")
        print(f"   Region: {self.aws_region}")
        print(f"   S3 Output: {self.athena_output_s3}")
    
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
    
    def execute(self,
                query_sql: str,
                username: str,
                projeto: str) -> Dict[str, Any]:
        """
        Executa query SQL no Athena
        
        Args:
            query_sql: Query SQL final a ser executada
            username: Usuário que solicitou
            projeto: Projeto do usuário
            
        Returns:
            Dict com resultado da execução
        """
        print(f"\n{'='*80}")
        print(f"🚀 ATHENA EXECUTOR AGENT - EXECUÇÃO DE QUERY")
        print(f"{'='*80}")
        print(f"📥 INPUTS:")
        print(f"   👤 Username: {username}")
        print(f"   📁 Projeto: {projeto}")
        print(f"   📝 Query (primeiros 200 chars): {query_sql[:200]}...")
        print(f"{'='*80}\n")
        
        start_time = datetime.now()
        
        try:
            print("⚙️  PROCESSAMENTO:")
            print("   🔄 Executando query no AWS Athena...")
            
            # Executar query no Athena
            df = wr.athena.read_sql_query(
                sql=query_sql,
                database=self.database,
                boto3_session=self.boto3_session,
                s3_output=self.athena_output_s3,
            )
            
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
                'database': self.database,
                'region': self.aws_region,
                'error': None
            }
            
            print(f"\n{'='*80}")
            print(f"📤 OUTPUT:")
            print(f"   ✅ Execução bem-sucedida")
            print(f"   📊 Linhas retornadas: {row_count:,}")
            print(f"   📋 Colunas: {column_count} - {columns}")
            print(f"   💾 Tamanho dos dados: {data_size_mb:.2f} MB")
            print(f"   ⏱️  Tempo de execução: {execution_time:.2f}s")
            print(f"   🏛️  Database: {self.database}")
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
                'database': self.database,
                'region': self.aws_region,
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
