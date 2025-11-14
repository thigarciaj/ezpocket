#!/bin/bash

# Script para rodar o endpoint de teste do Analysis Orchestrator Agent
# Uso: ./run_test.sh [modo]
# Modos: server, client, test, interactive, help

set -e

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Diretórios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EZPOKET_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BACKEND_DIR="$EZPOKET_DIR/backend"
VENV_DIR="$EZPOKET_DIR/ezinho_assistente"

echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}⚙️  ANALYSIS ORCHESTRATOR TEST RUNNER${NC}"
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

# Verifica modo
MODE="${1:-help}"

case "$MODE" in
    server)
        echo -e "${GREEN}🚀 Iniciando servidor de teste na porta 5012...${NC}"
        echo -e "${YELLOW}Pressione Ctrl+C para parar o servidor${NC}"
        echo ""
        python agents/analysis_orchestrator_agent/test_endpoint.py
        ;;
    
    interactive|i)
        echo -e "${GREEN}🔧 Modo interativo - Digite seus planos de análise${NC}"
        echo -e "${YELLOW}Digite 'sair' para encerrar${NC}"
        echo ""
        python agents/analysis_orchestrator_agent/test_client.py interactive
        ;;
    
    examples|e)
        echo -e "${GREEN}📚 Executando exemplos pré-definidos...${NC}"
        echo ""
        python agents/analysis_orchestrator_agent/test_client.py examples
        ;;
    
    test|t)
        echo -e "${GREEN}🧪 Executando teste unitário...${NC}"
        echo ""
        python agents/analysis_orchestrator_agent/test_analysis_orchestrator.py
        ;;
    
    help|h|*)
        echo -e "${YELLOW}Modos disponíveis:${NC}"
        echo ""
        echo -e "  ${GREEN}server${NC}        - Inicia servidor Flask na porta 5012"
        echo -e "  ${GREEN}interactive${NC}   - Modo interativo para testar planos"
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
        echo -e "${BLUE}📝 SOBRE O ANALYSIS ORCHESTRATOR AGENT${NC}"
        echo -e "${BLUE}================================================================================${NC}"
        echo ""
        echo -e "O Analysis Orchestrator Agent é o MOTOR PRINCIPAL responsável por:"
        echo -e "  • Transformar planos de análise em queries SQL otimizadas"
        echo -e "  • Validar segurança de queries (prevenir dados sensíveis)"
        echo -e "  • Aplicar regras semânticas de negócio"
        echo -e "  • Garantir sintaxe válida para AWS Athena"
        echo -e "  • Otimizar performance de queries"
        echo -e "  • Respeitar timezone America/New_York"
        echo -e "  • Tratar valores nulos adequadamente"
        echo ""
        echo -e "${YELLOW}Fluxo esperado:${NC}"
        echo -e "  PlanBuilder → AnalysisOrchestrator → QueryExecutor → Responder"
        echo ""
        echo -e "${YELLOW}Entrada:${NC} Plano de análise em linguagem natural"
        echo -e "${YELLOW}Saída:${NC} Query SQL válida e segura para Athena"
        echo ""
        ;;
esac

echo -e "${BLUE}================================================================================${NC}"
