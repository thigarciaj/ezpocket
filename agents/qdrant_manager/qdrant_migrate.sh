#!/bin/bash
# =============================================================================
# EzPocket Qdrant Migration Script
# Automatiza migração e operações do Qdrant Vector Database
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project paths
PROJECT_DIR="/home/servidores/ezpocket"
VENV_PATH="$PROJECT_DIR/ezinho_assistente"

# Load environment variables
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a  # automatically export all variables
    source "$PROJECT_DIR/.env"
    set +a  # disable automatic export
fi

# Qdrant configuration
QDRANT_HOST=${QDRANT_HOST:-localhost}
QDRANT_PORT=${QDRANT_PORT:-6333}
QDRANT_API_KEY=${QDRANT_API_KEY:-qdrant_admin_2025}
QDRANT_HTTP_USER=${QDRANT_HTTP_USER:-admin}
QDRANT_HTTP_PASSWORD=${QDRANT_HTTP_PASSWORD:-admin123}

# Functions
print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${CYAN}🚀 EzPocket Qdrant Migration Script${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

print_step() {
    echo -e "${PURPLE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

check_dependencies() {
    print_step "Verificando dependências..."
    
    # Check if docker is running
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker não está rodando!"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_PATH" ]; then
        print_error "Virtual environment não encontrado: $VENV_PATH"
        exit 1
    fi
    
    print_success "Dependências verificadas"
}

start_qdrant() {
    print_step "Iniciando Qdrant..."
    cd "$PROJECT_DIR"
    
    if docker compose ps qdrant | grep -q "Up"; then
        print_warning "Qdrant já está rodando"
    else
        docker compose up -d qdrant qdrant-proxy
        sleep 5  # Wait for containers to start
        print_success "Qdrant iniciado"
    fi
}

stop_qdrant() {
    print_step "Parando Qdrant..."
    cd "$PROJECT_DIR"
    docker compose stop qdrant qdrant-proxy
    print_success "Qdrant parado"
}

check_qdrant_health() {
    print_step "Verificando saúde do Qdrant..."
    
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -u "$QDRANT_HTTP_USER:$QDRANT_HTTP_PASSWORD" -H "api-key: $QDRANT_API_KEY" "http://$QDRANT_HOST:$QDRANT_PORT/health" > /dev/null 2>&1; then
            print_success "Qdrant está saudável"
            return 0
        fi
        
        echo -e "${YELLOW}Tentativa $attempt/$max_attempts...${NC}"
        sleep 2
        ((attempt++))
    done
    
    print_error "Qdrant não está respondendo"
    return 1
}

run_migration() {
    print_step "Executando migração completa..."
    cd "$PROJECT_DIR"
    source "$VENV_PATH/bin/activate"
    
    python agents/qdrant_manager/migrate_roles.py
    
    if [ $? -eq 0 ]; then
        print_success "Migração concluída com sucesso!"
    else
        print_error "Migração falhou!"
        exit 1
    fi
}

test_queries() {
    print_step "Testando consultas no Qdrant..."
    cd "$PROJECT_DIR"
    source "$VENV_PATH/bin/activate"
    
    # Create a simple test if it doesn't exist
    if [ ! -f "test_qdrant_simple.py" ]; then
        cat > test_qdrant_simple.py << 'EOF'
from agents.qdrant_manager.qdrant_manager import QdrantRoleManager
import requests
from requests.auth import HTTPBasicAuth

def test_qdrant():
    print("🔍 Testando conexão com Qdrant...")
    
    # Test HTTP connection
    try:
        import os
        auth = HTTPBasicAuth(os.getenv('QDRANT_HTTP_USER', 'admin'), os.getenv('QDRANT_HTTP_PASSWORD', 'admin123'))
        headers = {'api-key': os.getenv('QDRANT_API_KEY', 'qdrant_admin_2025')}
        
        qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
        qdrant_port = os.getenv('QDRANT_PORT', '6333')
        response = requests.get(f'http://{qdrant_host}:{qdrant_port}/collections', auth=auth, headers=headers)
        if response.status_code == 200:
            collections = response.json()
            print(f"✅ Conexão OK - {len(collections['result']['collections'])} collections encontradas")
            
            for collection in collections['result']['collections']:
                name = collection['name']
                count = collection.get('points_count', 0)
                print(f"   📁 {name}: {count} pontos")
        else:
            print(f"❌ Erro na conexão: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    test_qdrant()
EOF
    fi
    
    python test_qdrant_simple.py
}

show_status() {
    print_step "Status do sistema..."
    
    # Docker containers status
    echo -e "${CYAN}Docker Containers:${NC}"
    docker compose ps qdrant qdrant-proxy
    
    echo
    
    # Test connection
    test_queries
}

reset_collections() {
    print_warning "Esta operação irá DELETAR todas as collections e dados!"
    read -p "Tem certeza? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        print_step "Resetando collections..."
        cd "$PROJECT_DIR"
        source "$VENV_PATH/bin/activate"
        
        python -c "
from agents.qdrant_manager.qdrant_manager import QdrantRoleManager
import requests
from requests.auth import HTTPBasicAuth

import os
auth = HTTPBasicAuth(os.getenv('QDRANT_HTTP_USER', 'admin'), os.getenv('QDRANT_HTTP_PASSWORD', 'admin123'))
headers = {'api-key': os.getenv('QDRANT_API_KEY', 'qdrant_admin_2025')}

# Get all collections
qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
qdrant_port = os.getenv('QDRANT_PORT', '6333')
response = requests.get(f'http://{qdrant_host}:{qdrant_port}/collections', auth=auth, headers=headers)
collections = response.json()['result']['collections']

for collection in collections:
    name = collection['name']
    print(f'Deletando collection: {name}')
    requests.delete(f'http://{qdrant_host}:{qdrant_port}/collections/{name}', auth=auth, headers=headers)

print('✅ Todas as collections foram deletadas')
"
        print_success "Reset concluído"
    else
        print_warning "Operação cancelada"
    fi
}

manage_users() {
    print_step "Gerenciamento de usuários HTTP..."
    
    local htpasswd_file="$PROJECT_DIR/qdrant-htpasswd"
    
    echo -e "${CYAN}Escolha uma opção:${NC}"
    echo "1. Listar usuários existentes"
    echo "2. Adicionar novo usuário" 
    echo "3. Remover usuário"
    echo "4. Alterar senha"
    echo "5. Recriar arquivo (CUIDADO!)"
    echo "0. Voltar"
    
    read -p "Digite a opção (0-5): " option
    
    case $option in
        1)
            print_step "Usuários existentes:"
            if [ -f "$htpasswd_file" ]; then
                cut -d':' -f1 "$htpasswd_file" | while read user; do
                    echo -e "   👤 $user"
                done
            else
                print_warning "Arquivo qdrant-htpasswd não encontrado"
            fi
            ;;
        2)
            read -p "Nome do usuário: " username
            read -s -p "Senha: " password
            echo
            
            # Usar Docker para gerar htpasswd
            docker run --rm httpd:2.4-alpine htpasswd -nbB "$username" "$password" >> "$htpasswd_file"
            print_success "Usuário '$username' adicionado"
            ;;
        3)
            read -p "Usuário a remover: " username
            if [ -f "$htpasswd_file" ]; then
                grep -v "^$username:" "$htpasswd_file" > "${htpasswd_file}.tmp" && mv "${htpasswd_file}.tmp" "$htpasswd_file"
                print_success "Usuário '$username' removido"
            fi
            ;;
        4)
            read -p "Usuário para alterar senha: " username
            read -s -p "Nova senha: " password
            echo
            
            # Remover usuário antigo e adicionar novo
            grep -v "^$username:" "$htpasswd_file" > "${htpasswd_file}.tmp"
            docker run --rm httpd:2.4-alpine htpasswd -nbB "$username" "$password" >> "${htpasswd_file}.tmp"
            mv "${htpasswd_file}.tmp" "$htpasswd_file"
            print_success "Senha do usuário '$username' alterada"
            ;;
        5)
            print_warning "Esta operação irá DELETAR todos os usuários!"
            read -p "Tem certeza? (yes/no): " confirm
            if [ "$confirm" = "yes" ]; then
                read -p "Nome do primeiro usuário: " username
                read -s -p "Senha: " password
                echo
                
                docker run --rm httpd:2.4-alpine htpasswd -cbB "$htpasswd_file" "$username" "$password"
                print_success "Arquivo recriado com usuário '$username'"
            fi
            ;;
        0)
            return
            ;;
        *)
            print_error "Opção inválida"
            ;;
    esac
}

