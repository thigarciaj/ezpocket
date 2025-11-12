"""
Testes Unitários para o Intent Validator Agent
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Adiciona o caminho do backend ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.intent_validator_agent.intent_validator import IntentValidatorAgent


class TestIntentValidatorAgent(unittest.TestCase):
    """Testes para o IntentValidatorAgent"""
    
    def setUp(self):
        """Configuração antes de cada teste"""
        # Não inicializa o agente aqui, será feito em cada teste com mock
        pass
    
    @patch('agents.intent_validator_agent.intent_validator.OpenAI')
    def test_validate_pergunta_analise_dados_valida(self, mock_openai):
        """Testa validação de pergunta válida sobre análise de dados"""
        # Mock da resposta do OpenAI
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''{
            "valid": true,
            "category": "analise_dados",
            "reason": "Pergunta sobre dados financeiros"
        }'''
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Recria o agente com o mock
        self.agent = IntentValidatorAgent()
        
        # Estado de entrada
        state = {
            "pergunta": "Quantos pedidos tivemos em outubro?",
            "username": "test_user",
            "projeto": "ezpocket"
        }
        
        # Executa validação
        result = self.agent.validate(state)
        
        # Verificações
        self.assertTrue(result["intent_valid"])
        self.assertEqual(result["intent_category"], "analise_dados")
        self.assertIsNotNone(result["intent_reason"])
        self.assertIsInstance(result["intent_reason"], str)
        self.assertNotIn("is_special_case", result)
    
    @patch('agents.intent_validator_agent.intent_validator.OpenAI')
    def test_validate_pergunta_fora_escopo(self, mock_openai):
        """Testa validação de pergunta fora do escopo"""
        # Mock da resposta do OpenAI
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''{
            "valid": false,
            "category": "fora_escopo",
            "reason": "Pergunta sobre culinária, fora do domínio financeiro"
        }'''
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Recria o agente com o mock
        self.agent = IntentValidatorAgent()
        
        # Estado de entrada
        state = {
            "pergunta": "Qual a melhor receita de bolo de chocolate?",
            "username": "test_user",
            "projeto": "ezpocket"
        }
        
        # Executa validação
        result = self.agent.validate(state)
        
        # Verificações
        self.assertFalse(result["intent_valid"])
        self.assertEqual(result["intent_category"], "fora_escopo")
        self.assertIn("culinária", result["intent_reason"])
    
    @patch('agents.intent_validator_agent.intent_validator.OpenAI')
    def test_validate_despedida(self, mock_openai):
        """Testa detecção de despedida"""
        # Mock da resposta do OpenAI
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''{
            "valid": true,
            "category": "despedida",
            "reason": "Usuário está se despedindo"
        }'''
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Recria o agente com o mock
        self.agent = IntentValidatorAgent()
        
        # Estado de entrada
        state = {
            "pergunta": "Tchau, até logo!",
            "username": "test_user",
            "projeto": "ezpocket"
        }
        
        # Executa validação
        result = self.agent.validate(state)
        
        # Verificações
        self.assertTrue(result["intent_valid"])
        self.assertEqual(result["intent_category"], "despedida")
        self.assertTrue(result.get("is_special_case", False))
        self.assertEqual(result.get("special_type"), "despedida")
    
    @patch('agents.intent_validator_agent.intent_validator.OpenAI')
    def test_validate_ajuda(self, mock_openai):
        """Testa detecção de pedido de ajuda"""
        # Mock da resposta do OpenAI
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''{
            "valid": true,
            "category": "ajuda",
            "reason": "Usuário pedindo ajuda sobre o sistema"
        }'''
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Recria o agente com o mock
        self.agent = IntentValidatorAgent()
        
        # Estado de entrada
        state = {
            "pergunta": "Help! O que você pode fazer?",
            "username": "test_user",
            "projeto": "ezpocket"
        }
        
        # Executa validação
        result = self.agent.validate(state)
        
        # Verificações
        self.assertTrue(result["intent_valid"])
        self.assertEqual(result["intent_category"], "ajuda")
        self.assertTrue(result.get("is_special_case", False))
        self.assertEqual(result.get("special_type"), "ajuda")
    
    @patch('agents.intent_validator_agent.intent_validator.OpenAI')
    def test_validate_reset(self, mock_openai):
        """Testa detecção de comando reset"""
        # Mock da resposta do OpenAI
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''{
            "valid": true,
            "category": "reset",
            "reason": "Comando para reiniciar conversa"
        }'''
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Recria o agente com o mock
        self.agent = IntentValidatorAgent()
        
        # Estado de entrada
        state = {
            "pergunta": "#resetar",
            "username": "test_user",
            "projeto": "ezpocket"
        }
        
        # Executa validação
        result = self.agent.validate(state)
        
        # Verificações
        self.assertTrue(result["intent_valid"])
        self.assertEqual(result["intent_category"], "reset")
        self.assertTrue(result.get("is_special_case", False))
        self.assertEqual(result.get("special_type"), "reset")
    
    @patch('agents.intent_validator_agent.intent_validator.OpenAI')
    def test_validate_faq(self, mock_openai):
        """Testa detecção de pergunta FAQ"""
        # Mock da resposta do OpenAI
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''{
            "valid": true,
            "category": "faq",
            "reason": "Pergunta frequente conhecida"
        }'''
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Recria o agente com o mock
        self.agent = IntentValidatorAgent()
        
        # Estado de entrada
        state = {
            "pergunta": "Quantos pedidos temos?",
            "username": "test_user",
            "projeto": "ezpocket"
        }
        
        # Executa validação
        result = self.agent.validate(state)
        
        # Verificações
        self.assertTrue(result["intent_valid"])
        self.assertEqual(result["intent_category"], "faq")
    
    @patch('agents.intent_validator_agent.intent_validator.OpenAI')
    def test_validate_erro_api(self, mock_openai):
        """Testa tratamento de erro na API"""
        # Mock que lança exceção
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        # Recria o agente com o mock
        self.agent = IntentValidatorAgent()
        
        # Estado de entrada
        state = {
            "pergunta": "Teste de erro",
            "username": "test_user",
            "projeto": "ezpocket"
        }
        
        # Executa validação
        result = self.agent.validate(state)
        
        # Verificações - deve assumir válido em caso de erro
        self.assertTrue(result["intent_valid"])
        self.assertEqual(result["intent_category"], "analise_dados")
        self.assertIn("Erro na validação", result["intent_reason"])
    
    @patch('agents.intent_validator_agent.intent_validator.OpenAI')
    def test_validate_json_invalido(self, mock_openai):
        """Testa tratamento de JSON inválido da API"""
        # Mock da resposta do OpenAI com JSON inválido
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'JSON inválido aqui'
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Recria o agente com o mock
        self.agent = IntentValidatorAgent()
        
        # Estado de entrada
        state = {
            "pergunta": "Teste JSON inválido",
            "username": "test_user",
            "projeto": "ezpocket"
        }
        
        # Executa validação
        result = self.agent.validate(state)
        
        # Verificações - deve assumir válido em caso de erro
        self.assertTrue(result["intent_valid"])
        self.assertEqual(result["intent_category"], "analise_dados")
    
    def test_generate_out_of_scope_response(self):
        """Testa geração de resposta para perguntas fora do escopo"""
        # Cria agente sem precisar de API key para este teste
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'fake-key'}):
            agent = IntentValidatorAgent()
        
        state = {
            "intent_valid": False,
            "intent_category": "fora_escopo",
            "intent_reason": "Pergunta sobre culinária"
        }
        
        response = agent.generate_out_of_scope_response(state)
        
        # Verificações
        self.assertIsInstance(response, str)
        self.assertIn("fora do escopo", response.lower())
        self.assertIn("EZPocket", response)
        self.assertIn("financeiros", response)
        self.assertIn("help", response.lower())
    
    @patch('agents.intent_validator_agent.intent_validator.OpenAI')
    def test_validate_com_contexto_projeto(self, mock_openai):
        """Testa validação com contexto de projeto específico"""
        # Mock da resposta do OpenAI
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''{
            "valid": true,
            "category": "analise_dados",
            "reason": "Análise válida para o projeto específico"
        }'''
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Recria o agente com o mock
        self.agent = IntentValidatorAgent()
        
        # Estado de entrada com projeto específico
        state = {
            "pergunta": "Qual o status deste projeto?",
            "username": "test_user",
            "projeto": "Projeto ABC 2024"
        }
        
        # Executa validação
        result = self.agent.validate(state)
        
        # Verificações
        self.assertTrue(result["intent_valid"])
        self.assertEqual(result["intent_category"], "analise_dados")
    
    @patch('agents.intent_validator_agent.intent_validator.OpenAI')
    def test_validate_sem_contexto_projeto(self, mock_openai):
        """Testa validação sem contexto de projeto"""
        # Mock da resposta do OpenAI
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''{
            "valid": true,
            "category": "analise_dados",
            "reason": "Análise geral válida"
        }'''
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Recria o agente com o mock
        self.agent = IntentValidatorAgent()
        
        # Estado de entrada sem projeto
        state = {
            "pergunta": "Quantos clientes temos?",
            "username": "test_user",
            "projeto": ""
        }
        
        # Executa validação
        result = self.agent.validate(state)
        
        # Verificações
        self.assertTrue(result["intent_valid"])


class TestIntentValidatorIntegration(unittest.TestCase):
    """Testes de integração com chamadas reais (se API key disponível)"""
    
    def setUp(self):
        """Verifica se API key está disponível"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            self.skipTest("OPENAI_API_KEY não configurada")
        
        self.agent = IntentValidatorAgent()
    
    def test_real_api_call_valida(self):
        """Teste real com API (skip se não houver key)"""
        state = {
            "pergunta": "Quantos pedidos tivemos em outubro?",
            "username": "test_user",
            "projeto": "ezpocket"
        }
        
        result = self.agent.validate(state)
        
        # Verificações básicas
        self.assertIn("intent_valid", result)
        self.assertIn("intent_category", result)
        self.assertIn("intent_reason", result)
        self.assertIsInstance(result["intent_valid"], bool)
        self.assertIsInstance(result["intent_category"], str)


def run_tests():
    """Executa todos os testes"""
    # Cria suite de testes
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Adiciona testes unitários
    suite.addTests(loader.loadTestsFromTestCase(TestIntentValidatorAgent))
    
    # Adiciona testes de integração (se API key disponível)
    suite.addTests(loader.loadTestsFromTestCase(TestIntentValidatorIntegration))
    
    # Executa testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Retorna resultado
    return result.wasSuccessful()


if __name__ == '__main__':
    print("\n" + "="*80)
    print("🧪 EXECUTANDO TESTES UNITÁRIOS - INTENT VALIDATOR AGENT")
    print("="*80 + "\n")
    
    success = run_tests()
    
    print("\n" + "="*80)
    if success:
        print("✅ TODOS OS TESTES PASSARAM!")
    else:
        print("❌ ALGUNS TESTES FALHARAM")
    print("="*80 + "\n")
    
    sys.exit(0 if success else 1)
