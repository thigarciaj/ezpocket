#!/bin/bash
# Script de teste para Python Runtime Agent

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         PYTHON RUNTIME AGENT - TEST RUNNER                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"

# Definir diretórios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EZPOKET_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${YELLOW}📁 Diretório raiz do projeto: $EZPOKET_DIR${NC}"

# Carregar variáveis de ambiente
if [ -f "$EZPOKET_DIR/.env" ]; then
    export $(grep -v '^#' "$EZPOKET_DIR/.env" | xargs)
    echo -e "${GREEN}✅ Variáveis de ambiente carregadas${NC}"
else
    echo -e "${RED}❌ Arquivo .env não encontrado!${NC}"
    exit 1
fi

# Verificar OPENAI_API_KEY
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}❌ OPENAI_API_KEY não encontrada no .env${NC}"
    exit 1
fi

# Ir para raiz do projeto
cd "$EZPOKET_DIR"

# Verificar modo de execução
MODE=${1:-"basic"}

if [ "$MODE" == "interactive" ]; then
    echo -e "\n${BLUE}🚀 Iniciando servidor interativo...${NC}"
    echo -e "${YELLOW}   Porta: ${PYTHON_RUNTIME_PORT:-5018}${NC}"
    echo -e "${YELLOW}   Modo: Interactive Test Server${NC}\n"
    
    # Executar servidor Flask
    python agents/python_runtime_agent/test_endpoint.py
    
elif [ "$MODE" == "client" ]; then
    echo -e "\n${BLUE}🧪 Executando testes com client...${NC}\n"
    
    # Executar test client
    python agents/python_runtime_agent/test_client.py
    
else
    echo -e "\n${BLUE}🧪 Executando teste básico...${NC}\n"
    
    # Executar teste básico
    python agents/python_runtime_agent/python_runtime.py
fi

echo -e "\n${GREEN}✅ Teste concluído!${NC}"
