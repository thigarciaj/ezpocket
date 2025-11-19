#!/bin/bash

# Script para rodar o endpoint de teste do Auto Correction Agent
# Uso: ./run_test.sh [modo]
# Modos: server, interactive, tests

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
echo -e "${BLUE}🔧 AUTO CORRECTION TEST RUNNER${NC}"
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
        echo -e "${GREEN}🚀 Iniciando servidor de teste na porta 5015...${NC}"
        echo -e "${YELLOW}Pressione Ctrl+C para parar o servidor${NC}"
        echo ""
        python agents/auto_correction_agent/test_endpoint.py
        ;;
    
    interactive|i)
        echo -e "${GREEN}🔧 Iniciando modo interativo...${NC}"
        echo ""
        python agents/auto_correction_agent/test_client.py
        ;;
    
    tests|t)
        echo -e "${GREEN}🧪 Executando bateria de testes...${NC}"
        echo ""
        python agents/auto_correction_agent/test_client.py tests
        ;;
    
    help|h|*)
        echo ""
        echo -e "${YELLOW}Uso: ./run_test.sh [modo]${NC}"
        echo ""
        echo "Modos disponíveis:"
        echo -e "  ${GREEN}server${NC}       - Inicia servidor Flask de teste (porta 5015)"
        echo -e "  ${GREEN}interactive${NC}  - Modo interativo para corrigir queries"
        echo -e "  ${GREEN}tests${NC}        - Executa bateria de testes automáticos"
        echo -e "  ${GREEN}help${NC}         - Mostra esta mensagem"
        echo ""
        echo "Exemplos:"
        echo -e "  ${BLUE}./run_test.sh server${NC}       # Terminal 1: Inicia servidor"
        echo -e "  ${BLUE}./run_test.sh interactive${NC}  # Terminal 2: Modo interativo"
        echo -e "  ${BLUE}./run_test.sh tests${NC}        # Bateria de testes"
        echo ""
        exit 0
        ;;
esac
