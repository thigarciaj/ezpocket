""" 
POC EZINHO
Autor: Thiago Garcia João, EZBRAIN
Usuário ⇄ Assistente Python ⇄ LangChain + OpenAI ⇄ Athena via Boto3 + Glue Catalog
"""
import boto3
import os
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

# Ler credenciais e região do ambiente
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_REGION = os.getenv("AWS_REGION")

# Inicializar cliente Glue com as credenciais do .env
glue = boto3.client(
    "glue",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

# Listar bancos de dados
def listar_bancos():
    response = glue.get_databases()
    return [db["Name"] for db in response["DatabaseList"]]

# Listar tabelas de um banco
def listar_tabelas(banco):
    response = glue.get_tables(DatabaseName=banco)
    return [t["Name"] for t in response["TableList"]]

# Listar colunas de uma tabela
def listar_colunas(banco, tabela):
    response = glue.get_table(DatabaseName=banco, Name=tabela)
    colunas = response["Table"]["StorageDescriptor"]["Columns"]
    return [(c["Name"], c["Type"]) for c in colunas]

# Teste
if __name__ == "__main__":
    print("📚 Bancos disponíveis:")
    bancos = listar_bancos()
    for b in bancos:
        print(f"- {b}")

    banco_exemplo = bancos[0]
    print(f"\n📄 Tabelas em '{banco_exemplo}':")
    tabelas = listar_tabelas(banco_exemplo)
    for t in tabelas:
        print(f"- {t}")

    tabela_exemplo = tabelas[0]
    print(f"\n📌 Colunas da tabela '{tabela_exemplo}':")
    colunas = listar_colunas(banco_exemplo, tabela_exemplo)
    for nome, tipo in colunas:
        print(f"  - {nome} ({tipo})")
