#!/bin/bash

# Script para rodar o endpoint de teste do SQL Validator Agent
# Uso: ./run_test.sh [modo]
# Modos: server, interactive, tests, unit

set -e

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Diretórios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EZPOKET_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
# BACKEND_DIR removido - usando EZPOKET_DIR diretamente
VENV_DIR="$EZPOKET_DIR/ezinho_assistente"

echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}🔍 SQL VALIDATOR TEST RUNNER${NC}"
echo -e "${BLUE}================================================================================${NC}"

# Verifica se venv existe
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}❌ Erro: Virtual environment não encontrado em $VENV_DIR${NC}"
    exit 1
fi

# Ativa venv
echo -e "${YELLOW}📦 Ativando virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Vai para o diretório raiz do projeto
cd "$EZPOKET_DIR"

# Verifica modo
MODE="${1:-help}"

case "$MODE" in
    server)
        echo -e "${GREEN}🚀 Iniciando servidor de teste na porta 5014...${NC}"
        echo -e "${YELLOW}Pressione Ctrl+C para parar o servidor${NC}"
        echo ""
        python agents/sql_validator_agent/test_endpoint.py
        ;;
    
    interactive|i)
        echo -e "${GREEN}🔍 Iniciando modo interativo...${NC}"
        echo ""
        python agents/sql_validator_agent/test_client.py
        ;;
    
    tests|t)
        echo -e "${GREEN}🧪 Executando bateria de testes...${NC}"
        echo ""
        python agents/sql_validator_agent/test_client.py tests
        ;;
    
    unit|u)
        echo -e "${GREEN}🧪 Executando testes unitários...${NC}"
        echo ""
        python agents/sql_validator_agent/test_sql_validator.py
        ;;
    
    help|h|*)
        echo ""
        echo -e "${YELLOW}Uso: ./run_test.sh [modo]${NC}"
        echo ""
        echo "Modos disponíveis:"
        echo -e "  ${GREEN}server${NC}       - Inicia servidor Flask de teste (porta 5014)"
        echo -e "  ${GREEN}interactive${NC}  - Modo interativo para validar queries"
        echo -e "  ${GREEN}tests${NC}        - Executa bateria de testes automáticos"
        echo -e "  ${GREEN}unit${NC}         - Executa testes unitários"
        echo -e "  ${GREEN}help${NC}         - Mostra esta mensagem"
        echo ""
        echo "Exemplos:"
        echo -e "  ${BLUE}./run_test.sh server${NC}       # Terminal 1: Inicia servidor"
        echo -e "  ${BLUE}./run_test.sh interactive${NC}  # Terminal 2: Modo interativo"
        echo -e "  ${BLUE}./run_test.sh tests${NC}        # Bateria de testes"
        echo -e "  ${BLUE}./run_test.sh unit${NC}         # Testes unitários"
        echo ""
        exit 0
        ;;
esac
