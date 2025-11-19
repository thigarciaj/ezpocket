#!/bin/bash

# Script para rodar o endpoint de teste do Plan Confirm Agent
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
echo -e "${BLUE}🧪 PLAN CONFIRM TEST RUNNER${NC}"
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
        echo -e "${GREEN}🚀 Iniciando servidor de teste na porta 5010...${NC}"
        echo -e "${YELLOW}Pressione Ctrl+C para parar o servidor${NC}"
        echo ""
        python agents/plan_confirm_agent/test_endpoint.py
        ;;
    
    interactive|i)
        echo -e "${GREEN}🔧 Modo interativo - Digite suas perguntas${NC}"
        echo -e "${YELLOW}Digite 'sair' para encerrar${NC}"
        echo ""
        python agents/plan_confirm_agent/test_client.py interactive
        ;;
    
    examples|e)
        echo -e "${GREEN}📚 Executando exemplos pré-definidos...${NC}"
        echo ""
        python agents/plan_confirm_agent/test_client.py examples
        ;;
    
    test|t)
        echo -e "${GREEN}🧪 Executando teste unitário...${NC}"
        echo ""
        python agents/plan_confirm_agent/test_plan_confirm.py
        ;;
    
    help|h|*)
        echo -e "${YELLOW}Modos disponíveis:${NC}"
        echo ""
        echo -e "  ${GREEN}server${NC}        - Inicia servidor Flask na porta 5010"
        echo -e "  ${GREEN}interactive${NC}   - Modo interativo para testar perguntas"
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
        echo -e "${BLUE}📝 SOBRE O PLAN CONFIRM AGENT${NC}"
        echo -e "${BLUE}================================================================================${NC}"
        echo ""
        echo -e "O Plan Confirm Agent é responsável por:"
        echo -e "  • Apresentar o plano de execução gerado"
        echo -e "  • Solicitar confirmação do usuário"
        echo -e "  • Destacar recursos e complexidade"
        echo -e "  • Permitir aceite ou rejeição do plano"
        echo ""
        echo -e "${YELLOW}Nota:${NC} Este agente NÃO salva dados no banco de dados."
        echo -e "      Apenas imprime os resultados no console."
        echo ""
        ;;
esac

echo -e "${BLUE}================================================================================${NC}"
