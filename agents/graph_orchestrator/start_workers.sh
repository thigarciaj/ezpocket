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
EZPOKET_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
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

# Vai para o diretório raiz do projeto
cd "$EZPOKET_DIR"

echo -e "${GREEN}✓ Virtual environment ativado${NC}"
echo -e "${GREEN}✓ Diretório: $EZPOKET_DIR${NC}"
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

echo -e "${GREEN}[1/7] Iniciando Worker: Intent Validator${NC}"
python agents/graph_orchestrator/worker_intent_validator.py &
WORKER1_PID=$!
echo -e "      PID: $WORKER1_PID"
echo ""

echo -e "${GREEN}[2/7] Iniciando Worker: Plan Builder${NC}"
python agents/graph_orchestrator/worker_plan_builder.py &
WORKER2_PID=$!
echo -e "      PID: $WORKER2_PID"
echo ""

echo -e "${GREEN}[3/7] Iniciando Worker: Plan Confirm${NC}"
python agents/graph_orchestrator/worker_plan_confirm.py &
WORKER3_PID=$!
echo -e "      PID: $WORKER3_PID"
echo ""

echo -e "${GREEN}[4/7] Iniciando Worker: User Proposed Plan${NC}"
python agents/graph_orchestrator/worker_user_proposed_plan.py &
WORKER4_PID=$!
echo -e "      PID: $WORKER4_PID"
echo ""

echo -e "${GREEN}[5/9] Iniciando Worker: Plan Refiner${NC}"
python agents/graph_orchestrator/worker_plan_refiner.py &
WORKER5_PID=$!
echo -e "      PID: $WORKER5_PID"
echo ""

echo -e "${GREEN}[6/9] Iniciando Worker: Analysis Orchestrator${NC}"
python agents/graph_orchestrator/worker_analysis_orchestrator.py &
WORKER6_PID=$!
echo -e "      PID: $WORKER6_PID"
echo ""

echo -e "${GREEN}[7/9] Iniciando Worker: SQL Validator${NC}"
python agents/graph_orchestrator/worker_sql_validator.py &
WORKER7_PID=$!
echo -e "      PID: $WORKER7_PID"
echo ""

echo -e "${GREEN}[8/10] Iniciando Worker: Auto Correction${NC}"
python agents/graph_orchestrator/worker_auto_correction.py &
WORKER8_PID=$!
echo -e "      PID: $WORKER8_PID"
echo ""

echo -e "${GREEN}[9/11] Iniciando Worker: Athena Executor${NC}"
python agents/graph_orchestrator/worker_athena_executor.py &
WORKER9_PID=$!
echo -e "      PID: $WORKER9_PID"
echo ""

echo -e "${GREEN}[10/12] Iniciando Worker: Python Runtime${NC}"
python agents/graph_orchestrator/worker_python_runtime.py &
WORKER10_PID=$!
echo -e "      PID: $WORKER10_PID"
echo ""

echo -e "${GREEN}[11/12] Iniciando Worker: Response Composer${NC}"
python agents/graph_orchestrator/worker_response_composer.py &
WORKER11_PID=$!
echo -e "      PID: $WORKER11_PID"
echo ""

echo -e "${GREEN}[12/13] Iniciando Worker: User Feedback${NC}"
python agents/graph_orchestrator/worker_user_feedback.py &
WORKER12_PID=$!
echo -e "      PID: $WORKER12_PID"
echo ""

echo -e "${GREEN}[13/13] Iniciando Worker: History Preferences${NC}"
python agents/graph_orchestrator/worker_history_preferences.py &
WORKER13_PID=$!
echo -e "      PID: $WORKER13_PID"
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
echo -e "  • Plan Refiner (PID: $WORKER5_PID)"
echo -e "  • Analysis Orchestrator (PID: $WORKER6_PID)"
echo -e "  • SQL Validator (PID: $WORKER7_PID)"
echo -e "  • Auto Correction (PID: $WORKER8_PID)"
echo -e "  • Athena Executor (PID: $WORKER9_PID)"
echo -e "  • Python Runtime (PID: $WORKER10_PID)"
echo -e "  • Response Composer (PID: $WORKER11_PID)"
echo -e "  • User Feedback (PID: $WORKER12_PID)"
echo -e "  • History Preferences (PID: $WORKER13_PID)"
echo ""
echo -e "${YELLOW}Pressione Ctrl+C para parar todos os workers${NC}"
echo ""
echo -e "${BLUE}================================================================================${NC}"
echo ""

# Aguarda os processos
wait
