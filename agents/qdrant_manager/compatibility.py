
"""
Camada de Compatibilidade Qdrant - Substitui carregamento de roles.json
Mantém a interface atual enquanto busca dados no Qdrant
"""

import os
import json
from typing import Dict, Optional
from agents.qdrant_manager.qdrant_manager import QdrantRoleManager

class QdrantRolesAdapter:
    """Adapter que mantém compatibilidade com código existente"""
    
    def __init__(self):
        self._qdrant_manager = None
        self._cache = {}
    
    def get_qdrant_manager(self):
        """Lazy loading do QdrantRoleManager"""
        if self._qdrant_manager is None:
            try:
                self._qdrant_manager = QdrantRoleManager()
            except Exception as e:
                print(f"⚠️  Fallback para JSON: Erro ao conectar Qdrant: {e}")
                return None
        return self._qdrant_manager
    
    def load_roles(self, module_name: str, fallback_json_path: str = None) -> Dict:
        """
        Carrega roles do Qdrant com fallback para JSON
        
        Args:
            module_name: Nome do módulo (ex: 'intent_validator')
            fallback_json_path: Caminho para JSON de fallback
            
        Returns:
            Dict com roles do módulo
        """
        cache_key = f"{module_name}_roles"
        
        # Verificar cache primeiro
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        roles_dict = {}
        
        # Tentar carregar do Qdrant primeiro
        qdrant_manager = self.get_qdrant_manager()
        if qdrant_manager:
            try:
                roles_list = qdrant_manager.get_roles_by_module(module_name)
                
                # Converter lista de roles para dict (compatibilidade)
                for role in roles_list:
                    role_name = role.get('role_name', 'unknown')
                    role_content = role.get('content', '')
                    roles_dict[role_name] = role_content
                
                if roles_dict:
                    print(f"✅ Roles do '{module_name}' carregadas do Qdrant ({len(roles_dict)} roles)")
                    self._cache[cache_key] = roles_dict
                    return roles_dict
                
            except Exception as e:
                print(f"⚠️  Erro ao carregar do Qdrant: {e}")
        
        # Fallback para JSON se Qdrant falhar
        if fallback_json_path and os.path.exists(fallback_json_path):
            try:
                with open(fallback_json_path, 'r', encoding='utf-8') as f:
                    roles_dict = json.load(f)
                
                print(f"⚠️  Fallback: Roles do '{module_name}' carregadas do JSON ({len(roles_dict)} roles)")
                self._cache[cache_key] = roles_dict
                return roles_dict
                
            except Exception as e:
                print(f"❌ Erro ao carregar JSON fallback: {e}")
        
        print(f"❌ Nenhuma role encontrada para módulo '{module_name}'")
        return {}
    
    def get_role(self, module_name: str, role_type: str, role_name: str, fallback_json_path: str = None) -> Optional[str]:
        """
        Busca uma role específica
        
        Args:
            module_name: Nome do módulo
            role_type: Tipo da role
            role_name: Nome da role
            fallback_json_path: Caminho para JSON de fallback
            
        Returns:
            Conteúdo da role ou None
        """
        # Tentar busca direta no Qdrant primeiro
        qdrant_manager = self.get_qdrant_manager()
        if qdrant_manager:
            try:
                role_data = qdrant_manager.get_role(module_name, role_type, role_name)
                if role_data and role_data.get('content'):
                    return role_data['content']
            except Exception as e:
                print(f"⚠️  Erro na busca direta: {e}")
        
        # Fallback para carregamento completo
        roles = self.load_roles(module_name, fallback_json_path)
        return roles.get(role_name)
    
    def search_similar_roles(self, query: str, module_name: str = None, limit: int = 3) -> list:
        """
        Busca roles similares (nova funcionalidade)
        
        Args:
            query: Texto de busca
            module_name: Filtro por módulo (opcional)
            limit: Número máximo de resultados
            
        Returns:
            Lista de roles similares
        """
        qdrant_manager = self.get_qdrant_manager()
        if qdrant_manager:
            try:
                return qdrant_manager.search_similar_roles(query, module_name, limit)
            except Exception as e:
                print(f"❌ Erro na busca por similaridade: {e}")
        
        return []

# Instância global para uso nos agentes
qdrant_adapter = QdrantRolesAdapter()

def load_roles_qdrant(module_name: str, fallback_json_path: str = None) -> Dict:
    """Função utilitária para substituir carregamentos de JSON"""
    return qdrant_adapter.load_roles(module_name, fallback_json_path)

def get_role_qdrant(module_name: str, role_type: str, role_name: str, fallback_json_path: str = None) -> Optional[str]:
    """Função utilitária para busca de role específica"""
    return qdrant_adapter.get_role(module_name, role_type, role_name, fallback_json_path)
