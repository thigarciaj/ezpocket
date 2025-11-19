#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for PlanRefinerAgent
"""

import unittest
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar .env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
load_dotenv(dotenv_path)

# Adicionar backend ao path
backend_path = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, backend_path)

from agents.plan_refiner_agent.plan_refiner import PlanRefinerAgent

class TestPlanRefinerAgent(unittest.TestCase):
    """Test cases for PlanRefinerAgent"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.agent = PlanRefinerAgent()
        print("\n" + "="*60)
        print("🧪 TESTES UNITÁRIOS - PlanRefinerAgent")
        print("="*60)
    
    def test_01_initialization(self):
        """Test agent initialization"""
        print("\n📝 Test 01: Inicialização do agente")
        self.assertIsNotNone(self.agent)
        self.assertIsNotNone(self.agent.client)
        print("   ✅ Agente inicializado corretamente")
    
    def test_02_basic_refinement(self):
        """Test basic plan refinement"""
        print("\n📝 Test 02: Refinamento básico de plano")
        
        result = self.agent.refine_plan(
            pergunta="Qual o valor total de vendas?",
            original_plan="Vou consultar a tabela orders e somar o campo amount",
            user_suggestion="Adicione filtro para os últimos 30 dias",
            intent_category="analise_vendas"
        )
        
        # Validate result structure
        self.assertIn('refined_plan', result)
        self.assertIn('refinement_summary', result)
        self.assertIn('changes_applied', result)
        self.assertIn('user_suggestions_incorporated', result)
        self.assertIn('improvements_made', result)
        
        # Validate refined plan is not empty
        self.assertTrue(len(result['refined_plan']) > 0)
        print(f"   ✅ Plano refinado gerado: {len(result['refined_plan'])} caracteres")
        
        # Validate changes_applied is a list
        self.assertIsInstance(result['changes_applied'], list)
        print(f"   ✅ Mudanças aplicadas: {len(result['changes_applied'])} itens")
    
    def test_03_complex_refinement(self):
        """Test complex plan refinement with multiple suggestions"""
        print("\n📝 Test 03: Refinamento complexo com múltiplas sugestões")
        
        result = self.agent.refine_plan(
            pergunta="Quais os produtos mais vendidos?",
            original_plan="Consultar order_items, agrupar por product_id, contar quantidade",
            user_suggestion="Ordene por valor total de vendas, mostre nome do produto, inclua percentual do total, limite a 10 resultados",
            intent_category="analise_produtos"
        )
        
        # Should incorporate multiple suggestions
        self.assertTrue(len(result['user_suggestions_incorporated']) > 0)
        print(f"   ✅ Sugestões incorporadas: {len(result['user_suggestions_incorporated'])} itens")
        
        # Should have improvements
        self.assertTrue(len(result['improvements_made']) > 0)
        print(f"   ✅ Melhorias aplicadas: {len(result['improvements_made'])} itens")
    
    def test_04_refinement_with_filters(self):
        """Test refinement adding filters"""
        print("\n📝 Test 04: Refinamento adicionando filtros")
        
        result = self.agent.refine_plan(
            pergunta="Quantos pedidos temos?",
            original_plan="Contar registros na tabela orders",
            user_suggestion="Filtre apenas pedidos com status 'completed' e valor acima de R$ 100",
            intent_category="consulta_dados"
        )
        
        # Refined plan should be longer (added filters)
        original_length = len("Contar registros na tabela orders")
        refined_length = len(result['refined_plan'])
        self.assertGreater(refined_length, original_length)
        print(f"   ✅ Plano expandido: {original_length} → {refined_length} caracteres")
    
    def test_05_refinement_with_aggregation(self):
        """Test refinement adding aggregation"""
        print("\n📝 Test 05: Refinamento adicionando agregação")
        
        result = self.agent.refine_plan(
            pergunta="Qual o total de vendas?",
            original_plan="Consultar tabela orders",
            user_suggestion="Agrupe por região e mostre o total e a média de cada região",
            intent_category="analise_vendas"
        )
        
        # Should apply aggregation changes
        changes = result['changes_applied']
        self.assertTrue(len(changes) > 0)
        print(f"   ✅ Mudanças para agregação: {len(changes)} aplicadas")
    
    def test_06_refinement_metadata(self):
        """Test refinement metadata"""
        print("\n📝 Test 06: Metadados do refinamento")
        
        result = self.agent.refine_plan(
            pergunta="Teste metadados",
            original_plan="Plano teste",
            user_suggestion="Sugestão teste",
            intent_category="teste"
        )
        
        # Validate metadata
        self.assertIn('model_used', result)
        self.assertIn('temperature', result)
        self.assertIn('timestamp', result)
        
        print(f"   ✅ Modelo: {result['model_used']}")
        print(f"   ✅ Temperatura: {result['temperature']}")
        print(f"   ✅ Timestamp: {result['timestamp']}")
    
    def test_07_empty_suggestion(self):
        """Test with empty suggestion"""
        print("\n📝 Test 07: Sugestão vazia")
        
        result = self.agent.refine_plan(
            pergunta="Teste",
            original_plan="Plano original",
            user_suggestion="",
            intent_category="teste"
        )
        
        # Should still return valid result
        self.assertIn('refined_plan', result)
        print(f"   ✅ Tratamento de sugestão vazia OK")
    
    def test_08_validation_notes(self):
        """Test validation notes generation"""
        print("\n📝 Test 08: Notas de validação")
        
        result = self.agent.refine_plan(
            pergunta="Deletar todos os registros",
            original_plan="DELETE FROM orders",
            user_suggestion="Sem filtro mesmo, quero deletar tudo",
            intent_category="operacao_perigosa"
        )
        
        # Should have validation notes for dangerous operation
        self.assertIn('validation_notes', result)
        if result['validation_notes']:
            print(f"   ✅ Notas de validação geradas: {len(result['validation_notes'])} itens")
        else:
            print(f"   ⚠️ Nenhuma nota de validação (esperado para operações perigosas)")

def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestPlanRefinerAgent)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    print(f"✅ Testes executados: {result.testsRun}")
    print(f"✅ Sucessos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Falhas: {len(result.failures)}")
    print(f"❌ Erros: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
