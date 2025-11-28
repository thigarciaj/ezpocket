"""
Qdrant Manager - Gerencia roles e regras no Qdrant Vector Database
Organiza por módulo e tipo de regras para substituir roles.json
"""

import json
import os
import uuid
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import Distance, VectorParams
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print(f"⚠️  Dependências não instaladas: {e}")
    print("Execute: pip install qdrant-client sentence-transformers")

@dataclass
class RoleConfig:
    """Configuração de uma role/regra"""
    module_name: str
    role_type: str  # system, user, assistant, validation, etc.
    role_name: str
    content: str
    metadata: Dict[str, Any]
    created_at: str = None
    version: str = "1.0"

class QdrantRoleManager:
    """Gerenciador de roles no Qdrant"""
    
    def __init__(self, 
                 qdrant_host: str = None, 
                 qdrant_port: int = None,
                 api_key: str = None,
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Inicializa o gerenciador do Qdrant
        
        Args:
            qdrant_host: Host do Qdrant
            qdrant_port: Porta do Qdrant
            api_key: API key para autenticação  
            embedding_model: Modelo de embedding para vetorização
        """
        # Carregar configurações do .env
        qdrant_host = qdrant_host or os.getenv('QDRANT_HOST', 'localhost')
        qdrant_port = qdrant_port or int(os.getenv('QDRANT_PORT', '6333'))
        http_user = os.getenv('QDRANT_HTTP_USER', 'admin')
        http_password = os.getenv('QDRANT_HTTP_PASSWORD', 'admin123')
        if not api_key:
            api_key = os.getenv('QDRANT_API_KEY', 'qdrant_admin_2025')
        
        # Usar requests diretamente para contornar proxy nginx
        import requests
        from requests.auth import HTTPBasicAuth
        
        self.api_key = api_key
        self.base_url = f"http://{qdrant_host}:{qdrant_port}"
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(http_user, http_password)
        self.session.headers.update({'api-key': api_key})
        
        # Cliente Qdrant será None, usaremos requests diretamente
        self.client = None
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Configurações das collections
        self.collections = {
            "intent_validator_roles": "Roles para validação de intents",
            "plan_builder_roles": "Roles para construção de planos",
            "plan_confirm_roles": "Roles para confirmação de planos", 
            "user_proposed_plan_roles": "Roles para planos propostos pelo usuário",
            "analysis_orchestrator_roles": "Roles para orquestração de análises",
            "sql_validator_roles": "Roles para validação SQL",
            "auto_correction_roles": "Roles para correção automática",
            "athena_executor_roles": "Roles para execução Athena",
            "python_runtime_roles": "Roles para runtime Python",
            "response_composer_roles": "Roles para composição de respostas",
            "user_feedback_roles": "Roles para feedback do usuário",
            "plan_refiner_roles": "Roles para refinamento de planos",
            "system_roles": "Roles gerais do sistema"
        }
        
        self._setup_collections()
    
    def _setup_collections(self):
        """Configura as collections no Qdrant"""
        print("🔧 Configurando collections do Qdrant...")
        
        for collection_name, description in self.collections.items():
            try:
                # Verifica se a collection já existe
                response = self.session.get(f"{self.base_url}/collections")
                if response.status_code == 200:
                    collections_data = response.json()
                    existing_collections = [c['name'] for c in collections_data['result']['collections']]
                    
                    if collection_name not in existing_collections:
                        # Cria a collection
                        collection_config = {
                            "vectors": {
                                "size": 384,  # Tamanho do modelo all-MiniLM-L6-v2
                                "distance": "Cosine"
                            }
                        }
                        
                        create_response = self.session.put(
                            f"{self.base_url}/collections/{collection_name}",
                            json=collection_config
                        )
                        
                        if create_response.status_code == 200:
                            print(f"  ✅ Collection '{collection_name}' criada")
                        else:
                            print(f"  ❌ Erro ao criar collection '{collection_name}': {create_response.text}")
                    else:
                        print(f"  ℹ️  Collection '{collection_name}' já existe")
                else:
                    print(f"  ❌ Erro ao listar collections: {response.text}")
                    
            except Exception as e:
                print(f"  ❌ Erro ao criar collection '{collection_name}': {e}")
    
    def _get_collection_name(self, module_name: str) -> str:
        """Retorna o nome da collection baseado no módulo"""
        collection_name = f"{module_name.lower()}_roles"
        if collection_name in self.collections:
            return collection_name
        return "system_roles"  # Fallback para collection genérica
    
    def _vectorize_content(self, content: str) -> List[float]:
        """Converte texto em vetor usando sentence transformers"""
        try:
            embedding = self.embedding_model.encode(content)
            return embedding.tolist()
        except Exception as e:
            print(f"❌ Erro ao vetorizar conteúdo: {e}")
            return [0.0] * 384  # Retorna vetor zero em caso de erro
    
    def add_role(self, role_config: RoleConfig) -> str:
        """
        Adiciona uma nova role no Qdrant
        
        Args:
            role_config: Configuração da role
            
        Returns:
            ID da role inserida
        """
        try:
            collection_name = self._get_collection_name(role_config.module_name)
            
            # Gerar embedding do conteúdo
            vector = self._vectorize_content(role_config.content)
            
            # Preparar metadados
            payload = {
                "module_name": role_config.module_name,
                "role_type": role_config.role_type,
                "role_name": role_config.role_name,
                "content": role_config.content,
                "metadata": role_config.metadata,
                "created_at": role_config.created_at or datetime.now().isoformat(),
                "version": role_config.version
            }
            
            # Inserir no Qdrant via API REST
            point_id = str(uuid.uuid4())
            
            point_data = {
                "points": [{
                    "id": point_id,
                    "vector": vector,
                    "payload": payload
                }]
            }
            
            response = self.session.put(
                f"{self.base_url}/collections/{collection_name}/points",
                json=point_data
            )
            
            if response.status_code == 200:
                print(f"✅ Role '{role_config.role_name}' adicionada ao módulo '{role_config.module_name}'")
                return point_id
            else:
                print(f"❌ Erro HTTP {response.status_code}: {response.text}")
                return None
            
        except Exception as e:
            print(f"❌ Erro ao adicionar role: {e}")
            return None
    
    def get_role(self, module_name: str, role_type: str, role_name: str) -> Optional[Dict]:
        """
        Busca uma role específica
        
        Args:
            module_name: Nome do módulo
            role_type: Tipo da role
            role_name: Nome da role
            
        Returns:
            Dados da role ou None se não encontrada
        """
        try:
            collection_name = self._get_collection_name(module_name)
            
            # Buscar com filtros exatos
            search_result = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="module_name",
                            match=models.MatchValue(value=module_name)
                        ),
                        models.FieldCondition(
                            key="role_type", 
                            match=models.MatchValue(value=role_type)
                        ),
                        models.FieldCondition(
                            key="role_name",
                            match=models.MatchValue(value=role_name)
                        )
                    ]
                ),
                limit=1
            )
            
            if search_result[0]:  # Se encontrou resultados
                point = search_result[0][0]
                return point.payload
            
            return None
            
        except Exception as e:
            print(f"❌ Erro ao buscar role: {e}")
            return None
    
    def get_roles_by_module(self, module_name: str, role_type: str = None) -> List[Dict]:
        """
        Busca todas as roles de um módulo
        
        Args:
            module_name: Nome do módulo
            role_type: Filtro opcional por tipo de role
            
        Returns:
            Lista de roles do módulo
        """
        try:
            collection_name = self._get_collection_name(module_name)
            
            # Construir filtros
            filters = [
                models.FieldCondition(
                    key="module_name",
                    match=models.MatchValue(value=module_name)
                )
            ]
            
            if role_type:
                filters.append(
                    models.FieldCondition(
                        key="role_type",
                        match=models.MatchValue(value=role_type)
                    )
                )
            
            # Buscar roles
            search_result = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(must=filters),
                limit=100  # Limite máximo de roles por módulo
            )
            
            roles = []
            for point in search_result[0]:
                roles.append(point.payload)
            
            print(f"📋 Encontradas {len(roles)} roles para módulo '{module_name}'")
            return roles
            
        except Exception as e:
            print(f"❌ Erro ao buscar roles do módulo: {e}")
            return []
    
    def search_similar_roles(self, query_text: str, module_name: str = None, limit: int = 5) -> List[Dict]:
        """
        Busca roles similares usando busca vetorial
        
        Args:
            query_text: Texto de consulta
            module_name: Filtro opcional por módulo
            limit: Número máximo de resultados
            
        Returns:
            Lista de roles similares com scores
        """
        try:
            # Vetorizar a query
            query_vector = self._vectorize_content(query_text)
            
            # Definir collection a buscar
            if module_name:
                collections_to_search = [self._get_collection_name(module_name)]
            else:
                collections_to_search = list(self.collections.keys())
            
            all_results = []
            
            for collection_name in collections_to_search:
                try:
                    # Buscar similares
                    search_results = self.client.search(
                        collection_name=collection_name,
                        query_vector=query_vector,
                        limit=limit,
                        with_payload=True,
                        with_vectors=False
                    )
                    
                    for result in search_results:
                        all_results.append({
                            "role_data": result.payload,
                            "similarity_score": result.score,
                            "collection": collection_name
                        })
                        
                except Exception as e:
                    # Collection pode não existir ainda
                    continue
            
            # Ordenar por score de similaridade
            all_results.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            return all_results[:limit]
            
        except Exception as e:
            print(f"❌ Erro na busca por similaridade: {e}")
            return []
    
    def update_role(self, module_name: str, role_type: str, role_name: str, new_content: str, new_metadata: Dict = None) -> bool:
        """
        Atualiza uma role existente
        
        Args:
            module_name: Nome do módulo
            role_type: Tipo da role
            role_name: Nome da role
            new_content: Novo conteúdo
            new_metadata: Novos metadados (opcional)
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            # Buscar a role existente primeiro
            existing_role = self.get_role(module_name, role_type, role_name)
            if not existing_role:
                print(f"❌ Role '{role_name}' não encontrada")
                return False
            
            # Criar nova configuração
            updated_role = RoleConfig(
                module_name=module_name,
                role_type=role_type,
                role_name=role_name,
                content=new_content,
                metadata=new_metadata or existing_role.get("metadata", {}),
                version=str(float(existing_role.get("version", "1.0")) + 0.1)
            )
            
            # Adicionar como nova versão (Qdrant não tem update direto)
            self.add_role(updated_role)
            
            print(f"✅ Role '{role_name}' atualizada")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao atualizar role: {e}")
            return False
    
    def migrate_from_json(self, json_file_path: str, module_name: str) -> bool:
        """
        Migra roles de um arquivo JSON para o Qdrant
        
        Args:
            json_file_path: Caminho para o arquivo JSON
            module_name: Nome do módulo
            
        Returns:
            True se migração foi bem-sucedida
        """
        try:
            if not os.path.exists(json_file_path):
                print(f"❌ Arquivo não encontrado: {json_file_path}")
                return False
            
            with open(json_file_path, 'r', encoding='utf-8') as f:
                roles_data = json.load(f)
            
            migrated_count = 0
            
            # Processar cada role do JSON
            for role_key, role_content in roles_data.items():
                try:
                    # Determinar tipo da role baseado na key
                    role_type = "system"  # Padrão
                    if "system" in role_key.lower():
                        role_type = "system"
                    elif "user" in role_key.lower():
                        role_type = "user"
                    elif "assistant" in role_key.lower():
                        role_type = "assistant"
                    elif "validation" in role_key.lower():
                        role_type = "validation"
                    
                    # Criar configuração da role
                    role_config = RoleConfig(
                        module_name=module_name,
                        role_type=role_type,
                        role_name=role_key,
                        content=role_content,
                        metadata={
                            "migrated_from": json_file_path,
                            "original_key": role_key,
                            "migration_date": datetime.now().isoformat()
                        }
                    )
                    
                    # Adicionar no Qdrant
                    result = self.add_role(role_config)
                    if result:
                        migrated_count += 1
                        
                except Exception as e:
                    print(f"⚠️  Erro ao migrar role '{role_key}': {e}")
                    continue
            
            print(f"✅ Migração concluída: {migrated_count} roles migradas do arquivo '{json_file_path}'")
            return True
            
        except Exception as e:
            print(f"❌ Erro na migração: {e}")
            return False
    
    def export_module_roles(self, module_name: str, output_file: str) -> bool:
        """
        Exporta roles de um módulo para arquivo JSON (backup)
        
        Args:
            module_name: Nome do módulo
            output_file: Arquivo de saída
            
        Returns:
            True se export foi bem-sucedido
        """
        try:
            roles = self.get_roles_by_module(module_name)
            
            export_data = {
                "module_name": module_name,
                "export_date": datetime.now().isoformat(),
                "total_roles": len(roles),
                "roles": roles
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Export concluído: {len(roles)} roles exportadas para '{output_file}'")
            return True
            
        except Exception as e:
            print(f"❌ Erro no export: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do Qdrant"""
        try:
            stats = {}
            
            for collection_name in self.collections.keys():
                try:
                    info = self.client.get_collection(collection_name)
                    stats[collection_name] = {
                        "points_count": info.points_count,
                        "vectors_count": info.vectors_count,
                        "status": info.status
                    }
                except:
                    stats[collection_name] = {"status": "not_created"}
            
            return stats
            
        except Exception as e:
            print(f"❌ Erro ao obter estatísticas: {e}")
            return {}

if __name__ == "__main__":
    # Teste básico
    try:
        manager = QdrantRoleManager()
        print("🎯 QdrantRoleManager inicializado com sucesso!")
        
        # Exibir estatísticas
        stats = manager.get_stats()
        print(f"📊 Estatísticas: {json.dumps(stats, indent=2)}")
        
    except Exception as e:
        print(f"❌ Erro na inicialização: {e}")