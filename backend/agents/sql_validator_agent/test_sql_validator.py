#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for SQLValidatorAgent
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

from agents.sql_validator_agent.sql_validator import SQLValidatorAgent

class TestSQLValidatorAgent(unittest.TestCase):
    """Test cases for SQLValidatorAgent"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.agent = SQLValidatorAgent()
        print("\n" + "="*60)
        print("🧪 TESTES UNITÁRIOS - SQLValidatorAgent")
        print("="*60)
    
    def test_01_initialization(self):
        """Test agent initialization"""
        print("\n📝 Test 01: Inicialização do agente")
        self.assertIsNotNone(self.agent)
        self.assertIsNotNone(self.agent.client)
        print("   ✅ Agente inicializado corretamente")
    
    def test_02_valid_select_query(self):
        """Test validation of valid SELECT query"""
        print("\n📝 Test 02: Validação de query SELECT válida")
        
        query = """
        SELECT order_id, SUM(amount) as total
        FROM receivables_db.report_orders
        WHERE date >= current_date - interval '30' day
        GROUP BY order_id
        LIMIT 100
        """
        
        result = self.agent.validate(
            query_sql=query,
            username="test_user",
            projeto="test_project",
            estimated_complexity="média"
        )
        
        # Validate result structure
        self.assertIn('valid', result)
        self.assertIn('syntax_valid', result)
        self.assertIn('athena_compatible', result)
        self.assertIn('security_issues', result)
        self.assertIn('estimated_cost_usd', result)
        self.assertIn('risk_level', result)
        
        # Should be valid
        self.assertTrue(result['valid'])
        self.assertTrue(result['syntax_valid'])
        print(f"   ✅ Query válida: {result['valid']}")
        print(f"   ✅ Risk Level: {result['risk_level']}")
        print(f"   ✅ Cost: ${result['estimated_cost_usd']} USD")
    
    def test_03_forbidden_operation_insert(self):
        """Test detection of forbidden INSERT operation"""
        print("\n📝 Test 03: Detecção de operação INSERT proibida")
        
        query = """
        INSERT INTO orders (id, amount) VALUES (1, 100)
        """
        
        result = self.agent.validate(
            query_sql=query,
            username="test_user",
            projeto="test_project",
            estimated_complexity="baixa"
        )
        
        # Should be invalid
        self.assertFalse(result['valid'])
        self.assertGreater(len(result.get('security_issues', [])), 0)
        print(f"   ✅ Operação proibida detectada")
        print(f"   ✅ Security Issues: {result['security_issues']}")
    
    def test_04_forbidden_operation_delete(self):
        """Test detection of forbidden DELETE operation"""
        print("\n📝 Test 04: Detecção de operação DELETE proibida")
        
        query = """
        DELETE FROM orders WHERE id = 1
        """
        
        result = self.agent.validate(
            query_sql=query,
            username="test_user",
            projeto="test_project",
            estimated_complexity="baixa"
        )
        
        # Should be invalid
        self.assertFalse(result['valid'])
        print(f"   ✅ Operação DELETE bloqueada")
    
    def test_05_forbidden_operation_drop(self):
        """Test detection of forbidden DROP operation"""
        print("\n📝 Test 05: Detecção de operação DROP proibida")
        
        query = """
        DROP TABLE orders
        """
        
        result = self.agent.validate(
            query_sql=query,
            username="test_user",
            projeto="test_project",
            estimated_complexity="baixa"
        )
        
        # Should be invalid
        self.assertFalse(result['valid'])
        print(f"   ✅ Operação DROP bloqueada")
    
    def test_06_multiple_queries(self):
        """Test detection of multiple queries (SQL injection)"""
        print("\n📝 Test 06: Detecção de múltiplas queries")
        
        query = """
        SELECT * FROM orders; DROP TABLE orders;
        """
        
        result = self.agent.validate(
            query_sql=query,
            username="test_user",
            projeto="test_project",
            estimated_complexity="baixa"
        )
        
        # Should be invalid
        self.assertFalse(result['valid'])
        print(f"   ✅ Múltiplas queries detectadas")
    
    def test_07_complex_query_cost_estimation(self):
        """Test cost estimation for complex query"""
        print("\n📝 Test 07: Estimativa de custo para query complexa")
        
        query = """
        SELECT a.*, b.*, c.*
        FROM large_table a
        JOIN another_table b ON a.id = b.id
        JOIN third_table c ON b.id = c.id
        WHERE a.date >= '2025-01-01'
        GROUP BY a.id, b.id, c.id
        ORDER BY a.amount DESC
        """
        
        result = self.agent.validate(
            query_sql=query,
            username="test_user",
            projeto="test_project",
            estimated_complexity="alta"
        )
        
        # Should estimate higher cost
        self.assertGreater(result['estimated_scan_size_gb'], 0.1)
        self.assertGreater(result['estimated_execution_time_seconds'], 2.0)
        print(f"   ✅ Scan estimado: {result['estimated_scan_size_gb']} GB")
        print(f"   ✅ Custo estimado: ${result['estimated_cost_usd']} USD")
        print(f"   ✅ Tempo estimado: {result['estimated_execution_time_seconds']}s")
    
    def test_08_empty_query(self):
        """Test validation of empty query"""
        print("\n📝 Test 08: Validação de query vazia")
        
        result = self.agent.validate(
            query_sql="",
            username="test_user",
            projeto="test_project",
            estimated_complexity="baixa"
        )
        
        # Should be invalid
        self.assertFalse(result['valid'])
        self.assertIsNotNone(result.get('error'))
        print(f"   ✅ Query vazia detectada")
    
    def test_09_query_with_aggregation(self):
        """Test query with aggregation functions"""
        print("\n📝 Test 09: Query com funções de agregação")
        
        query = """
        SELECT 
            DATE_TRUNC('day', order_date) as day,
            COUNT(*) as total_orders,
            SUM(amount) as total_amount,
            AVG(amount) as avg_amount,
            MAX(amount) as max_amount,
            MIN(amount) as min_amount
        FROM receivables_db.report_orders
        WHERE order_date >= current_date - interval '7' day
        GROUP BY DATE_TRUNC('day', order_date)
        ORDER BY day DESC
        """
        
        result = self.agent.validate(
            query_sql=query,
            username="test_user",
            projeto="test_project",
            estimated_complexity="média"
        )
        
        # Should be valid
        self.assertTrue(result['valid'])
        print(f"   ✅ Query com agregação válida")
        print(f"   ✅ Risk Level: {result['risk_level']}")
    
    def test_10_query_size_limit(self):
        """Test query size limit"""
        print("\n📝 Test 10: Limite de tamanho da query")
        
        # Create a very large query (> 256 KB)
        large_query = "SELECT * FROM orders WHERE id IN (" + ",".join([str(i) for i in range(100000)]) + ")"
        
        result = self.agent.validate(
            query_sql=large_query,
            username="test_user",
            projeto="test_project",
            estimated_complexity="baixa"
        )
        
        # Should be invalid
        self.assertFalse(result['valid'])
        print(f"   ✅ Query muito grande detectada ({len(large_query)} bytes)")


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSQLValidatorAgent)
    
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
    print("="*60)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
