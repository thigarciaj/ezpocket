#!/bin/bash

# Script para rodar o endpoint de teste do Graph Orchestrator
# Uso: ./run_test.sh [modo]
# Modos: server, interactive, examples, test

set -e

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Diretórios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EZPOKET_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BACKEND_DIR="$EZPOKET_DIR/backend"
VENV_DIR="$EZPOKET_DIR/ezinho_assistente"

echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}🔄 GRAPH ORCHESTRATOR TEST RUNNER${NC}"
echo -e "${BLUE}================================================================================${NC}"

# Verifica se venv existe
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}❌ Erro: Virtual environment não encontrado em $VENV_DIR${NC}"
    exit 1
fi

# Ativa venv
echo -e "${YELLOW}📦 Ativando virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Vai para o diretório backend
cd "$BACKEND_DIR"

# Verifica modo
MODE="${1:-help}"

case "$MODE" in
    server)
        echo -e "${GREEN}🚀 Iniciando servidor de teste na porta 5008...${NC}"
        echo -e "${YELLOW}Pressione Ctrl+C para parar o servidor${NC}"
        echo ""
        python agents/graph_orchestrator/test_endpoint.py
        ;;
    
    interactive|i)
        echo -e "${GREEN}🎮 Iniciando modo interativo...${NC}"
        echo ""
        source "$VENV_DIR/bin/activate"
        cd "$BACKEND_DIR"
        python agents/graph_orchestrator/test_client.py interactive
        ;;
    
    examples|ex)
        echo -e "${GREEN}📚 Executando todos os exemplos...${NC}"
        echo ""
        source "$VENV_DIR/bin/activate"
        cd "$BACKEND_DIR"
        python agents/graph_orchestrator/test_client.py run-examples
        ;;
    
    test)
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Erro: Especifique uma pergunta${NC}"
            echo -e "${YELLOW}Uso: ./run_test.sh test \"<pergunta>\" [username] [projeto]${NC}"
            exit 1
        fi
        
        source "$VENV_DIR/bin/activate"
        cd "$BACKEND_DIR"
        
        PERGUNTA="$2"
        USERNAME="${3:-test_user}"
        PROJETO="${4:-test_project}"
        
        echo -e "${GREEN}🔍 Testando pergunta...${NC}"
        echo ""
        python agents/graph_orchestrator/test_client.py test "$PERGUNTA" "$USERNAME" "$PROJETO"
        ;;
    
    health|h)
        echo -e "${GREEN}🏥 Verificando health do servidor...${NC}"
        echo ""
        source "$VENV_DIR/bin/activate"
        cd "$BACKEND_DIR"
        python agents/graph_orchestrator/test_client.py health
        ;;
    
    help|*)
        echo ""
        echo -e "${GREEN}Uso: ./run_test.sh [modo] [argumentos]${NC}"
        echo ""
        echo -e "${YELLOW}Modos disponíveis:${NC}"
        echo ""
        echo -e "  ${BLUE}server${NC}           - Inicia o servidor de teste (porta 5008)"
        echo -e "  ${BLUE}interactive, i${NC}   - Modo interativo (digite perguntas em tempo real)"
        echo -e "  ${BLUE}examples, ex${NC}     - Executa todos os exemplos automaticamente"
        echo -e "  ${BLUE}test${NC}             - Testa uma pergunta específica"
        echo -e "  ${BLUE}health, h${NC}        - Verifica se o servidor está rodando"
        echo -e "  ${BLUE}help${NC}             - Mostra esta ajuda"
        echo ""
        echo -e "${YELLOW}Exemplos:${NC}"
        echo ""
        echo -e "  ${GREEN}# Iniciar servidor (Terminal 1)${NC}"
        echo -e "  ./run_test.sh server"
        echo ""
        echo -e "  ${GREEN}# Modo interativo (Terminal 2, após servidor iniciar)${NC}"
        echo -e "  ./run_test.sh interactive"
        echo ""
        echo -e "  ${GREEN}# Executar exemplos${NC}"
        echo -e "  ./run_test.sh examples"
        echo ""
        echo -e "  ${GREEN}# Testar pergunta específica${NC}"
        echo -e "  ./run_test.sh test \"Quantos pedidos temos?\""
        echo -e "  ./run_test.sh test \"Mostre relatório\" joao ezpag"
        echo ""
        echo -e "  ${GREEN}# Health check${NC}"
        echo -e "  ./run_test.sh health"
        echo ""
        echo -e "${BLUE}================================================================================${NC}"
        ;;
esac

