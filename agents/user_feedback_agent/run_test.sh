#!/bin/bash

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   User Feedback Agent - Test Runner${NC}"
echo -e "${BLUE}========================================${NC}"

MODE=$1

if [ "$MODE" == "server" ]; then
    echo -e "${GREEN}[1] Iniciando worker (servidor)...${NC}"
    cd /home/developer/Projetos/projectezpocket/ezpocket/EZPOKET
    source ezinho_assistente/bin/activate
    python agents/graph_orchestrator/worker_user_feedback.py

elif [ "$MODE" == "interactive" ]; then
    echo -e "${GREEN}[2] Modo interativo - Teste com Redis${NC}"
    cd /home/developer/Projetos/projectezpocket/ezpocket/EZPOKET
    source ezinho_assistente/bin/activate
    python agents/user_feedback_agent/test_endpoint.py

else
    echo -e "${YELLOW}[0] Teste básico (sem Redis)${NC}"
    cd /home/developer/Projetos/projectezpocket/ezpocket/EZPOKET
    source ezinho_assistente/bin/activate
    python agents/user_feedback_agent/test_client.py
fi
