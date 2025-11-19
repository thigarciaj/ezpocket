#!/bin/bash

# Script para rodar o endpoint de teste do User Proposed Plan Agent
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
EZPOKET_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
# BACKEND_DIR removido - usando EZPOKET_DIR diretamente
VENV_DIR="$EZPOKET_DIR/ezinho_assistente"

echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}💡 USER PROPOSED PLAN TEST RUNNER${NC}"
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
        echo -e "${GREEN}🚀 Iniciando servidor de teste na porta 5011...${NC}"
        echo -e "${YELLOW}Pressione Ctrl+C para parar o servidor${NC}"
        echo ""
        python agents/user_proposed_plan_agent/test_endpoint.py
        ;;
    
    interactive|i)
        echo -e "${GREEN}🔧 Modo interativo - Digite suas sugestões${NC}"
        echo -e "${YELLOW}Digite 'sair' para encerrar${NC}"
        echo ""
        python agents/user_proposed_plan_agent/test_client.py interactive
        ;;
    
    examples|e)
        echo -e "${GREEN}📚 Executando exemplos pré-definidos...${NC}"
        echo ""
        python agents/user_proposed_plan_agent/test_client.py examples
        ;;
    
    test|t)
        echo -e "${GREEN}🧪 Executando teste unitário...${NC}"
        echo ""
        python agents/user_proposed_plan_agent/test_user_proposed_plan.py
        ;;
    
    help|h|*)
        echo -e "${YELLOW}Modos disponíveis:${NC}"
        echo ""
        echo -e "  ${GREEN}server${NC}        - Inicia servidor Flask na porta 5011"
        echo -e "  ${GREEN}interactive${NC}   - Modo interativo para testar sugestões"
        echo -e "  ${GREEN}examples${NC}      - Executa exemplos pré-definidos"
        echo -e "  ${GREEN}test${NC}          - Executa teste unitário do agente"
        echo -e "  ${GREEN}help${NC}          - Mostra esta mensagem"
        echo ""
        echo -e "${YELLOW}Exemplos de uso:${NC}"
        echo -e "  ./run_test.sh server"
        echo -e "  ./run_test.sh interactive"
        echo -e "  ./run_test.sh examples"
        echo -e "  ./run_test.sh test"
        echo ""
        echo -e "${BLUE}================================================================================${NC}"
        echo -e "${BLUE}📝 SOBRE O USER PROPOSED PLAN AGENT${NC}"
        echo -e "${BLUE}================================================================================${NC}"
        echo ""
        echo -e "O User Proposed Plan Agent é responsável por:"
        echo -e "  • Receber sugestão do usuário sobre o que fazer"
        echo -e "  • Validar que sugestão não está vazia"
        echo -e "  • Retornar sugestão sem modificações"
        echo -e "  • Não processar com IA (apenas pass-through)"
        echo ""
        echo -e "${YELLOW}Nota:${NC} Similar ao PlanConfirmAgent - apenas recebe input do usuário."
        echo ""
        ;;
esac

echo -e "${BLUE}================================================================================${NC}"