show_web_access() {
    print_step "Informações de acesso web..."
    
    echo -e "${CYAN}🌐 Acesso Web:${NC}"
    echo -e "   Dashboard: http://$QDRANT_HOST:$QDRANT_PORT/dashboard"
    echo -e "   Usuário: $QDRANT_HTTP_USER"
    echo -e "   Senha: $QDRANT_HTTP_PASSWORD"
    echo
    echo -e "${YELLOW}🔐 Para fazer logout:${NC}"
    echo -e "   1. Acesse: http://$QDRANT_HOST:$QDRANT_PORT/logout-page"
    echo -e "   2. Ou feche completamente o navegador"
    echo -e "   3. Ou limpe dados de navegação"
    echo
    echo -e "${PURPLE}💡 Dicas de Segurança:${NC}"
    echo -e "   - Sempre faça logout em computadores compartilhados"
    echo -e "   - Use navegação privada/incógnita quando possível"
    echo -e "   - Mude as credenciais padrão no .env"
    echo
    echo -e "${BLUE}👥 Usuários cadastrados:${NC}"
    if [ -f "$PROJECT_DIR/qdrant-htpasswd" ]; then
        cut -d':' -f1 "$PROJECT_DIR/qdrant-htpasswd" | while read user; do
            echo -e "   👤 $user"
        done
    else
        echo -e "   ⚠️  Arquivo qdrant-htpasswd não encontrado"
    fi
}

