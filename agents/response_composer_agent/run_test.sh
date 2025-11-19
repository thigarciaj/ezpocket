#!/bin/bash
# Script de teste para Response Composer Agent

echo "🎨 Testando Response Composer Agent..."
echo ""

# Ativar virtual environment
source ../../ezinho_assistente/bin/activate

# Rodar teste
python response_composer.py

echo ""
echo "✅ Teste concluído!"
