#!/bin/bash

# Script para iniciar todos os workers do Graph Orchestrator
# Os workers processam jobs das filas Redis

set -e

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Diretórios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EZPOKET_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BACKEND_DIR="$EZPOKET_DIR/backend"
VENV_DIR="$EZPOKET_DIR/ezinho_assistente"

echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}🔧 INICIANDO WORKERS DO GRAPH ORCHESTRATOR${NC}"
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

echo -e "${GREEN}✓ Virtual environment ativado${NC}"
echo -e "${GREEN}✓ Diretório: $BACKEND_DIR${NC}"
echo ""

# Função para cleanup quando script terminar
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Parando todos os workers...${NC}"
    kill $(jobs -p) 2>/dev/null || true
    echo -e "${GREEN}✓ Workers parados${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Inicia workers em background
echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}🚀 INICIANDO WORKERS${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""

echo -e "${GREEN}[1/5] Iniciando Worker: Intent Validator${NC}"
python agents/graph_orchestrator/worker_intent_validator.py &
WORKER1_PID=$!
echo -e "      PID: $WORKER1_PID"
echo ""

echo -e "${GREEN}[2/5] Iniciando Worker: Plan Builder${NC}"
python agents/graph_orchestrator/worker_plan_builder.py &
WORKER2_PID=$!
echo -e "      PID: $WORKER2_PID"
echo ""

echo -e "${GREEN}[3/5] Iniciando Worker: Plan Confirm${NC}"
python agents/graph_orchestrator/worker_plan_confirm.py &
WORKER3_PID=$!
echo -e "      PID: $WORKER3_PID"
echo ""

echo -e "${GREEN}[4/5] Iniciando Worker: User Proposed Plan${NC}"
python agents/graph_orchestrator/worker_user_proposed_plan.py &
WORKER4_PID=$!
echo -e "      PID: $WORKER4_PID"
echo ""

echo -e "${GREEN}[5/5] Iniciando Worker: History Preferences${NC}"
python agents/graph_orchestrator/worker_history_preferences.py &
WORKER5_PID=$!
echo -e "      PID: $WORKER5_PID"
echo ""

echo -e "${BLUE}================================================================================${NC}"
echo -e "${GREEN}✅ TODOS OS WORKERS INICIADOS${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""
echo -e "${YELLOW}Workers rodando em background:${NC}"
echo -e "  • Intent Validator (PID: $WORKER1_PID)"
echo -e "  • Plan Builder (PID: $WORKER2_PID)"
echo -e "  • Plan Confirm (PID: $WORKER3_PID)"
echo -e "  • User Proposed Plan (PID: $WORKER4_PID)"
echo -e "  • History Preferences (PID: $WORKER5_PID)"
echo ""
echo -e "${YELLOW}Pressione Ctrl+C para parar todos os workers${NC}"
echo ""
echo -e "${BLUE}================================================================================${NC}"
echo ""

# Aguarda os processos
wait
