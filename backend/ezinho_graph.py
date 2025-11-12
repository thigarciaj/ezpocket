"""
Orquestrador LangGraph - Ezinho Assistant
Integra os agentes em um grafo de execução
"""
from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph, END
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.intent_validator_agent.intent_validator import IntentValidatorAgent
from agents.router_agent.router import RouterAgent
from agents.generator_agent.generator import GeneratorAgent
from agents.responder_agent.responder import ResponderAgent


# Define o estado compartilhado entre nós
class GraphState(TypedDict):
    """Estado compartilhado entre todos os nós"""
    pergunta: str
    username: Optional[str]
    projeto: Optional[str]
    intent_valid: Optional[bool]
    intent_category: Optional[str]
    intent_reason: Optional[str]
    is_special_case: Optional[bool]
    special_type: Optional[str]
    route: Optional[Literal["special", "faq", "generate"]]
    tipo: Optional[str]
    faq_match: Optional[dict]
    sql_query: Optional[str]
    resposta_final: Optional[str]
    query: Optional[str]
    source: Optional[str]
    erro: Optional[bool]


class EzinhoGraph:
    """Grafo LangGraph que orquestra os agentes"""
    
    def __init__(self):
        # Inicializa os agentes
        self.intent_validator_agent = IntentValidatorAgent()
        self.router_agent = RouterAgent()
        self.generator_agent = GeneratorAgent()
        self.responder_agent = ResponderAgent()
        
        # Constrói o grafo
        self.app = self._build_graph()
    
    def _build_graph(self):
        """Constrói o grafo de execução"""
        workflow = StateGraph(GraphState)
        
        # Adiciona os nós
        workflow.add_node("intent_validator", self._intent_validator_node)
        workflow.add_node("router", self._router_node)
        workflow.add_node("special_handler", self._special_handler_node)
        workflow.add_node("generator", self._generator_node)
        workflow.add_node("responder", self._responder_node)
        workflow.add_node("out_of_scope", self._out_of_scope_node)
        
        # Define o ponto de entrada - agora é o Intent Validator
        workflow.set_entry_point("intent_validator")
        
        # Roteamento após validação de intenção
        workflow.add_conditional_edges(
            "intent_validator",
            self._intent_decision,
            {
                "valid": "router",
                "invalid": "out_of_scope"
            }
        )
        
        # Roteamento condicional após router
        workflow.add_conditional_edges(
            "router",
            self._route_decision,
            {
                "special": "special_handler",
                "faq": "responder",
                "generate": "generator"
            }
        )
        
        # Edges diretas
        workflow.add_edge("out_of_scope", END)
        workflow.add_edge("special_handler", END)
        workflow.add_edge("generator", "responder")
        workflow.add_edge("responder", END)
        
        return workflow.compile()
    
    def _intent_validator_node(self, state: GraphState) -> GraphState:
        """NÓ 0: Intent Validator Agent"""
        resultado = self.intent_validator_agent.validate(state)
        state.update(resultado)
        return state
    
    def _intent_decision(self, state: GraphState) -> Literal["valid", "invalid"]:
        """Decide se a intenção é válida"""
        is_valid = state.get("intent_valid", True)
        return "valid" if is_valid else "invalid"
    
    def _out_of_scope_node(self, state: GraphState) -> GraphState:
        """Trata perguntas fora do escopo"""
        print(f"\n{'='*60}")
        print(f"[GRAPH] OUT OF SCOPE - Pergunta fora do escopo")
        print(f"{'='*60}")
        
        response = self.intent_validator_agent.generate_out_of_scope_response(state)
        state["resposta_final"] = response
        state["source"] = "out_of_scope"
        return state
    
    def _router_node(self, state: GraphState) -> GraphState:
        """NÓ 1: Router Agent"""
        print(f"\n{'='*60}")
        print(f"[GRAPH] NÓ 1: ROUTER AGENT")
        print(f"{'='*60}")
        
        resultado = self.router_agent.route(state)
        state.update(resultado)
        return state
    
    def _special_handler_node(self, state: GraphState) -> GraphState:
        """Processa casos especiais (parte do Router Agent)"""
        print(f"\n{'='*60}")
        print(f"[GRAPH] SPECIAL HANDLER (Router Agent)")
        print(f"{'='*60}")
        
        resultado = self.router_agent.handle_special(state)
        state.update(resultado)
        return state
    
    def _generator_node(self, state: GraphState) -> GraphState:
        """NÓ 2: Generator Agent"""
        print(f"\n{'='*60}")
        print(f"[GRAPH] NÓ 2: GENERATOR AGENT")
        print(f"{'='*60}")
        
        resultado = self.generator_agent.generate(state)
        state.update(resultado)
        return state
    
    def _responder_node(self, state: GraphState) -> GraphState:
        """NÓ 3: Responder Agent"""
        print(f"\n{'='*60}")
        print(f"[GRAPH] NÓ 3: RESPONDER AGENT")
        print(f"{'='*60}")
        
        resultado = self.responder_agent.respond(state)
        state.update(resultado)
        return state
    
    def _route_decision(self, state: GraphState) -> str:
        """Decide qual caminho seguir após o router"""
        route = state.get("route", "generate")
        print(f"[GRAPH] 🔀 Roteamento: {route}")
        return route
    
    def invoke(self, pergunta: str, username: str = None, projeto: str = None) -> dict:
        """
        Executa o grafo completo
        
        Args:
            pergunta: Pergunta do usuário
            username: Nome do usuário (opcional)
            projeto: Projeto selecionado (opcional)
            
        Returns:
            dict com resposta_final, query e source
        """
        print(f"\n{'='*60}")
        print(f"[GRAPH] 🚀 INICIANDO PROCESSAMENTO")
        print(f"[GRAPH] Pergunta: {pergunta}")
        print(f"{'='*60}")
        
        # Estado inicial
        initial_state = {
            "pergunta": pergunta,
            "username": username,
            "projeto": projeto,
            "intent_valid": None,
            "intent_category": None,
            "intent_reason": None,
            "is_special_case": None,
            "special_type": None,
            "route": None,
            "tipo": None,
            "faq_match": None,
            "sql_query": None,
            "resposta_final": None,
            "query": None,
            "source": None,
            "erro": False
        }
        
        # Executa o grafo
        final_state = self.app.invoke(initial_state)
        
        print(f"\n{'='*60}")
        print(f"[GRAPH] ✅ PROCESSAMENTO CONCLUÍDO")
        print(f"[GRAPH] Source: {final_state.get('source')}")
        print(f"{'='*60}\n")
        
        # Retorna no formato esperado
        return {
            "resposta": final_state.get("resposta_final"),
            "query": final_state.get("query"),
            "source": final_state.get("source")
        }
    
    def reset_history(self):
        """Reseta o histórico de conversação"""
        self.generator_agent.reset_history()


# Singleton global
_ezinho_graph = None

def get_ezinho_graph():
    """Retorna instância singleton do grafo"""
    global _ezinho_graph
    if _ezinho_graph is None:
        _ezinho_graph = EzinhoGraph()
    return _ezinho_graph


# Função de compatibilidade com código legado
def responder(pergunta: str) -> dict:
    """
    Função wrapper para manter compatibilidade com código existente
    """
    graph = get_ezinho_graph()
    return graph.invoke(pergunta)
