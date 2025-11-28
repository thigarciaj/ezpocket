#!/usr/bin/env python3
"""
Script de Migração - Transfere todas as roles.json para Qdrant
Executa a migração completa mantendo a compatibilidade com o fluxo atual
"""

import os
import sys
import json
import time
import uuid
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, '/home/servidores/ezpocket')

from agents.qdrant_manager.qdrant_manager import QdrantRoleManager, RoleConfig

class RolesMigrator:
    """Migrador de roles JSON para Qdrant"""
    
    def __init__(self):
        self.base_path = Path('/home/servidores/ezpocket/agents')
        self.qdrant_manager = None
        self.migration_report = []
        
    def initialize_qdrant(self):
        """Inicializa conexão com Qdrant"""
        try:
            print("🔌 Conectando ao Qdrant...")
            qdrant_host = os.getenv('QDRANT_HOST', 'qdrant')
            qdrant_port = int(os.getenv('QDRANT_PORT', '6333'))
            api_key = os.getenv('QDRANT_API_KEY', 'qdrant_admin_2025')
            
            self.qdrant_manager = QdrantRoleManager(
                qdrant_host=qdrant_host,
                qdrant_port=qdrant_port,
                api_key=api_key
            )
            print("✅ Conexão com Qdrant estabelecida")
            return True
        except Exception as e:
            print(f"❌ Erro ao conectar com Qdrant: {e}")
            print("💡 Certifique-se que o Docker com Qdrant está rodando")
            return False
    
    def find_roles_files(self) -> list:
        """Encontra todos os arquivos roles.json"""
        roles_files = []
        
        for agent_dir in self.base_path.iterdir():
            if agent_dir.is_dir() and agent_dir.name.endswith('_agent'):
                roles_file = agent_dir / 'roles.json'
                if roles_file.exists():
                    roles_files.append({
                        'file_path': str(roles_file),
                        'module_name': agent_dir.name.replace('_agent', ''),
                        'agent_dir': str(agent_dir)
                    })
        
        print(f"📋 Encontrados {len(roles_files)} arquivos roles.json")
        return roles_files
    
    def migrate_single_module(self, file_info: dict) -> dict:
        """Migra um único módulo"""
        result = {
            'module': file_info['module_name'],
            'file_path': file_info['file_path'],
            'success': False,
            'roles_count': 0,
            'errors': []
        }
        
        try:
            print(f"\n🔄 Migrando módulo: {file_info['module_name']}")
            print(f"   📁 Arquivo: {file_info['file_path']}")
            
            # Ler arquivo JSON
            with open(file_info['file_path'], 'r', encoding='utf-8') as f:
                roles_data = json.load(f)
            
            print(f"   📖 Carregadas {len(roles_data)} roles")
            
            # Migrar cada role
            migrated_count = 0
            for role_key, role_content in roles_data.items():
                try:
                    # Determinar tipo da role baseado na estrutura/nome
                    role_type = self._determine_role_type(role_key, role_content)
                    
                    # Criar configuração da role
                    role_config = RoleConfig(
                        module_name=file_info['module_name'],
                        role_type=role_type,
                        role_name=role_key,
                        content=str(role_content),  # Garantir que seja string
                        metadata={
                            'migrated_from': file_info['file_path'],
                            'original_key': role_key,
                            'migration_timestamp': time.time(),
                            'agent_directory': file_info['agent_dir']
                        }
                    )
                    
                    # Adicionar no Qdrant
                    point_id = self.qdrant_manager.add_role(role_config)
                    if point_id:
                        migrated_count += 1
                        print(f"     ✅ Role '{role_key}' → {role_type}")
                    else:
                        result['errors'].append(f"Falha ao inserir role '{role_key}'")
                        
                except Exception as e:
                    error_msg = f"Erro ao processar role '{role_key}': {e}"
                    result['errors'].append(error_msg)
                    print(f"     ❌ {error_msg}")
                    continue
            
            result['roles_count'] = migrated_count
            result['success'] = migrated_count > 0
            
            if result['success']:
                print(f"   ✅ Migração concluída: {migrated_count}/{len(roles_data)} roles")
            else:
                print(f"   ❌ Migração falhou")
                
        except Exception as e:
            error_msg = f"Erro ao migrar módulo {file_info['module_name']}: {e}"
            result['errors'].append(error_msg)
            print(f"   ❌ {error_msg}")
        
        return result
    
    def _determine_role_type(self, role_key: str, role_content) -> str:
        """Determina o tipo da role baseado no contexto"""
        key_lower = role_key.lower()
        
        # Tipos baseados no nome da key
        if 'system' in key_lower:
            return 'system'
        elif 'user' in key_lower:
            return 'user'
        elif 'assistant' in key_lower:
            return 'assistant'
        elif 'validation' in key_lower or 'validator' in key_lower:
            return 'validation'
        elif 'prompt' in key_lower:
            return 'prompt'
        elif 'template' in key_lower:
            return 'template'
        elif 'instruction' in key_lower:
            return 'instruction'
        elif 'example' in key_lower:
            return 'example'
        
        # Análise do conteúdo se for string
        if isinstance(role_content, str):
            content_lower = role_content.lower()
            if content_lower.startswith('você é') or content_lower.startswith('you are'):
                return 'system'
            elif 'exemplo' in content_lower or 'example' in content_lower:
                return 'example'
            elif 'validar' in content_lower or 'validate' in content_lower:
                return 'validation'
        
        return 'system'  # Padrão
    
    def create_compatibility_layer(self):
        """Cria camada de compatibilidade para manter o fluxo atual"""
        compatibility_code = '''
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
'''
        
        # Salvar camada de compatibilidade
        compatibility_path = '/home/servidores/ezpocket/agents/qdrant_manager/compatibility.py'
        with open(compatibility_path, 'w', encoding='utf-8') as f:
            f.write(compatibility_code)
        
        print(f"✅ Camada de compatibilidade criada em: {compatibility_path}")
    
    def run_migration(self):
        """Executa migração completa"""
        print("🚀 Iniciando migração completa de roles.json para Qdrant")
        print("=" * 60)
        
        # Inicializar Qdrant
        if not self.initialize_qdrant():
            return False
        
        # Encontrar arquivos
        roles_files = self.find_roles_files()
        if not roles_files:
            print("❌ Nenhum arquivo roles.json encontrado")
            return False
        
        # Migrar cada módulo
        total_roles = 0
        successful_modules = 0
        
        for file_info in roles_files:
            result = self.migrate_single_module(file_info)
            self.migration_report.append(result)
            
            if result['success']:
                successful_modules += 1
                total_roles += result['roles_count']
        
        # Criar camada de compatibilidade
        self.create_compatibility_layer()
        
        # Relatório final
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO DE MIGRAÇÃO")
        print("=" * 60)
        print(f"📁 Módulos processados: {len(roles_files)}")
        print(f"✅ Módulos migrados: {successful_modules}")
        print(f"🔢 Total de roles migradas: {total_roles}")
        
        if successful_modules < len(roles_files):
            print(f"⚠️  Módulos com erro: {len(roles_files) - successful_modules}")
        
        # Detalhes por módulo
        print("\n📋 Detalhes por módulo:")
        for result in self.migration_report:
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {result['module']}: {result['roles_count']} roles")
            
            if result['errors']:
                for error in result['errors']:
                    print(f"     ⚠️  {error}")
        
        # Verificar estatísticas do Qdrant
        print(f"\n📊 Estatísticas do Qdrant:")
        stats = self.qdrant_manager.get_stats()
        for collection, stat in stats.items():
            if stat.get('points_count', 0) > 0:
                print(f"  📦 {collection}: {stat['points_count']} roles")
        
        print(f"\n✅ Migração concluída! Qdrant está pronto para uso.")
        return True

if __name__ == "__main__":
    migrator = RolesMigrator()
    success = migrator.run_migration()
    
    if success:
        print(f"\n🎉 Migração bem-sucedida!")
        print(f"💡 Para testar: docker-compose logs qdrant")
        qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
        qdrant_port = os.getenv('QDRANT_PORT', '6333')
        print(f"💡 Interface web: http://{qdrant_host}:{qdrant_port}/dashboard")
    else:
        print(f"\n❌ Migração falhou!")
        sys.exit(1)