"""
Athena Executor Agent - Executa queries no AWS Athena
Não usa IA, apenas executa a query final validada/corrigida
"""

from .athena_executor import AthenaExecutorAgent

__all__ = ['AthenaExecutorAgent']
