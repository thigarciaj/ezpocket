#!/usr/bin/env python3
"""
Data Sync Agent - Sincronização Athena -> PostgreSQL
Sincroniza dados do order_report do Athena para PostgreSQL
Executa uma vez e sai (para uso com PM2 cron_restart)
"""

import os
import sys
import psycopg2
import pandas as pd
from datetime import datetime
from pytz import timezone
import boto3
import time
import logging
import json
from typing import Optional, Dict, Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/servidores/ezpocket/agents/data_sync_agent/data_sync.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DataSyncAgent:
    def __init__(self):
        """Inicializar o agente de sincronização"""
        self.load_config()
        self.setup_clients()
        
    def load_config(self):
        """Carregar configurações do .env"""
        self.postgres_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5546)),
            'database': os.getenv('POSTGRES_DB', 'ezpocket_logs'),
            'user': os.getenv('POSTGRES_USER', 'ezpocket_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'ezpocket_pass_2025')
        }
        
        self.aws_config = {
            'access_key': os.getenv('AWS_ACCESS_KEY'),
            'secret_key': os.getenv('AWS_SECRET_KEY'),
            'region': os.getenv('AWS_REGION', 'us-east-1'),
            'database': os.getenv('ATHENA_DATABASE', 'receivables_db'),
            'output_location': os.getenv('ATHENA_OUTPUT_S3', 's3://ezpocket-athena-results/')
        }
        
        self.sync_config = {
            'athena_table': os.getenv('DATA_SYNC_ATHENA_TABLE', 'order_report'),
            'postgres_table': os.getenv('DATA_SYNC_POSTGRES_TABLE', 'order_report'),
            'batch_size': int(os.getenv('DATA_SYNC_BATCH_SIZE', 1000)),
            'max_retries': int(os.getenv('DATA_SYNC_MAX_RETRIES', 3)),
            'retry_delay': int(os.getenv('DATA_SYNC_RETRY_DELAY', 300))  # 5 minutos
        }
        
        logger.info("🔧 Configurações carregadas para execução única")
        
    def setup_clients(self):
        """Configurar clientes AWS e PostgreSQL"""
        try:
            # Cliente Athena
            self.athena_client = boto3.client(
                'athena',
                aws_access_key_id=self.aws_config['access_key'],
                aws_secret_access_key=self.aws_config['secret_key'],
                region_name=self.aws_config['region']
            )
            
            # Cliente S3 para resultados
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_config['access_key'],
                aws_secret_access_key=self.aws_config['secret_key'],
                region_name=self.aws_config['region']
            )
            
            logger.info("✅ Clientes AWS configurados")
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar clientes AWS: {e}")
            raise
    
    def get_postgres_connection(self):
        """Obter conexão PostgreSQL"""
        try:
            conn = psycopg2.connect(**self.postgres_config)
            return conn
        except Exception as e:
            logger.error(f"❌ Erro ao conectar PostgreSQL: {e}")
            raise
    
    def execute_athena_query(self, query: str) -> Optional[str]:
        """Executar query no Athena e retornar execution_id"""
        try:
            logger.info(f"🔍 Executando query no Athena...")
            
            response = self.athena_client.start_query_execution(
                QueryString=query,
                QueryExecutionContext={
                    'Database': self.aws_config['database']
                },
                ResultConfiguration={
                    'OutputLocation': self.aws_config['output_location']
                }
            )
            
            execution_id = response['QueryExecutionId']
            logger.info(f"📋 Query iniciada - ID: {execution_id}")
            
            return execution_id
            
        except Exception as e:
            logger.error(f"❌ Erro ao executar query Athena: {e}")
            return None
    
    def wait_for_query_completion(self, execution_id: str, max_wait: int = 300) -> Dict[str, Any]:
        """Aguardar conclusão da query no Athena"""
        start_time = time.time()
        
        while (time.time() - start_time) < max_wait:
            try:
                response = self.athena_client.get_query_execution(
                    QueryExecutionId=execution_id
                )
                
                status = response['QueryExecution']['Status']['State']
                
                if status == 'SUCCEEDED':
                    logger.info(f"✅ Query concluída com sucesso")
                    return {
                        'success': True,
                        'execution': response['QueryExecution']
                    }
                elif status == 'FAILED':
                    error = response['QueryExecution']['Status'].get('StateChangeReason', 'Erro desconhecido')
                    logger.error(f"❌ Query falhou: {error}")
                    return {
                        'success': False,
                        'error': error
                    }
                elif status in ['CANCELLED', 'CANCELLED']:
                    logger.warning(f"⚠️ Query cancelada")
                    return {
                        'success': False,
                        'error': 'Query cancelada'
                    }
                
                # Query ainda em execução
                logger.info(f"⏳ Query em execução... Status: {status}")
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"❌ Erro ao verificar status da query: {e}")
                return {
                    'success': False,
                    'error': str(e)
                }
        
        logger.error(f"⏰ Timeout aguardando conclusão da query")
        return {
            'success': False,
            'error': 'Timeout'
        }
    
    def get_athena_results(self, execution_id: str) -> Optional[pd.DataFrame]:
        """Obter resultados da query do Athena com paginação"""
        try:
            all_rows = []
            next_token = None
            page = 1
            
            # Loop de paginação
            while True:
                # Obter resultados (com ou sem token de paginação)
                if next_token:
                    response = self.athena_client.get_query_results(
                        QueryExecutionId=execution_id,
                        NextToken=next_token
                    )
                else:
                    response = self.athena_client.get_query_results(
                        QueryExecutionId=execution_id
                    )
                
                rows = response['ResultSet']['Rows']
                
                # Na primeira página, pegar headers e pular primeira linha
                if page == 1:
                    if not rows:
                        logger.warning("⚠️ Nenhum resultado encontrado")
                        return pd.DataFrame()
                    
                    # Primeira linha são os headers
                    headers = [col['VarCharValue'] for col in rows[0]['Data']]
                    rows = rows[1:]  # Pular headers
                
                # Adicionar linhas desta página
                all_rows.extend(rows)
                logger.info(f"📄 Página {page}: {len(rows)} registros obtidos (total acumulado: {len(all_rows)})")
                
                # Verificar se há mais páginas
                next_token = response.get('NextToken')
                if not next_token:
                    break
                
                page += 1
            
            # Processar todas as linhas
            data = []
            for row in all_rows:
                row_data = []
                for col in row['Data']:
                    value = col.get('VarCharValue', '')
                    # Tratar valores nulos/vazios
                    if value == '' or value == 'null':
                        row_data.append(None)
                    else:
                        row_data.append(value)
                data.append(row_data)
            
            # Criar DataFrame
            df = pd.DataFrame(data, columns=headers)
            logger.info(f"📊 Total de dados obtidos: {len(df)} registros de {page} páginas")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter resultados do Athena: {e}")
            return None
    
    def fetch_athena_data(self) -> Optional[pd.DataFrame]:
        """Buscar dados completos do report_orders no Athena"""
        query = f"""
        SELECT 
            "Order Code",
            "Date Order Created",
            "Status",
            "Customer Name",
            "Customer Email",
            "Customer Phone Number",
            "customer_income",
            "Shipping Address",
            "Zip Code",
            "item_name",
            "Serial Number",
            "IMEI 1",
            "IMEI 2",
            "TAC Expected",
            "TAC Paid",
            "Downpayment Paid",
            "Taxes Percent",
            "Installments Value",
            "Taxes Value Installments",
            "Taxes Value Initial Payment",
            "Total Installments",
            "Shipment Value",
            "Discount Value",
            "Dealer",
            "Sellers",
            "Coupons",
            "Delivery Date",
            "Contract Start Date",
            "Cancelled At",
            "Finished At",
            "PDD at",
            "Early Purchase Date",
            "Status Default",
            "Contract Total Value Expected",
            "Installments Paid Value",
            "Order Total Paid",
            "Remaining Total",
            "Total Delay",
            "Total Extra Payment Value Paid",
            "Total Value Refunded",
            "Early Purchase Value"
        FROM {self.sync_config['athena_table']}
        """
        
        execution_id = self.execute_athena_query(query)
        if not execution_id:
            return None
        
        result = self.wait_for_query_completion(execution_id)
        if not result['success']:
            return None
        
        return self.get_athena_results(execution_id)
    
    def clear_postgres_table(self):
        """Limpar tabela PostgreSQL antes da sincronização"""
        try:
            conn = self.get_postgres_connection()
            cursor = conn.cursor()
            
            cursor.execute(f"TRUNCATE TABLE {self.sync_config['postgres_table']} RESTART IDENTITY")
            conn.commit()
            
            cursor.close()
            conn.close()
            
            logger.info(f"🗑️ Tabela {self.sync_config['postgres_table']} limpa")
            
        except Exception as e:
            logger.error(f"❌ Erro ao limpar tabela PostgreSQL: {e}")
            raise
    
    def insert_data_to_postgres(self, df: pd.DataFrame):
        """Inserir dados no PostgreSQL em lotes"""
        try:
            conn = self.get_postgres_connection()
            cursor = conn.cursor()
            
            # Preparar dados para inserção
            total_rows = len(df)
            logger.info(f"📥 Iniciando inserção de {total_rows} registros")
            
            # Processar em lotes
            for i in range(0, total_rows, self.sync_config['batch_size']):
                batch = df.iloc[i:i + self.sync_config['batch_size']]
                
                # Converter DataFrame para lista de tuplas
                values = []
                for _, row in batch.iterrows():
                    # Tratar valores None/NaN
                    row_values = []
                    for value in row:
                        if pd.isna(value) or value == '' or value == 'null':
                            row_values.append(None)
                        else:
                            row_values.append(value)
                    values.append(tuple(row_values))
                
                # Preparar SQL de inserção usando os nomes corretos das colunas
                placeholders = ','.join(['%s'] * len(df.columns))
                columns = ','.join([f'"{col}"' for col in df.columns])  # Escapar nomes com aspas
                
                insert_sql = f"""
                INSERT INTO {self.sync_config['postgres_table']} 
                ({columns}) VALUES ({placeholders})
                ON CONFLICT ("Order Code", "item_name") 
                DO UPDATE SET
                    "Date Order Created" = EXCLUDED."Date Order Created",
                    "Status" = EXCLUDED."Status",
                    "Customer Name" = EXCLUDED."Customer Name",
                    "Customer Email" = EXCLUDED."Customer Email",
                    "Customer Phone Number" = EXCLUDED."Customer Phone Number",
                    "customer_income" = EXCLUDED."customer_income",
                    "Shipping Address" = EXCLUDED."Shipping Address",
                    "Zip Code" = EXCLUDED."Zip Code",
                    "Serial Number" = EXCLUDED."Serial Number",
                    "IMEI 1" = EXCLUDED."IMEI 1",
                    "IMEI 2" = EXCLUDED."IMEI 2",
                    "TAC Expected" = EXCLUDED."TAC Expected",
                    "TAC Paid" = EXCLUDED."TAC Paid",
                    "Downpayment Paid" = EXCLUDED."Downpayment Paid",
                    "Taxes Percent" = EXCLUDED."Taxes Percent",
                    "Installments Value" = EXCLUDED."Installments Value",
                    "Taxes Value Installments" = EXCLUDED."Taxes Value Installments",
                    "Taxes Value Initial Payment" = EXCLUDED."Taxes Value Initial Payment",
                    "Total Installments" = EXCLUDED."Total Installments",
                    "Shipment Value" = EXCLUDED."Shipment Value",
                    "Discount Value" = EXCLUDED."Discount Value",
                    "Dealer" = EXCLUDED."Dealer",
                    "Sellers" = EXCLUDED."Sellers",
                    "Coupons" = EXCLUDED."Coupons",
                    "Delivery Date" = EXCLUDED."Delivery Date",
                    "Contract Start Date" = EXCLUDED."Contract Start Date",
                    "Cancelled At" = EXCLUDED."Cancelled At",
                    "Finished At" = EXCLUDED."Finished At",
                    "PDD at" = EXCLUDED."PDD at",
                    "Early Purchase Date" = EXCLUDED."Early Purchase Date",
                    "Status Default" = EXCLUDED."Status Default",
                    "Contract Total Value Expected" = EXCLUDED."Contract Total Value Expected",
                    "Installments Paid Value" = EXCLUDED."Installments Paid Value",
                    "Order Total Paid" = EXCLUDED."Order Total Paid",
                    "Remaining Total" = EXCLUDED."Remaining Total",
                    "Total Delay" = EXCLUDED."Total Delay",
                    "Total Extra Payment Value Paid" = EXCLUDED."Total Extra Payment Value Paid",
                    "Total Value Refunded" = EXCLUDED."Total Value Refunded",
                    "Early Purchase Value" = EXCLUDED."Early Purchase Value",
                    updated_at = CURRENT_TIMESTAMP
                """
                
                cursor.executemany(insert_sql, values)
                conn.commit()
                
                logger.info(f"✅ Lote {i//self.sync_config['batch_size'] + 1} inserido: {len(values)} registros")
            
            cursor.close()
            conn.close()
            
            logger.info(f"🎉 Sincronização concluída: {total_rows} registros processados")
            
        except Exception as e:
            logger.error(f"❌ Erro ao inserir dados no PostgreSQL: {e}")
            raise
    
    def perform_sync_with_retry(self):
        """Executar sincronização com sistema de retry"""
        max_retries = self.sync_config['max_retries']
        retry_delay = self.sync_config['retry_delay']
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🚀 Tentativa {attempt}/{max_retries} - Iniciando sincronização Athena -> PostgreSQL")
                
                success = self.perform_sync()
                
                if success:
                    if attempt > 1:
                        logger.info(f"✅ Sincronização bem-sucedida na tentativa {attempt}")
                    return True
                else:
                    raise Exception("Sincronização retornou False")
                    
            except Exception as e:
                logger.error(f"❌ Tentativa {attempt}/{max_retries} falhou: {e}")
                
                if attempt < max_retries:
                    logger.warning(f"⏳ Aguardando {retry_delay} segundos antes da próxima tentativa...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"💥 Todas as {max_retries} tentativas falharam!")
                    self.log_failure_details(str(e))
                    return False
        
        return False

    def create_sync_record(self) -> str:
        """Criar registro de controle da sincronização"""
        try:
            conn = self.get_postgres_connection()
            cursor = conn.cursor()
            
            sync_config = {
                'athena_table': self.sync_config['athena_table'],
                'postgres_table': self.sync_config['postgres_table'],
                'batch_size': self.sync_config['batch_size'],
                'max_retries': self.sync_config['max_retries']
            }
            
            # Obter horário atual em Miami (naive datetime para PostgreSQL TIMESTAMP)
            miami_tz = timezone('America/New_York')
            now_miami = datetime.now(miami_tz).replace(tzinfo=None)
            
            cursor.execute("""
                INSERT INTO data_sync_control 
                (sync_type, source_system, target_table, sync_started_at, batch_size, sync_config, sync_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                'order_report',
                'athena',
                self.sync_config['postgres_table'],
                now_miami,
                self.sync_config['batch_size'],
                json.dumps(sync_config),
                'running'
            ))
            
            sync_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            return str(sync_id)
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar registro de sincronização: {e}")
            return None

    def update_sync_record(self, sync_id: str, status: str, stats: dict, error_msg: str = None):
        """Atualizar registro de controle da sincronização"""
        try:
            conn = self.get_postgres_connection()
            cursor = conn.cursor()
            
            # Obter horário atual em Miami (naive datetime para PostgreSQL TIMESTAMP)
            miami_tz = timezone('America/New_York')
            now_miami = datetime.now(miami_tz).replace(tzinfo=None)
            
            update_data = {
                'sync_status': status,
                'sync_completed_at': now_miami,
                'records_processed': stats.get('processed', 0),
                'records_inserted': stats.get('inserted', 0),
                'records_updated': stats.get('updated', 0),
                'records_failed': stats.get('failed', 0),
                'execution_time_seconds': stats.get('execution_time', 0)
            }
            
            if status == 'completed':
                cursor.execute("""
                    UPDATE data_sync_control SET
                        sync_status = %s,
                        sync_completed_at = %s,
                        records_processed = %s,
                        records_inserted = %s,
                        records_updated = %s,
                        execution_time_seconds = %s,
                        success_message = %s
                    WHERE id = %s
                """, (
                    update_data['sync_status'],
                    update_data['sync_completed_at'],
                    update_data['records_processed'],
                    update_data['records_inserted'],
                    update_data['records_updated'],
                    update_data['execution_time_seconds'],
                    f"Sincronização concluída com sucesso - {stats.get('processed', 0)} registros processados",
                    sync_id
                ))
            else:
                cursor.execute("""
                    UPDATE data_sync_control SET
                        sync_status = %s,
                        sync_completed_at = %s,
                        error_message = %s,
                        retry_count = retry_count + 1
                    WHERE id = %s
                """, (
                    update_data['sync_status'],
                    update_data['sync_completed_at'],
                    error_msg,
                    sync_id
                ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar registro de sincronização: {e}")

    def perform_sync(self):
        """Executar sincronização completa"""
        start_time = time.time()
        sync_id = None
        
        try:
            # 0. Criar registro de controle
            sync_id = self.create_sync_record()
            if sync_id:
                logger.info(f"📝 Registro de sincronização criado: {sync_id}")
            
            # 1. Buscar dados do Athena
            logger.info("1️⃣ Buscando dados do Athena...")
            df = self.fetch_athena_data()
            
            if df is None or df.empty:
                logger.warning("⚠️ Nenhum dado encontrado no Athena")
                if sync_id:
                    self.update_sync_record(sync_id, 'completed', {'processed': 0}, 'Nenhum dado encontrado no Athena')
                return False
            
            # 2. Limpar tabela PostgreSQL
            logger.info("2️⃣ Limpando tabela PostgreSQL...")
            self.clear_postgres_table()
            
            # 3. Inserir dados no PostgreSQL
            logger.info("3️⃣ Inserindo dados no PostgreSQL...")
            self.insert_data_to_postgres(df)
            
            # 4. Atualizar registro de controle com sucesso
            elapsed_time = time.time() - start_time
            stats = {
                'processed': len(df),
                'inserted': len(df),
                'updated': 0,
                'failed': 0,
                'execution_time': elapsed_time
            }
            
            if sync_id:
                self.update_sync_record(sync_id, 'completed', stats)
            
            logger.info(f"✅ Sincronização concluída em {elapsed_time:.2f} segundos - {len(df)} registros")
            
            return True
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            if sync_id:
                stats = {'execution_time': elapsed_time}
                self.update_sync_record(sync_id, 'failed', stats, str(e))
            
            logger.error(f"❌ Erro na sincronização: {e}")
            raise  # Re-raise para o retry handler

    def log_failure_details(self, error_msg: str):
        """Registrar detalhes da falha para debug"""
        try:
            failure_log = {
                'timestamp': datetime.now().isoformat(),
                'error': error_msg,
                'config': {
                    'athena_table': self.sync_config['athena_table'],
                    'postgres_table': self.sync_config['postgres_table'],
                    'batch_size': self.sync_config['batch_size']
                },
                'aws_config': {
                    'region': self.aws_config['region'],
                    'database': self.aws_config['database'],
                    'output_location': self.aws_config['output_location']
                },
                'postgres_config': {
                    'host': self.postgres_config['host'],
                    'port': self.postgres_config['port'],
                    'database': self.postgres_config['database']
                }
            }
            
            # Salvar em arquivo de falhas
            failure_file = '/home/servidores/ezpocket/agents/data_sync_agent/sync_failures.log'
            with open(failure_file, 'a') as f:
                f.write(f"{datetime.now()}: {error_msg}\n")
                f.write(f"Config: {failure_log}\n")
                f.write("-" * 80 + "\n")
            
            logger.error(f"📁 Detalhes da falha salvos em: {failure_file}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar log de falha: {e}")


    def should_run_now(self) -> bool:
        """Verificar se deve executar agora baseado no schedule do .env"""
        try:
            schedule = os.getenv('DATA_SYNC_SCHEDULE', '0 2 * * *')
            now = datetime.now()
            
            # Parse do cron: "minuto hora dia mês dia_semana"
            parts = schedule.strip().split()
            if len(parts) != 5:
                logger.warning(f"⚠️ Schedule inválido: {schedule}, executando sempre")
                return True
            
            minute, hour, day, month, weekday = parts
            
            # Verificar minuto
            if minute != '*' and int(minute) != now.minute:
                return False
            
            # Verificar hora  
            if hour != '*' and int(hour) != now.hour:
                return False
            
            # Verificar dia do mês
            if day != '*' and int(day) != now.day:
                return False
            
            # Verificar mês
            if month != '*' and int(month) != now.month:
                return False
            
            # Verificar dia da semana (0=domingo no cron, mas datetime usa 0=segunda)
            if weekday != '*':
                cron_weekday = int(weekday)
                # Converter: domingo=0 no cron para domingo=6 no Python
                python_weekday = now.weekday()  # 0=segunda, 6=domingo
                if cron_weekday == 0:  # domingo no cron
                    cron_weekday = 7
                if cron_weekday - 1 != python_weekday:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar schedule: {e}")
            return False


def main():
    """Função principal - Executa só no horário agendado"""
    try:
        logger.info("🟢 Data Sync Agent iniciado (PM2 mode)")
        
        # Criar agente para verificar schedule
        agent = DataSyncAgent()
        
        # Verificar se deve executar agora
        if not agent.should_run_now():
            schedule = os.getenv('DATA_SYNC_SCHEDULE', '0 2 * * *')
            logger.info(f"⏰ Não está no horário agendado ({schedule}) - saindo sem executar")
            sys.exit(0)
        
        logger.info("✅ Horário correto - executando sincronização...")
        
        # Executar sincronização com retry
        success = agent.perform_sync_with_retry()
        
        if success:
            logger.info("✅ Sincronização concluída com sucesso - saindo")
            sys.exit(0)
        else:
            logger.error("❌ Sincronização falhou - saindo com erro")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()