show_help() {
    echo -e "${CYAN}Uso: $0 [COMANDO]${NC}"
    echo
    echo "Comandos disponíveis:"
    echo "  start       - Inicia o Qdrant"
    echo "  stop        - Para o Qdrant"  
    echo "  migrate     - Executa migração completa"
    echo "  test        - Testa consultas no Qdrant"
    echo "  status      - Mostra status do sistema"
    echo "  web         - Mostra informações de acesso web"
    echo "  users       - Gerencia usuários HTTP (adicionar/remover)"
    echo "  reset       - Reseta todas as collections (CUIDADO!)"
    echo "  full        - Executa sequência completa (start + migrate + test)"
    echo "  help        - Mostra esta ajuda"
    echo
    echo "Exemplos:"
    echo "  $0 full     - Setup completo"
    echo "  $0 migrate  - Apenas migração"
    echo "  $0 web      - Ver como acessar e fazer logout"
}

# Main script logic
main() {
    print_header
    
    case "${1:-help}" in
        "start")
            check_dependencies
            start_qdrant
            check_qdrant_health
            ;;
        "stop")
            stop_qdrant
            ;;
        "migrate")
            check_dependencies
            start_qdrant
            check_qdrant_health
            run_migration
            ;;
        "test")
            check_qdrant_health
            test_queries
            ;;
        "status")
            show_status
            ;;
        "web")
            show_web_access
            ;;
        "users")
            manage_users
            ;;
        "reset")
            check_qdrant_health
            reset_collections
            ;;
        "full")
            check_dependencies
            start_qdrant
            check_qdrant_health
            run_migration
            test_queries
            print_success "Setup completo finalizado!"
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"