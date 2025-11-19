#!/bin/bash

# Script para testar o Athena Executor Agent
# Oferece 2 modos:
# 1. Servidor Flask (test_endpoint.py) - para testes via HTTP
# 2. Cliente Interativo (test_client.py) - para testes via terminal

set -e

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Diretórios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EZPOKET_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
# BACKEND_DIR removido - usando EZPOKET_DIR diretamente
VENV_DIR="$EZPOKET_DIR/ezinho_assistente"

echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}🚨 ATHENA EXECUTOR TEST RUNNER${NC}"
echo -e "${BLUE}================================================================================${NC}"

# Verifica se venv existe
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}❌ Erro: Virtual environment não encontrado em $VENV_DIR${NC}"
    exit 1
fi

# Ativa venv
echo -e "${YELLOW}📦 Ativando virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Carrega variáveis de ambiente
if [ -f "$EZPOKET_DIR/config/.env" ]; then
    export $(grep -v '^#' "$EZPOKET_DIR/config/.env" | xargs)
fi

# Vai para o diretório raiz do projeto (para imports funcionarem)
cd "$EZPOKET_DIR"

# Menu de opções
echo -e "${GREEN}Escolha o modo de teste:${NC}"
echo -e "  ${YELLOW}1)${NC} Servidor Flask (HTTP API)"
echo -e "  ${YELLOW}2)${NC} Cliente Interativo (Terminal)"
echo -e "  ${YELLOW}3)${NC} Teste Rápido (Standalone)"
echo ""
read -p "Digite sua escolha (1, 2 ou 3): " choice

case $choice in
    1)
        echo -e "${YELLOW}🚀 Iniciando servidor de teste na porta 5017...${NC}"
        echo -e "${YELLOW}Pressione Ctrl+C para parar o servidor${NC}"
        echo ""
        python "$SCRIPT_DIR/test_endpoint.py"
        ;;
    2)
        echo -e "${YELLOW}🎮 Iniciando cliente interativo...${NC}"
        echo ""
        python "$SCRIPT_DIR/test_client.py"
        ;;
    3)
        echo -e "${YELLOW}⚡ Executando teste rápido...${NC}"
        echo ""
        python "$SCRIPT_DIR/athena_executor.py"
        ;;
    *)
        echo -e "${RED}❌ Opção inválida${NC}"
        exit 1
        ;;
esac
