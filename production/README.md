# EZPOCKET - Production Docker Setup

Sistema multi-agente de análise de dados com LangGraph, WebSocket, Redis e PostgreSQL.

## 🏗️ Arquitetura

- **Orchestrator**: Graph Orchestrator + WebSocket Server (porta 5555)
- **Workers**: 13 agentes especializados processando jobs via Redis
- **Redis**: Fila de jobs e cache (porta 6493)
- **PostgreSQL**: Logs, histórico e preferências (porta 5546)
- **Keycloak**: Autenticação OAuth2/OIDC (porta 8180)

## 📋 Pré-requisitos

- Docker Engine 20.10+
- Docker Compose 2.0+
- Arquivo `.env` configurado na raiz do projeto

## 🚀 Início Rápido

### 1. Configurar variáveis de ambiente

Copie `.env.example` para `.env` e configure:

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# AWS Athena
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
ATHENA_DATABASE=ezpocket_analytics
ATHENA_OUTPUT_LOCATION=s3://...

# PostgreSQL
POSTGRES_DB=ezpocket_logs
POSTGRES_USER=ezpocket_user
POSTGRES_PASSWORD=ezpocket_pass_2025
POSTGRES_PORT=5546

# Redis
REDIS_PORT=6493

# Keycloak
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin
KEYCLOAK_PORT=8180
KEYCLOAK_HOSTNAME=localhost
KEYCLOAK_REALM=ezpocket
KEYCLOAK_CLIENT_ID=ezpocket-client
KEYCLOAK_CLIENT_SECRET=...

# Frontend
FRONTEND_MODE=production
```

### 2. Build e Start

```bash
# Build de todas as imagens
docker-compose -f production/docker-compose.yml build

# Subir todos os serviços
docker-compose -f production/docker-compose.yml up -d

# Ver logs em tempo real
docker-compose -f production/docker-compose.yml logs -f

# Ver logs de um serviço específico
docker-compose -f production/docker-compose.yml logs -f orchestrator
docker-compose -f production/docker-compose.yml logs -f worker-intent-validator
```

### 3. Verificar Status

```bash
# Status de todos os containers
docker-compose -f production/docker-compose.yml ps

# Health check do orchestrator
curl http://localhost:5555/health

# Conectar no Redis
docker exec -it ezpocket-redis redis-cli -p 6379

# Conectar no PostgreSQL
docker exec -it ezpocket-postgres psql -U ezpocket_user -d ezpocket_logs
```

### 4. Acessar Aplicação

- **Dashboard**: http://localhost:5555
- **Keycloak Admin**: http://localhost:8180/admin (admin/admin)
- **Redis**: localhost:6493
- **PostgreSQL**: localhost:5546

## 🔧 Comandos Úteis

### Gerenciamento

```bash
# Parar todos os serviços
docker-compose -f production/docker-compose.yml down

# Parar e remover volumes (⚠️ apaga dados!)
docker-compose -f production/docker-compose.yml down -v

# Reiniciar serviço específico
docker-compose -f production/docker-compose.yml restart orchestrator
docker-compose -f production/docker-compose.yml restart worker-plan-builder

# Rebuild sem cache
docker-compose -f production/docker-compose.yml build --no-cache
```

### Scaling Workers

```bash
# Escalar workers para processar mais jobs
docker-compose -f production/docker-compose.yml up -d --scale worker-plan-builder=3
docker-compose -f production/docker-compose.yml up -d --scale worker-athena-executor=2
docker-compose -f production/docker-compose.yml up -d --scale worker-python-runtime=2
```

### Debug

```bash
# Entrar no container do orchestrator
docker exec -it ezpocket-orchestrator bash

# Entrar em um worker específico
docker exec -it ezpocket-worker-intent-validator bash

# Ver logs de erro apenas
docker-compose -f production/docker-compose.yml logs | grep -i error

# Ver uso de recursos
docker stats
```

### Limpeza

```bash
# Remover containers parados
docker container prune

# Remover imagens não utilizadas
docker image prune -a

# Remover volumes não utilizados
docker volume prune

