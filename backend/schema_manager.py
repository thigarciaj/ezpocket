"""
Módulo de gerenciamento de schemas
Refatorado de ezinho.py para melhor organização
"""
import json
import os
import glob

class SchemaManager:
    """Gerencia schemas de tabelas do banco de dados"""
    
    def __init__(self, schemas_dir='schemas', instrucoes_dir='instrucoes'):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.schemas_dir = os.path.join(self.base_dir, '..', schemas_dir)
        self.instrucoes_dir = os.path.join(self.base_dir, '..', instrucoes_dir)
        self.schemas = self._carregar_schemas()
        self.instrucoes = self._carregar_instrucoes()
    
    def _carregar_schemas(self):
        """Carrega todos os schemas dinamicamente"""
        schemas = {}
        for path in glob.glob(os.path.join(self.schemas_dir, "*_schema.json")):
            nome_tabela = os.path.basename(path).replace("_schema.json", "")
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Suporte para arquivos com wrapper de tabela (antigo) ou só 'columns' (novo)
                if "columns" in data:
                    schemas[nome_tabela] = data["columns"]
                elif nome_tabela in data and "columns" in data[nome_tabela]:
                    schemas[nome_tabela] = data[nome_tabela]["columns"]
                else:
                    # Se houver apenas um campo no root, pega o primeiro
                    for k, v in data.items():
                        if isinstance(v, dict) and "columns" in v:
                            if k == nome_tabela:
                                schemas[nome_tabela] = v["columns"]
                            else:
                                schemas[k] = v["columns"]
                            break
                    else:
                        raise ValueError(f"Schema inválido para {nome_tabela}: {path}")
        return schemas
    
    def _carregar_instrucoes(self):
        """Carrega todas as instruções dinamicamente"""
        instrucoes = {}
        for path in glob.glob(os.path.join(self.instrucoes_dir, "*_instrucoes.json")):
            nome_tabela = os.path.basename(path).replace("_instrucoes.json", "")
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                instrucoes[nome_tabela] = data
        return instrucoes
    
    def get_schema(self, tabela):
        """Retorna o schema de uma tabela específica"""
        return self.schemas.get(tabela, {})
    
    def get_instrucoes(self, tabela):
        """Retorna as instruções de uma tabela específica"""
        return self.instrucoes.get(tabela, {})
    
    def formatar_schema_para_prompt(self, schema):
        """Formata schema para usar no prompt da IA"""
        linhas = []
        for nome, info in schema.items():
            descricao = info.get("description", "")
            tipo = info.get("type", "")
            linhas.append(f'- "{nome}" ({tipo}): {descricao}')
        return "\n".join(linhas)
    
    def formatar_schemas_para_prompt(self, schemas_dict):
        """Formata múltiplos schemas para usar no prompt da IA"""
        blocos = []
        for tabela, schema in schemas_dict.items():
            if not schema:
                continue
            linhas = [f'• {tabela}:']
            for nome, info in schema.items():
                descricao = info.get("description", "")
                tipo = info.get("type", "")
                linhas.append(f'  - "{nome}" ({tipo}): {descricao}')
            blocos.append("\n".join(linhas))
        return "\n\n".join(blocos)
    
    def identificar_tabela(self, pergunta):
        """Identifica qual tabela usar baseado na pergunta"""
        # Por enquanto retorna a tabela padrão
        # Pode ser expandido com lógica mais complexa
        return "report_orders"
