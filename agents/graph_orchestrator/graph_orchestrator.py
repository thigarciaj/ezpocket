"""
GRAPH ORCHESTRATOR - Sistema de Filas
======================================
Processa grafo de módulos usando filas assíncronas (RabbitMQ/Redis)
ao invés de HTTP requests sequenciais - MUITO MAIS RÁPIDO!

COMO FUNCIONA:
1. Cada módulo consome mensagens de sua fila
2. Quando termina, deposita resultado na fila do próximo módulo
3. Processamento paralelo e assíncrono
4. Log salvo no PostgreSQL ao final
"""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv
import redis
from redis import Redis
import uuid
from copy import deepcopy

# Importar configuração do grafo
from agents.graph_orchestrator.graph_config import GRAPH_CONNECTIONS

load_dotenv()

# =====================================================
# CONFIGURAÇÃO DO REDIS (FILA)
# =====================================================

REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6493)),
    'db': int(os.getenv('REDIS_DB', 0)),
    'decode_responses': True
}

# =====================================================
# GRAPH ORCHESTRATOR
# =====================================================

class GraphOrchestrator:
    """
    Orquestrador que gerencia filas e processamento do grafo
    """
    
    def __init__(self):
        self.redis_client = Redis(**REDIS_CONFIG)
        self.connections = GRAPH_CONNECTIONS
        
    def submit_job(
        self,
        start_module: str,
        username: str,
        projeto: str,
        initial_data: Dict[str, Any]
    ) -> str:
        """
        Submete um job para processamento no grafo
        
        Args:
            start_module: Módulo inicial (ex: 'intent_validator')
            username: Nome do usuário
            projeto: Nome do projeto
            initial_data: Dados iniciais (ex: {'pergunta': '...'})
            
        Returns:
            job_id para rastreamento
        """
        
        job_id = str(uuid.uuid4())
        
        # Criar job no Redis
        job_data = {
            'job_id': job_id,
            'username': username,
            'projeto': projeto,
            'start_module': start_module,
            'current_module': start_module,
            'data': initial_data,
            'execution_chain': [],
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        # Salvar job info
        self.redis_client.setex(
            f"job:{job_id}",
            3600,  # TTL: 1 hora
            json.dumps(job_data)
        )
        
        # Adicionar à fila do módulo inicial
        queue_name = f"queue:{start_module}"
        self.redis_client.rpush(queue_name, job_id)
        
        print(f"\n✅ Job {job_id} submetido para {start_module}")
        print(f"   👤 Usuário: {username}")
        print(f"   📊 Projeto: {projeto}")
        print(f"   📥 Dados: {list(initial_data.keys())}")
        
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Consulta status de um job"""
        job_json = self.redis_client.get(f"job:{job_id}")
        if job_json:
            return json.loads(job_json)
        return None
    
    def get_job_with_branches(self, job_id: str) -> Optional[Dict]:
        """
        Consulta job principal e todas as branches paralelas (recursivamente)
        Consolida execution_chain de todas as branches e sub-branches
        """
        main_job = self.get_job_status(job_id)
        if not main_job:
            return None
        
        # Função recursiva para buscar todas as branches aninhadas
        def get_all_child_jobs(parent_id: str) -> list:
            children = []
            for key in self.redis_client.scan_iter(match="job:*"):
                job_data_json = self.redis_client.get(key)
                if job_data_json:
                    job_data = json.loads(job_data_json)
                    
                    # Se é filho direto deste parent
                    if job_data.get('parent_job_id') == parent_id:
                        children.append(job_data)
                        # Buscar recursivamente os filhos deste job
                        children.extend(get_all_child_jobs(job_data.get('job_id')))
            
            return children
        
        # Buscar TODAS as branches recursivamente
        all_jobs = [main_job]
        branch_jobs = get_all_child_jobs(job_id)
        
        # Consolidar execution_chain de todos os jobs
        consolidated_chain = []
        for job in all_jobs + branch_jobs:
            consolidated_chain.extend(job.get('execution_chain', []))
        
        # Ordenar por timestamp
        consolidated_chain.sort(key=lambda x: x.get('timestamp', ''))
        
        # Verificar status de todas as branches E do job principal
        main_status = main_job.get('status', 'unknown')
        all_completed = all(job.get('status') == 'completed' for job in branch_jobs)
        any_failed = any(job.get('status') == 'failed' for job in branch_jobs)
        
        # Determinar status consolidado
        if branch_jobs:
            if any_failed:
                consolidated_status = 'partial_failure'
            elif all_completed and main_status == 'completed':
                # Só considera completo quando TODAS as branches E o job principal completaram
                consolidated_status = 'completed'
            else:
                consolidated_status = 'processing_branches'
        else:
            consolidated_status = main_status
        
        # Criar job consolidado
        result = main_job.copy()
        result['execution_chain'] = consolidated_chain
        result['branches_count'] = len(branch_jobs)
        result['consolidated_status'] = consolidated_status
        result['branch_details'] = [
            {
                'job_id': b.get('job_id'),
                'module': b.get('current_module'),
                'status': b.get('status'),
                'completed_at': b.get('completed_at')
            }
            for b in branch_jobs
        ]
        
        return result
    
    def list_queues(self) -> Dict[str, int]:
        """Lista tamanho de todas as filas"""
        queues = {}
        for module in self.connections.keys():
            queue_name = f"queue:{module}"
            size = self.redis_client.llen(queue_name)
            queues[module] = size
        return queues
    
    def cleanup_user_session(self, username: str, projeto: str) -> Dict[str, Any]:
        """
        Limpa TUDO relacionado a um usuário/projeto quando ele faz logout/F5/reset
        
        Remove:
        - Jobs ativos e suas branches
        - Chaves pendentes (plan_confirm, user_feedback, user_proposed_plan)
        - Histórico/memória no Redis
        - Jobs das filas (previne processamento de jobs antigos)
        
        Args:
            username: Nome do usuário
            projeto: Nome do projeto
            
        Returns:
            Dict com estatísticas da limpeza
        """
        print(f"\n{'='*80}")
        print(f"🧹 LIMPEZA DE SESSÃO - {username}/{projeto}")
        print(f"{'='*80}")
        
        stats = {
            'jobs_deleted': 0,
            'branches_deleted': 0,
            'pending_keys_deleted': 0,
            'memory_keys_deleted': 0,
            'queue_jobs_removed': 0
        }
        
        # 1. BUSCAR E DELETAR **TODOS** OS JOBS DO USUÁRIO (qualquer status)
        print(f"\n[CLEANUP] 🔍 Buscando TODOS os jobs de {username}/{projeto}...")
        
        job_pattern = "job:*"
        deleted_job_ids = []  # Para deletar parent/child jobs depois
        
        for job_key in self.redis_client.scan_iter(match=job_pattern):
            try:
                job_data_raw = self.redis_client.get(job_key)
                if not job_data_raw:
                    continue
                    
                job_data = json.loads(job_data_raw)
                
                # Verificar se o job pertence ao usuário/projeto (QUALQUER STATUS)
                if (job_data.get('username') == username and 
                    job_data.get('projeto') == projeto):
                    
                    job_id = job_data.get('job_id')
                    status = job_data.get('status', 'unknown')
                    print(f"[CLEANUP] 🗑️  Deletando job {status}: {job_id[:8]}...")
                    
                    # Guardar job_id para limpar relacionados depois
                    deleted_job_ids.append(job_id)
                    
                    # Deletar o job
                    self.redis_client.delete(job_key)
                    stats['jobs_deleted'] += 1
                    
                    # Deletar branches deste job
                    branch_pattern = f"job:{job_id}:branch:*"
                    for branch_key in self.redis_client.scan_iter(match=branch_pattern):
                        self.redis_client.delete(branch_key)
                        stats['branches_deleted'] += 1
                        print(f"[CLEANUP] 🗑️  Deletando branch: {branch_key}")
            
            except (json.JSONDecodeError, TypeError) as e:
                continue
        
        # Deletar jobs que tenham parent_job_id de algum job deletado
        if deleted_job_ids:
            print(f"\n[CLEANUP] 🧹 Limpando jobs filhos (parent_job_id)...")
            for job_key in self.redis_client.scan_iter(match=job_pattern):
                try:
                    job_data_raw = self.redis_client.get(job_key)
                    if not job_data_raw:
                        continue
                    job_data = json.loads(job_data_raw)
                    parent_id = job_data.get('parent_job_id')
                    if parent_id in deleted_job_ids:
                        print(f"[CLEANUP] 🗑️  Deletando job filho: {job_data.get('job_id', '')[:8]}...")
                        self.redis_client.delete(job_key)
                        stats['jobs_deleted'] += 1
                except:
                    continue
        
        # 2. DELETAR CHAVES PENDENTES DE INPUT
        print(f"\n[CLEANUP] 🔑 Limpando chaves pendentes...")
        pending_patterns = [
            f"plan_confirm:*:{username}:{projeto}",
            f"user_feedback:*:{username}:{projeto}",
            f"user_proposed_plan:*:{username}:{projeto}",
        ]
        
        for pattern in pending_patterns:
            for key in self.redis_client.scan_iter(match=pattern):
                self.redis_client.delete(key)
                stats['pending_keys_deleted'] += 1
                print(f"[CLEANUP] 🗑️  Deletando chave: {key}")
        
        # 3. DELETAR HISTÓRICO/MEMÓRIA NO REDIS
        print(f"\n[CLEANUP] 💾 Limpando histórico/memória...")
        memory_patterns = [
            f"history:{username}:{projeto}",
            f"memory:{username}:{projeto}",
            f"context:{username}:{projeto}",
            f"chat_history:{username}:{projeto}",
        ]
        
        for pattern in memory_patterns:
            for key in self.redis_client.scan_iter(match=pattern):
                self.redis_client.delete(key)
                stats['memory_keys_deleted'] += 1
                print(f"[CLEANUP] 🗑️  Deletando memória: {key}")
        
        # 4. MARCAR JOBS PARA CANCELAMENTO (jobs em processamento)
        print(f"\n[CLEANUP] 🚫 Marcando jobs em processamento para cancelamento...")
        # Criar chave de cancelamento que os workers irão verificar
        cancel_key = f"cancelled_jobs:{username}:{projeto}"
        
        # Buscar todos os jobs do usuário e adicionar seus IDs à lista de cancelamento
        job_pattern = "job:*"
        cancelled_job_ids = []
        for job_key in self.redis_client.scan_iter(match=job_pattern):
            try:
                job_data = json.loads(self.redis_client.get(job_key))
                if (job_data.get('username') == username and 
                    job_data.get('projeto') == projeto and
                    job_data.get('status') in ['pending', 'processing']):
                    job_id = job_data.get('job_id')
                    cancelled_job_ids.append(job_id)
                    print(f"[CLEANUP] 🚫 Marcando job para cancelamento: {job_id}")
            except:
                continue
        
        # Salvar lista de jobs cancelados no Redis (expira em 60s)
        if cancelled_job_ids:
            self.redis_client.sadd(cancel_key, *cancelled_job_ids)
            self.redis_client.expire(cancel_key, 60)
            print(f"[CLEANUP] 🚫 {len(cancelled_job_ids)} jobs marcados para cancelamento")
        
        # 5. REMOVER JOBS DAS FILAS (previne processamento de jobs antigos)
        print(f"\n[CLEANUP] 📮 Limpando filas...")
        for module in self.connections.keys():
            queue_name = f"queue:{module}"
            queue_length = self.redis_client.llen(queue_name)
            
            if queue_length > 0:
                # Processar cada job na fila
                temp_jobs = []
                for _ in range(queue_length):
                    job_id = self.redis_client.lpop(queue_name)
                    if job_id:
                        # Verificar se o job pertence ao usuário
                        job_key = f"job:{job_id}"
                        job_data_raw = self.redis_client.get(job_key)
                        
                        if job_data_raw:
                            try:
                                job_data = json.loads(job_data_raw)
                                if (job_data.get('username') != username or 
                                    job_data.get('projeto') != projeto):
                                    # Manter jobs de outros usuários
                                    temp_jobs.append(job_id)
                                else:
                                    stats['queue_jobs_removed'] += 1
                                    print(f"[CLEANUP] 🗑️  Removendo job da fila {queue_name}: {job_id}")
                            except json.JSONDecodeError:
                                temp_jobs.append(job_id)
                
                # Re-adicionar jobs que não são do usuário
                for job_id in temp_jobs:
                    self.redis_client.rpush(queue_name, job_id)
        
        # 5. LIMPEZA EXTRA: Remover jobs antigos completados/falhados
        print(f"\n[CLEANUP] 🧹 Limpando jobs antigos completados/falhados...")
        old_jobs_deleted = self.cleanup_old_jobs(max_age_minutes=5)
        stats['old_jobs_deleted'] = old_jobs_deleted
        
        # 6. RESUMO
        print(f"\n{'='*80}")
        print(f"✅ LIMPEZA CONCLUÍDA - {username}/{projeto}")
        print(f"{'='*80}")
        print(f"📊 Estatísticas:")
        print(f"   🗑️  Jobs deletados: {stats['jobs_deleted']}")
        print(f"   🗑️  Branches deletadas: {stats['branches_deleted']}")
        print(f"   🗑️  Chaves pendentes deletadas: {stats['pending_keys_deleted']}")
        print(f"   🗑️  Memória/histórico deletado: {stats['memory_keys_deleted']}")
        print(f"   🗑️  Jobs removidos das filas: {stats['queue_jobs_removed']}")
        print(f"   🗑️  Jobs antigos deletados: {stats['old_jobs_deleted']}")
        print(f"{'='*80}\n")
        
        return stats
    
    def cleanup_old_jobs(self, max_age_minutes: int = 10) -> int:
        """
        Remove jobs completados/falhados mais antigos que max_age_minutes.
        Útil para evitar acúmulo de jobs antigos no Redis.
        
        Args:
            max_age_minutes: Idade máxima dos jobs em minutos (padrão: 10)
            
        Returns:
            Número de jobs deletados
        """
        from datetime import datetime, timedelta
        
        deleted_count = 0
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
        
        print(f"\n🧹 Limpando jobs mais antigos que {max_age_minutes} minutos...")
        
        job_pattern = "job:*"
        for job_key in self.redis_client.scan_iter(match=job_pattern):
            try:
                job_data = json.loads(self.redis_client.get(job_key))
                status = job_data.get('status')
                
                # Só deletar jobs completados ou falhados
                if status in ['completed', 'failed', 'cancelled']:
                    # Verificar timestamp
                    completed_at = job_data.get('completed_at') or job_data.get('failed_at')
                    if completed_at:
                        job_time = datetime.fromisoformat(completed_at)
                        if job_time < cutoff_time:
                            self.redis_client.delete(job_key)
                            deleted_count += 1
                            
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
        
        if deleted_count > 0:
            print(f"✅ {deleted_count} jobs antigos deletados")
        else:
            print(f"✅ Nenhum job antigo para deletar")
        
        return deleted_count
    
    def visualize_graph(self):
        """Mostra estrutura do grafo"""
        print("\n" + "="*80)
        print("📊 ESTRUTURA DO GRAFO (Sistema de Filas)")
        print("="*80 + "\n")
        
        for module, connected_to in self.connections.items():
            print(f"📦 {module}")
            print(f"   📮 Fila: queue:{module}")
            
            if connected_to:
                print(f"   ⬇️  OUTPUT enviado para fila de:")
                for target in connected_to:
                    print(f"      → {target} (queue:{target})")
            else:
                print(f"   🏁 Nó final (sem conexões)")
            print()
        
        # Mostrar status das filas
        queues = self.list_queues()
        print("📊 Status das Filas:")
        for module, size in queues.items():
            status = "🟢" if size == 0 else f"🔴 {size} jobs"
            print(f"   queue:{module} - {status}")
        
        print("\n" + "="*80 + "\n")

# =====================================================
# MODULE WORKER - Base para Workers de Módulos
# =====================================================

class ModuleWorker:
    """
    Worker base que processa jobs de uma fila específica
    Cada módulo deve herdar desta classe
    """
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.redis_client = Redis(**REDIS_CONFIG)
        self.queue_name = f"queue:{module_name}"
        self.connections = GRAPH_CONNECTIONS
        self.running = False
    
    def is_job_cancelled(self, job_id: str, username: str, projeto: str) -> bool:
        """
        Verifica se o job foi cancelado (F5/logout do usuário)
        Workers devem chamar isso ANTES de processar
        """
        cancel_key = f"cancelled_jobs:{username}:{projeto}"
        is_cancelled = self.redis_client.sismember(cancel_key, job_id)
        
        if is_cancelled:
            print(f"[{self.module_name}] 🚫 Job {job_id[:8]}... foi CANCELADO - Pulando processamento")
            # Atualizar status do job para cancelled
            job_key = f"job:{job_id}"
            job_data_raw = self.redis_client.get(job_key)
            if job_data_raw:
                try:
                    job_data = json.loads(job_data_raw)
                    job_data['status'] = 'cancelled'
                    job_data['cancelled_at'] = datetime.now().isoformat()
                    job_data['cancelled_reason'] = 'User logout/refresh'
                    self.redis_client.setex(job_key, 60, json.dumps(job_data))
                except:
                    pass
        
        return is_cancelled
        
    def start(self):
        """Inicia o worker (loop infinito processando fila)"""
        self.running = True
        print(f"\n🚀 Worker {self.module_name} iniciado")
        print(f"   📮 Consumindo fila: {self.queue_name}")
        print(f"   ⬇️  Depositará em: {self.connections.get(self.module_name, [])}")
        print("   ⏳ Aguardando jobs...\n")
        
        while self.running:
            try:
                # Bloqueia até ter um job (timeout 1s)
                result = self.redis_client.blpop(self.queue_name, timeout=1)
                
                if result:
                    _, job_id_bytes = result
                    # Converter bytes para string se necessário
                    job_id = job_id_bytes.decode('utf-8') if isinstance(job_id_bytes, bytes) else job_id_bytes
                    self.process_job(job_id)
                    
            except KeyboardInterrupt:
                print(f"\n⏹️  Worker {self.module_name} parando...")
                self.running = False
            except Exception as e:
                print(f"❌ Erro no worker: {str(e)}")
                time.sleep(1)
    
    def process_job(self, job_id: str):
        """Processa um job"""
        print(f"📍 {self.module_name} processando job {job_id[:8]}...")
        
        # Carregar job
        job_json = self.redis_client.get(f"job:{job_id}")
        if not job_json:
            print(f"   ❌ Job não encontrado")
            return
        
        try:
            job_data = json.loads(job_json)
        except json.JSONDecodeError as e:
            print(f"   ❌ Erro ao decodificar JSON: {e}")
            return
        
        # VERIFICAR SE JOB FOI CANCELADO (status direto)
        if job_data.get('status') == 'cancelled':
            print(f"   🚫 Job cancelado (motivo: {job_data.get('cancelled_reason', 'unknown')}) - pulando processamento")
            return
        
        # VERIFICAR SE JOB ESTÁ NA LISTA DE CANCELAMENTO (F5/logout)
        username = job_data.get('username', 'unknown')
        projeto = job_data.get('projeto', 'default')
        if self.is_job_cancelled(job_id, username, projeto):
            print(f"   🚫 Job {job_id[:8]}... está na lista de cancelamento - pulando")
            return
        
        try:
            start_time = time.time()
            
            # Garantir que data é um dict
            data_input = job_data.get('data', {})
            
            # IMPORTANTE: Adicionar username e projeto ao data_input
            # (necessário para o primeiro módulo que recebe apenas initial_data)
            if 'username' not in data_input:
                data_input['username'] = job_data.get('username', 'unknown')
            if 'projeto' not in data_input:
                data_input['projeto'] = job_data.get('projeto', 'default')
            
            # RASTREIO: Adicionar job_id ao data_input para salvar no banco
            data_input['job_id'] = job_id
            
            # DEBUG: Mostrar o que chegou
            print(f"   🔍 DEBUG: type(data_input) = {type(data_input)}")
            print(f"   🔍 DEBUG: data_input = {data_input}")
            
            # Se data veio como string JSON, decodificar
            if isinstance(data_input, str):
                try:
                    data_input = json.loads(data_input)
                    print(f"   ✓ Decodificado de string para dict")
                except Exception as e:
                    print(f"   ❌ Erro ao decodificar string: {e}")
                    print(f"   ❌ data não é um dict válido: {type(data_input)}")
                    return
            
            # PROCESSAR MÓDULO (implementado pela subclasse)
            try:
                output = self.process(data_input)
            except Exception as e:
                print(f"   ❌ Erro no process(): {e}")
                import traceback
                traceback.print_exc()
                
                # Marcar job como failed
                job_data['status'] = 'failed'
                job_data['error'] = str(e)
                self.redis_client.setex(
                    f"job:{job_id}",
                    3600,
                    json.dumps(job_data)
                )
                return
            
            execution_time = time.time() - start_time
            
            # EXTRAIR _next_modules ANTES de processar o resto
            custom_next_modules = output.pop('_next_modules', None)
            
            print(f"   🔍 DEBUG _next_modules:")
            print(f"      - Existe no output? {custom_next_modules is not None}")
            print(f"      - Valor: {custom_next_modules}")
            
            # Registrar execução
            job_data['execution_chain'].append({
                'module': self.module_name,
                'input': job_data['data'],
                'output': output,
                'execution_time': execution_time,
                'success': True,
                'timestamp': datetime.now().isoformat()
            })
            
            # Atualizar dados para próximo módulo
            job_data['data'] = {
                'username': job_data['username'],
                'projeto': job_data['projeto'],
                'job_id': job_id,  # PRESERVAR job_id para rastreio
                'parent_job_id': job_data.get('parent_job_id'),  # PRESERVAR parent_job_id para FK
                **output  # Output deste módulo
            }
            
            print(f"   ✅ Processado em {execution_time:.2f}s")
            print(f"   📤 Output: {list(output.keys())}")
            
            # Depositar em próximos módulos
            # Verificar se o worker definiu próximos módulos customizados
            if custom_next_modules:
                next_modules = custom_next_modules
                print(f"   🔀 Worker definiu próximos módulos: {next_modules}")
            else:
                next_modules = self.connections.get(self.module_name, [])
            
            if next_modules:
                print(f"   ⬇️  Depositando em: {', '.join(next_modules)}")
                
                # Se múltiplos destinos (paralelo), criar job_id único para cada branch
                if len(next_modules) > 1:
                    for next_module in next_modules:
                        # Criar novo job_id para esta branch
                        branch_job_id = str(uuid.uuid4())
                        
                        # Deep copy do job_data para evitar compartilhamento
                        branch_job_data = deepcopy(job_data)
                        branch_job_data['job_id'] = branch_job_id
                        branch_job_data['parent_job_id'] = job_id
                        branch_job_data['current_module'] = next_module
                        
                        # IMPORTANTE: Adicionar parent_job_id ao data para os workers
                        branch_job_data['data']['parent_job_id'] = job_id
                        
                        # IMPORTANTE: Limpar execution_chain da branch para evitar duplicação
                        # Cada branch terá seu próprio execution_chain independente
                        branch_job_data['execution_chain'] = []
                        
                        # Salvar job da branch
                        self.redis_client.setex(
                            f"job:{branch_job_id}",
                            3600,
                            json.dumps(branch_job_data)
                        )
                        
                        # Adicionar à fila do próximo módulo
                        next_queue = f"queue:{next_module}"
                        self.redis_client.rpush(next_queue, branch_job_id)
                        print(f"   ✓ Branch {branch_job_id[:8]} → {next_queue}")
                    
                    # Marcar job principal como completed (branches criadas com sucesso)
                    job_data['status'] = 'completed'
                    job_data['completed_at'] = datetime.now().isoformat()
                    job_data['note'] = f'Job split into {len(next_modules)} parallel branches'
                    
                    # TTL de 5 minutos para jobs completados (evita acúmulo no Redis)
                    self.redis_client.setex(
                        f"job:{job_id}",
                        300,  # 5 minutos
                        json.dumps(job_data)
                    )
                    
                    print(f"   🔀 Job principal marcado como completed ({len(next_modules)} branches criadas)")
                else:
                    # Um único destino - usar mesmo job_id
                    next_module = next_modules[0]
                    job_data['current_module'] = next_module
                    
                    # Salvar job atualizado
                    self.redis_client.setex(
                        f"job:{job_id}",
                        3600,
                        json.dumps(job_data)
                    )
                    
                    # Adicionar à fila do próximo módulo
                    next_queue = f"queue:{next_module}"
                    self.redis_client.rpush(next_queue, job_id)
                    print(f"   ✓ Job {job_id[:8]} depositado em fila: {next_queue}")
            else:
                # Nó final - marcar como completo
                job_data['status'] = 'completed'
                job_data['completed_at'] = datetime.now().isoformat()
                
                # TTL de 5 minutos para jobs completados (evita acúmulo no Redis)
                self.redis_client.setex(
                    f"job:{job_id}",
                    300,  # 5 minutos
                    json.dumps(job_data)
                )
                
                print(f"   🏁 Job completo - Nó final alcançado")
                
                # Salvar no PostgreSQL

            
            print()
            
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}\n")
            
            job_data['status'] = 'failed'
            job_data['error'] = str(e)
            job_data['failed_at'] = datetime.now().isoformat()
            
            # TTL de 5 minutos para jobs falhados (evita acúmulo no Redis)
            self.redis_client.setex(
                f"job:{job_id}",
                300,  # 5 minutos
                json.dumps(job_data)
            )
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        IMPLEMENTAR ESTE MÉTODO NA SUBCLASSE
        
        Args:
            data: Dados de entrada (output do módulo anterior)
            
        Returns:
            Output do módulo (será input do próximo)
        """
        raise NotImplementedError("Subclasse deve implementar process()")
    
    def _save_to_postgres(self, job_data: Dict):
        """Salva execução completa no PostgreSQL"""
        import requests
        
        try:
            # Construir grafo para Flow Orchestration
            nodes = []
            
            for idx, log in enumerate(job_data['execution_chain']):
                module = log['module']
                node_id = f"{module}_node_{idx}"
                
                # Preparar dados do módulo
                log_data = {
                    "execution_time": log['execution_time'],
                    "success": True,
                    **self._prepare_module_data(module, log['output'], log['input'])
                }
                
                # Determinar conexões
                connected_to = []
                next_modules = self.connections.get(module, [])
                for next_module in next_modules:
                    for future_idx in range(idx + 1, len(job_data['execution_chain'])):
                        if job_data['execution_chain'][future_idx]['module'] == next_module:
                            connected_to.append(f"{next_module}_node_{future_idx}")
                            break
                
                nodes.append({
                    "id": node_id,
                    "module": module,
                    "data": log_data,
                    "connected_to": connected_to
                })
            
            # Enviar para Flow Orchestration
            flow_port = os.getenv('FLOW_ORCHESTRATION_PORT', '5004')
            flow_url = os.getenv('FLOW_ORCHESTRATION_URL', f'http://localhost:{flow_port}')
            response = requests.post(
                f"{flow_url}/execute-flow",
                json={
                    "username": job_data['username'],
                    "projeto": job_data['projeto'],
                    "flow_graph": {"nodes": nodes}
                },
                timeout=30
            )
            
            if response.status_code == 201:
                print(f"   💾 Salvo no PostgreSQL")
            
        except Exception as e:
            print(f"   ⚠️  Erro ao salvar PostgreSQL: {str(e)}")
    
    def _prepare_module_data(self, module: str, output: Dict, input_data: Dict) -> Dict:
        """Prepara dados específicos de cada módulo"""
        
        if module == 'intent_validator':
            return {
                "pergunta": input_data.get('pergunta'),
                "intent_valid": output.get('intent_valid'),
                "intent_category": output.get('intent_category'),
                "intent_reason": output.get('reason'),
                "model_used": output.get('model_used', 'gpt-4o')
            }
        
        elif module == 'history_preferences':
            context = output.get('context', {})
            return {
                "user_preferences": context.get('preferences'),
                "user_patterns": context.get('patterns'),
                "interaction_count": context.get('interaction_count'),
                "context_summary": context.get('context_summary'),
                "relevant_history_found": context.get('relevant_history_found')
            }
        
        return {}

# =====================================================
# FUNÇÕES DE CONVENIÊNCIA
# =====================================================

def visualize():
    """Mostra estrutura do grafo"""
    orchestrator = GraphOrchestrator()
    orchestrator.visualize_graph()

def submit(start_module: str, username: str, projeto: str, **data) -> str:
    """Submete job para processamento"""
    orchestrator = GraphOrchestrator()
    return orchestrator.submit_job(start_module, username, projeto, data)

def status(job_id: str) -> Optional[Dict]:
    """Consulta status de um job"""
    orchestrator = GraphOrchestrator()
    return orchestrator.get_job_status(job_id)

# =====================================================
# EXEMPLO DE USO
# =====================================================

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'viz':
        # Visualizar grafo
        visualize()
    else:
        # Submeter job de teste
        job_id = submit(
            start_module='intent_validator',
            username='joao',
            projeto='ezpag',
            pergunta='quantos pedidos tivemos hoje?'
        )
        
        print(f"\n📋 Para consultar status:")
        print(f"   python graph_orchestrator.py status {job_id}")