# Limpeza completa (⚠️ cuidado!)
docker system prune -a --volumes
```

## 📊 Workers Disponíveis

| Worker                  | Função                       | Recursos        |
| ----------------------- | ---------------------------- | --------------- |
| `intent-validator`      | Valida intenção do usuário   | 512MB, 0.5 CPU  |
| `plan-builder`          | Cria plano de análise        | 512MB, 0.5 CPU  |
| `plan-confirm`          | Aguarda confirmação          | 256MB, 0.25 CPU |
| `user-proposed-plan`    | Aceita plano do usuário      | 256MB, 0.25 CPU |
| `plan-refiner`          | Refina plano proposto        | 512MB, 0.5 CPU  |
| `analysis-orchestrator` | Orquestra análise SQL/Python | 512MB, 0.5 CPU  |
| `sql-validator`         | Valida SQL antes de executar | 512MB, 0.5 CPU  |
| `athena-executor`       | Executa queries no Athena    | 1GB, 1.0 CPU    |
| `auto-correction`       | Corrige erros SQL            | 512MB, 0.5 CPU  |
| `python-runtime`        | Executa código Python        | 2GB, 1.5 CPU    |
| `response-composer`     | Compõe resposta natural      | 512MB, 0.5 CPU  |
| `user-feedback`         | Processa avaliação           | 512MB, 0.5 CPU  |
| `history-preferences`   | Carrega contexto histórico   | 512MB, 0.5 CPU  |

## 🔒 Segurança

- **Secrets**: Nunca commitar `.env` no Git
- **Keycloak**: Alterar senha padrão admin/admin
- **PostgreSQL**: Usar senha forte em produção
- **Redis**: Adicionar senha em produção
- **Network**: Usar network isolada (já configurada)

## 🐛 Troubleshooting

### Containers não iniciam

```bash
# Ver erro detalhado
docker-compose -f production/docker-compose.yml logs

# Reconstruir imagens
docker-compose -f production/docker-compose.yml build --no-cache
docker-compose -f production/docker-compose.yml up -d
```

### Worker não processa jobs

```bash
# Verificar se Redis está rodando
docker exec -it ezpocket-redis redis-cli ping

# Ver jobs pendentes no Redis
docker exec -it ezpocket-redis redis-cli KEYS "rq:job:*"

# Reiniciar worker específico
docker-compose -f production/docker-compose.yml restart worker-plan-builder
```

### PostgreSQL não conecta

```bash
# Verificar se está rodando
docker exec -it ezpocket-postgres pg_isready

# Ver logs de erro
docker-compose -f production/docker-compose.yml logs postgres

# Resetar banco (⚠️ apaga dados!)
docker-compose -f production/docker-compose.yml down -v
docker-compose -f production/docker-compose.yml up -d postgres
```

### Keycloak não inicia

```bash
# Verificar se PostgreSQL está pronto
docker-compose -f production/docker-compose.yml logs postgres | grep "ready"

# Aguardar health check (pode demorar 30-60s)
docker-compose -f production/docker-compose.yml ps keycloak

# Ver logs completos
docker-compose -f production/docker-compose.yml logs keycloak
```

## 📈 Monitoramento

### Redis

```bash
# Ver informações do Redis
docker exec -it ezpocket-redis redis-cli INFO

# Monitorar comandos em tempo real
docker exec -it ezpocket-redis redis-cli MONITOR

# Ver jobs por status
docker exec -it ezpocket-redis redis-cli KEYS "rq:queue:*"
```

### PostgreSQL

```bash
# Ver conexões ativas
docker exec -it ezpocket-postgres psql -U ezpocket_user -d ezpocket_logs -c "SELECT * FROM pg_stat_activity;"

# Ver tamanho das tabelas
docker exec -it ezpocket-postgres psql -U ezpocket_user -d ezpocket_logs -c "SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC;"
```

### Workers

```bash
# Ver CPU e memória de cada worker
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Ver logs de todos os workers
docker-compose -f production/docker-compose.yml logs -f | grep worker-
```

## 🚢 Deploy em Produção

### AWS ECS/Fargate

```bash
# Build e push para ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

docker tag ezpocket-orchestrator:latest <account>.dkr.ecr.us-east-1.amazonaws.com/ezpocket-orchestrator:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/ezpocket-orchestrator:latest
```

### Docker Swarm

```bash
# Inicializar Swarm
docker swarm init

# Deploy stack
docker stack deploy -c production/docker-compose.yml ezpocket

# Ver serviços
docker service ls

# Escalar workers
docker service scale ezpocket_worker-plan-builder=3
```

### Kubernetes

```bash
# Converter docker-compose para K8s (usando kompose)
kompose convert -f production/docker-compose.yml

# Aplicar manifests
kubectl apply -f .
```

## 📝 Notas

- **Health Checks**: Todos os serviços têm health checks configurados
- **Restart Policy**: `unless-stopped` - reinicia automaticamente exceto se parado manualmente
- **Volumes**: Dados persistidos em volumes Docker nomeados
- **Network**: Todos os containers na mesma rede `ezpocket-network`
- **Resource Limits**: Workers têm limites de CPU/memória para evitar sobrecarga

## 📧 Suporte

Para problemas ou dúvidas, abra uma issue no repositório.
