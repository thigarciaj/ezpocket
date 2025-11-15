#!/bin/bash

# Script para rodar o endpoint de teste do Plan Refiner Agent
# Uso: ./run_test.sh [modo]
# Modos: server, interactive

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
echo -e "${BLUE}🔧 PLAN REFINER TEST RUNNER${NC}"
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
        echo -e "${GREEN}🚀 Iniciando servidor de teste na porta 5013...${NC}"
        echo -e "${YELLOW}Pressione Ctrl+C para parar o servidor${NC}"
        echo ""
        python agents/plan_refiner_agent/test_endpoint.py
        ;;
    
    interactive|i)
        echo -e "${GREEN}🔧 Modo interativo - Digite seus refinamentos${NC}"
        echo ""
        python agents/plan_refiner_agent/test_client.py interactive
        ;;
    
    help|h|*)
        echo -e "${YELLOW}Modos disponíveis:${NC}"
        echo ""
        echo -e "  ${GREEN}server${NC}        - Inicia servidor Flask na porta 5013"
        echo -e "  ${GREEN}interactive${NC}   - Modo interativo para testar refinamentos"
        echo ""
        echo -e "${YELLOW}Exemplos de uso:${NC}"
        echo -e "  ./run_test.sh server"
        echo -e "  ./run_test.sh interactive"
        echo ""
        ;;
esac

echo -e "${BLUE}================================================================================${NC}"
