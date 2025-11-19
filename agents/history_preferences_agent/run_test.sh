#!/bin/bash

# run_test.sh - Script de automação para testar History and Preferences Agent
# Autor: AI Assistant
# Versão: 1.0.0

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configurações
PORT=5002
ENDPOINT_SCRIPT="test_endpoint.py"
CLIENT_SCRIPT="test_client.py"

# Função para imprimir cabeçalho
print_header() {
    echo -e "\n${BOLD}${CYAN}================================================================================${NC}"
    echo -e "${BOLD}${CYAN}$1${NC}"
    echo -e "${BOLD}${CYAN}================================================================================${NC}\n"
}

# Função para imprimir sucesso
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Função para imprimir erro
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Função para imprimir info
print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Função para imprimir aviso
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Função para verificar se o servidor está rodando
check_server() {
    if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Modo: server - Inicia o servidor de teste
mode_server() {
    print_header "🧠 INICIANDO SERVIDOR DE TESTE - HISTORY AND PREFERENCES AGENT"
    
    if check_server; then
        print_warning "Servidor já está rodando na porta $PORT"
        print_info "Para parar: pkill -f $ENDPOINT_SCRIPT"
        exit 1
    fi
    
    # Determina caminhos
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    EZPOKET_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
    # BACKEND_DIR removido - usando EZPOKET_DIR diretamente
    VENV_DIR="$EZPOKET_DIR/ezinho_assistente"
    
    # Ativa virtualenv
    if [ -d "$VENV_DIR" ]; then
        print_info "Ativando virtualenv..."
        source "$VENV_DIR/bin/activate"
    fi
    
    # Vai para o diretório raiz do projeto
    cd "$EZPOKET_DIR"
    
    print_info "Iniciando servidor na porta $PORT..."
    python agents/history_preferences_agent/$ENDPOINT_SCRIPT
}

# Modo: health - Verifica se servidor está rodando
mode_health() {
    print_header "🏥 VERIFICANDO HEALTH DO SERVIDOR"
    
    if check_server; then
        print_success "Servidor está rodando!"
        echo ""
        curl -s http://localhost:$PORT/health | python3 -m json.tool
    else
        print_error "Servidor não está rodando"
        print_info "Inicie o servidor com: ./run_test.sh server"
        exit 1
    fi
}

# Modo: interactive - Modo interativo
mode_interactive() {
    print_header "🧠 MODO INTERATIVO - HISTORY AND PREFERENCES AGENT"
    
    if ! check_server; then
        print_error "Servidor não está rodando!"
        print_info "Inicie o servidor em outro terminal: ./run_test.sh server"
        exit 1
    fi
    
    python3 $CLIENT_SCRIPT interactive
}

# Modo: examples - Executa exemplos predefinidos
mode_examples() {
    print_header "📚 EXECUTANDO EXEMPLOS - HISTORY AND PREFERENCES AGENT"
    
    if ! check_server; then
        print_error "Servidor não está rodando!"
        print_info "Inicie o servidor em outro terminal: ./run_test.sh server"
        exit 1
    fi
    
    # Exemplo 1: Salvar primeira interação
    print_header "Exemplo 1: Salvar Primeira Interação"
    python3 $CLIENT_SCRIPT save "joao_silva" "ezpag" "Quantos pedidos tivemos hoje?" "quantidade"
    sleep 2
    
    # Exemplo 2: Salvar segunda interação
    print_header "Exemplo 2: Salvar Segunda Interação"
    python3 $CLIENT_SCRIPT save "joao_silva" "ezpag" "Quais os pilares da EzPag?" "conhecimentos_gerais"
    sleep 2
    
    # Exemplo 3: Carregar contexto
    print_header "Exemplo 3: Carregar Contexto do Usuário"
    python3 $CLIENT_SCRIPT load "joao_silva" "ezpag" "Nova pergunta aqui"
    sleep 2
    
    # Exemplo 4: Ver histórico
    print_header "Exemplo 4: Ver Histórico do Usuário"
    python3 $CLIENT_SCRIPT history "joao_silva" "ezpag" 5
    sleep 2
    
    # Exemplo 5: Ver preferências
    print_header "Exemplo 5: Ver Preferências do Usuário"
    python3 $CLIENT_SCRIPT preferences "joao_silva" "ezpag"
    
    print_success "\n✓ Todos os exemplos executados com sucesso!"
}

# Modo: test - Testa uma query específica
mode_test() {
    if [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
        print_error "Uso: ./run_test.sh test <username> <projeto> <pergunta> [categoria]"
        exit 1
    fi
    
    USERNAME=$2
    PROJETO=$3
    PERGUNTA=$4
    CATEGORIA=${5:-"quantidade"}
    
    print_header "🧪 TESTE INDIVIDUAL - HISTORY AND PREFERENCES AGENT"
    
    if ! check_server; then
        print_error "Servidor não está rodando!"
        print_info "Inicie o servidor em outro terminal: ./run_test.sh server"
        exit 1
    fi
    
    print_info "Salvando interação..."
    python3 $CLIENT_SCRIPT save "$USERNAME" "$PROJETO" "$PERGUNTA" "$CATEGORIA"
    
    echo ""
    print_info "Carregando contexto..."
    python3 $CLIENT_SCRIPT load "$USERNAME" "$PROJETO"
}

# Modo: clean - Limpa banco de dados (cuidado!)
mode_clean() {
    print_header "🗑️  LIMPANDO BANCO DE DADOS"
    
    DB_PATH="../../../backend/database/user_context.db"
    
    if [ -f "$DB_PATH" ]; then
        print_warning "Isso irá DELETAR todos os dados de histórico e preferências!"
        read -p "Tem certeza? (sim/não): " confirm
        
        if [ "$confirm" == "sim" ]; then
            rm "$DB_PATH"
            print_success "Banco de dados removido!"
            print_info "Será recriado automaticamente no próximo uso"
        else
            print_info "Operação cancelada"
        fi
    else
        print_info "Banco de dados não existe"
    fi
}

# Menu de ajuda
show_help() {
    echo -e "${BOLD}${CYAN}
╔══════════════════════════════════════════════════════════════════════════════╗
║                   HISTORY AND PREFERENCES AGENT - TEST SUITE                 ║
╚══════════════════════════════════════════════════════════════════════════════╝${NC}

${BOLD}Uso:${NC}
    ./run_test.sh <modo> [argumentos]

${BOLD}Modos Disponíveis:${NC}

    ${GREEN}server${NC}
        Inicia o servidor de teste na porta $PORT
        Exemplo: ./run_test.sh server

    ${GREEN}health${NC}
        Verifica se o servidor está rodando
        Exemplo: ./run_test.sh health

    ${GREEN}interactive${NC}
        Modo interativo para testar manualmente
        Exemplo: ./run_test.sh interactive

    ${GREEN}examples${NC}
        Executa 5 exemplos predefinidos
        Exemplo: ./run_test.sh examples

    ${GREEN}test${NC} <username> <projeto> <pergunta> [categoria]
        Testa uma query específica
        Exemplo: ./run_test.sh test joao_silva ezpag \"Quantos pedidos?\" quantidade

    ${GREEN}clean${NC}
        Remove o banco de dados (cuidado!)
        Exemplo: ./run_test.sh clean

${BOLD}Workflow Recomendado:${NC}

    ${CYAN}Terminal 1:${NC} ./run_test.sh server
    ${CYAN}Terminal 2:${NC} ./run_test.sh interactive
    
    ${YELLOW}ou${NC}
    
    ${CYAN}Terminal 1:${NC} ./run_test.sh server
    ${CYAN}Terminal 2:${NC} ./run_test.sh examples

${BOLD}Dicas:${NC}

    • Use ${CYAN}health${NC} para verificar se servidor está ok
    • Use ${CYAN}examples${NC} para popular o banco com dados de teste
    • Use ${CYAN}interactive${NC} para testar diferentes cenários
    • Use ${CYAN}clean${NC} se precisar resetar tudo

${BOLD}Porta do Servidor:${NC} $PORT
${BOLD}Scripts:${NC} $ENDPOINT_SCRIPT, $CLIENT_SCRIPT
"
}

# Main
case "$1" in
    server)
        mode_server
        ;;
    health)
        mode_health
        ;;
    interactive)
        mode_interactive
        ;;
    examples)
        mode_examples
        ;;
    test)
        mode_test "$@"
        ;;
    clean)
        mode_clean
        ;;
    *)
        show_help
        exit 1
        ;;
esac
