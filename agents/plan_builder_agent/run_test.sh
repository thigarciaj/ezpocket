#!/bin/bash

# Script para rodar o endpoint de teste do Plan Builder Agent
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
echo -e "${BLUE}🧪 PLAN BUILDER TEST RUNNER${NC}"
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
        echo -e "${GREEN}🚀 Iniciando servidor de teste na porta 5009...${NC}"
        echo -e "${YELLOW}Pressione Ctrl+C para parar o servidor${NC}"
        echo ""
        python agents/plan_builder_agent/test_endpoint.py
        ;;
    
    interactive|i)
        echo -e "${GREEN}🎮 Iniciando modo interativo...${NC}"
        echo ""
        python agents/plan_builder_agent/test_client.py interactive
        ;;
    
    examples|ex)
        echo -e "${GREEN}📚 Executando todos os exemplos...${NC}"
        echo ""
        python agents/plan_builder_agent/test_client.py run-examples
        ;;
    
    test)
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Erro: Especifique uma pergunta e categoria${NC}"
            echo -e "${YELLOW}Uso: ./run_test.sh test \"<pergunta>\" <categoria> [username] [projeto]${NC}"
            exit 1
        fi
        
        if [ -z "$3" ]; then
            echo -e "${RED}❌ Erro: Especifique a categoria da intenção${NC}"
            echo -e "${YELLOW}Categorias: quantidade, conhecimentos_gerais, analise_estatistica${NC}"
            exit 1
        fi
        
        PERGUNTA="$2"
        CATEGORIA="$3"
        USERNAME="${4:-test_user}"
        PROJETO="${5:-test_project}"
        
        echo -e "${GREEN}🔍 Testando pergunta...${NC}"
        echo ""
        python agents/plan_builder_agent/test_client.py test "$PERGUNTA" "$CATEGORIA" "$USERNAME" "$PROJETO"
        ;;
    
    health|h)
        echo -e "${GREEN}🏥 Verificando health do servidor...${NC}"
        echo ""
        python agents/plan_builder_agent/test_client.py health
        ;;
    
    help|*)
        echo ""
        echo -e "${GREEN}Uso: ./run_test.sh [modo] [argumentos]${NC}"
        echo ""
        echo -e "${YELLOW}Modos disponíveis:${NC}"
        echo ""
        echo -e "  ${BLUE}server${NC}           - Inicia o servidor de teste (porta 5009)"
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
        echo -e "  ./run_test.sh test \"Quantos pedidos temos?\" quantidade"
        echo -e "  ./run_test.sh test \"O que é EZPocket?\" conhecimentos_gerais joao projeto_abc"
        echo ""
        echo -e "  ${GREEN}# Health check${NC}"
        echo -e "  ./run_test.sh health"
        echo ""
        echo -e "${YELLOW}Categorias disponíveis:${NC}"
        echo -e "  • quantidade"
        echo -e "  • conhecimentos_gerais"
        echo -e "  • analise_estatistica"
        echo -e "  • comparacao"
        echo ""
        echo -e "${BLUE}================================================================================${NC}"
        ;;
esac
