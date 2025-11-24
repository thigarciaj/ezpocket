#!/bin/bash

# Script para rodar o Graph Orchestrator com WebSocket
# Uso: ./run_test_websocket.sh

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
VENV_DIR="$EZPOKET_DIR/ezinho_assistente"

echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}🔄 GRAPH ORCHESTRATOR WEBSOCKET TEST RUNNER${NC}"
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

# Verifica se flask-socketio está instalado
echo -e "${YELLOW}🔍 Verificando dependências...${NC}"
if ! python -c "import flask_socketio" 2>/dev/null; then
    echo -e "${YELLOW}📦 Instalando flask-socketio...${NC}"
    pip install flask-socketio python-socketio
fi

# Verifica modo
MODE="${1:-server}"

case "$MODE" in
    server|s)
        echo -e "${GREEN}🚀 Iniciando servidor WebSocket na porta 5008...${NC}"
        echo -e "${YELLOW}Pressione Ctrl+C para parar o servidor${NC}"
        echo ""
        echo -e "${BLUE}📱 Acesse o frontend em: http://localhost:5008${NC}"
        echo ""
        python agents/graph_orchestrator/test_endpoint_websocket.py
        ;;
    
    health|h)
        echo -e "${GREEN}🏥 Verificando health do servidor...${NC}"
        echo ""
        curl -s http://localhost:5008/test-orchestrator/health | python -m json.tool
        ;;
    
    help|*)
        echo ""
        echo -e "${GREEN}Uso: ./run_test_websocket.sh [modo]${NC}"
        echo ""
        echo -e "${YELLOW}Modos disponíveis:${NC}"
        echo ""
        echo -e "  ${BLUE}server, s${NC}    - Inicia o servidor WebSocket (porta 5008)"
        echo -e "  ${BLUE}health, h${NC}    - Verifica health do servidor"
        echo -e "  ${BLUE}help${NC}         - Mostra esta mensagem de ajuda"
        echo ""
        echo -e "${YELLOW}Exemplos:${NC}"
        echo ""
        echo -e "  ${GREEN}# Iniciar servidor${NC}"
        echo -e "  ./run_test_websocket.sh server"
        echo ""
        echo -e "  ${GREEN}# Verificar health${NC}"
        echo -e "  ./run_test_websocket.sh health"
        echo ""
        echo -e "${YELLOW}Como usar:${NC}"
        echo -e "  1. Execute: ./run_test_websocket.sh server"
        echo -e "  2. Abra o navegador em: http://localhost:5008"
        echo -e "  3. Digite suas perguntas no chat"
        echo ""
        echo -e "${BLUE}================================================================================${NC}"
        ;;
esac
