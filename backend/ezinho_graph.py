"""
Orquestrador LangGraph - Ezinho Assistant
Integra os 3 agentes em um grafo de execução
"""
from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph, END
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.router_agent.router import RouterAgent
from agents.generator_agent.generator import GeneratorAgent
from agents.responder_agent.responder import ResponderAgent


# Define o estado compartilhado entre nós
class GraphState(TypedDict):
    """Estado compartilhado entre todos os nós"""
    pergunta: str
    route: Optional[Literal["special", "faq", "generate"]]
    tipo: Optional[str]
    faq_match: Optional[dict]
    sql_query: Optional[str]
    resposta_final: Optional[str]
    query: Optional[str]
    source: Optional[str]
    erro: Optional[bool]


class EzinhoGraph:
    """Grafo LangGraph que orquestra os 3 agentes"""
    
    def __init__(self):
        # Inicializa os agentes
        self.router_agent = RouterAgent()
        self.generator_agent = GeneratorAgent()
        self.responder_agent = ResponderAgent()
        
        # Constrói o grafo
        self.app = self._build_graph()
    
    def _build_graph(self):
        """Constrói o grafo de execução"""
        workflow = StateGraph(GraphState)
        
        # Adiciona os nós
        workflow.add_node("router", self._router_node)
        workflow.add_node("special_handler", self._special_handler_node)
        workflow.add_node("generator", self._generator_node)
        workflow.add_node("responder", self._responder_node)
        
        # Define o ponto de entrada
        workflow.set_entry_point("router")
        
        # Define roteamento condicional após router
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
        workflow.add_edge("special_handler", END)
        workflow.add_edge("generator", "responder")
        workflow.add_edge("responder", END)
        
        return workflow.compile()
    
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
    
    def invoke(self, pergunta: str) -> dict:
        """
        Executa o grafo completo
        
        Args:
            pergunta: Pergunta do usuário
            
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
