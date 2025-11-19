"""
Analysis Orchestrator Agent
============================
Transforma planos em queries SQL otimizadas para AWS Athena.
Motor principal da funcionalidade de análise de dados.
"""

from .analysis_orchestrator import AnalysisOrchestratorAgent

__all__ = ['AnalysisOrchestratorAgent']
