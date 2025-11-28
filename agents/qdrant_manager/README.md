# Qdrant Manager - Vector Database para Roles

Este módulo gerencia as roles do sistema usando Qdrant Vector Database, substituindo os arquivos `roles.json` estáticos.

## Configuração

Todas as configurações estão no arquivo `.env` na raiz do projeto:

```bash
# Qdrant Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_API_KEY=qdrant_admin_2025
QDRANT_HTTP_USER=admin
QDRANT_HTTP_PASSWORD=admin123
```

## Uso Rápido

### Script de Migração (Recomendado)

```bash
# Executar setup completo
./qdrant_migrate.sh full

# Ver status
./qdrant_migrate.sh status

# Apenas migrar roles
./qdrant_migrate.sh migrate

# Resetar tudo (cuidado!)
./qdrant_migrate.sh reset
```

### Comandos Manuais

```bash
# Iniciar Qdrant
docker compose up -d qdrant qdrant-proxy

# Executar migração
python migrate_roles.py

# Testar conexão
python test_qdrant_query.py
```

## Estrutura

- **qdrant_manager.py** - Core do sistema de vector database
- **migrate_roles.py** - Script de migração dos roles.json 
- **compatibility.py** - Camada de compatibilidade para agents existentes
- **qdrant_migrate.sh** - Script bash para operações automatizadas

## Collections Criadas

O sistema cria uma collection para cada módulo:
- `intent_validator_roles`
- `plan_builder_roles`
- `auto_correction_roles`
- `sql_validator_roles`
- `python_runtime_roles`
- `response_composer_roles`
- E mais...

## Migração de Servidor

Para mover para outro servidor:

1. **Copie o projeto inteiro**
2. **Configure o .env com IPs/portas corretos**
3. **Execute a migração:**
   ```bash
   ./qdrant_migrate.sh full
   ```

Todas as variáveis estão no `.env` - basta ajustar para o novo ambiente!

## Interface Web

Após iniciar: http://localhost:6333/dashboard
- **Usuário:** admin
- **Senha:** admin123

## Integração com Dashboard

O Qdrant aparece automaticamente no menu do EZPocket para usuários com a role `qdrant_admin` no Keycloak.

### Configuração da Role:

```bash
# Configurar role qdrant_admin no Keycloak
./qdrant_migrate.sh keycloak
```

### Como Funciona:

1. **Role-Based Access:** Apenas usuários com role `qdrant_admin` veem o item "🔍 Qdrant DB" no menu
2. **Acesso Integrado:** Clique no menu abre modal com informações e link direto
3. **Logout Seguro:** Página de logout personalizada em `/logout-page`

### Atribuir Role a Usuário:

1. Acesse Keycloak Admin: `http://localhost:8090/auth/admin/`
2. Vá em: **Users** > **[usuário]** > **Role Mappings**
3. Adicione role: `qdrant_admin`

## Troubleshooting

- **Erro de conexão:** Verifique se o Docker está rodando
- **Erro de autenticação:** Confirme as credenciais no .env
- **Collections vazias:** Execute `./qdrant_migrate.sh migrate`
- **Menu não aparece:** Verifique se o usuário tem role `qdrant_admin`
- **Reset completo:** Execute `./qdrant_migrate.sh reset && ./qdrant_migrate.sh migrate`