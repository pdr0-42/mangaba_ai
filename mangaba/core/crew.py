"""
Crew implementation for multi-agent orchestration
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from mangaba.core.agent import Agent
from mangaba.core.task import Task, TaskOutput
from utils.logger import get_logger


class Process(Enum):
    """Processos de execução disponíveis para Crews"""
    SEQUENTIAL = "sequential"      # Tarefas executadas em sequência
    HIERARCHICAL = "hierarchical"  # Com gerente delegando tarefas
    PARALLEL = "parallel"          # Tarefas executadas em paralelo (futuro)
    CONSENSUAL = "consensual"      # Decisões por consenso (futuro)


class CrewOutput:
    """Resultado da execução de um Crew"""
    
    def __init__(
        self,
        tasks_outputs: List[TaskOutput],
        process: Process,
        duration: float,
        crew_id: str
    ):
        self.tasks_outputs = tasks_outputs
        self.process = process
        self.duration = duration
        self.crew_id = crew_id
        self.timestamp = datetime.now().isoformat()
    
    @property
    def final_output(self) -> str:
        """Retorna o output da última task executada"""
        if self.tasks_outputs:
            return self.tasks_outputs[-1].result
        return ""
    
    def __str__(self) -> str:
        return self.final_output


class Crew:
    """
    Coordena a execução de múltiplos agentes trabalhando em conjunto.
    
    Exemplo:
        crew = Crew(
            agents=[researcher, analyst, writer],
            tasks=[research_task, analyze_task, write_task],
            process=Process.SEQUENTIAL,
            verbose=True
        )
        
        result = crew.kickoff(inputs={"topic": "AI trends"})
    """
    
    def __init__(
        self,
        agents: List[Agent],
        tasks: List[Task],
        process: Process = Process.SEQUENTIAL,
        verbose: bool = False,
        max_rpm: Optional[int] = None,
        crew_id: Optional[str] = None
    ):
        """
        Inicializa um Crew.
        
        Args:
            agents: Lista de agentes disponíveis
            tasks: Lista de tasks a executar
            process: Processo de execução (SEQUENTIAL ou HIERARCHICAL)
            verbose: Se True, imprime logs detalhados
            max_rpm: Taxa máxima de requisições por minuto (rate limiting)
            crew_id: ID único do crew (gerado automaticamente se None)
        """
        if not agents:
            raise ValueError("Crew must have at least one agent")
        if not tasks:
            raise ValueError("Crew must have at least one task")
        
        self.crew_id = crew_id or f"crew_{uuid.uuid4().hex[:8]}"
        self.agents = agents
        self.tasks = tasks
        self.process = process
        self.verbose = verbose
        self.max_rpm = max_rpm
        
        self.logger = get_logger(f"Crew[{self.crew_id}]")
        
        # Validações
        self._validate_setup()
        
        # Conecta agentes via A2A
        self._connect_agents()
        
        if self.verbose:
            self.logger.info(f"✅ Crew initialized")
            self.logger.info(f"   Agents: {len(self.agents)}")
            self.logger.info(f"   Tasks: {len(self.tasks)}")
            self.logger.info(f"   Process: {self.process.value}")
    
    def _validate_setup(self):
        """Valida a configuração do crew"""
        # Verifica se todas as tasks têm agentes atribuídos
        for task in self.tasks:
            if not task.agent:
                raise ValueError(f"Task '{task.description[:50]}...' has no agent assigned")
            
            # Verifica se o agente está na lista
            if task.agent not in self.agents:
                raise ValueError(
                    f"Task agent '{task.agent.role}' is not in the crew's agent list"
                )
        
        # Verifica dependências de contexto
        for task in self.tasks:
            for context_task in task.context:
                if context_task not in self.tasks:
                    raise ValueError(
                        f"Task has dependency on a task not in the crew"
                    )
    
    def _connect_agents(self):
        """Conecta todos os agentes via protocolo A2A"""
        for i, agent1 in enumerate(self.agents):
            for agent2 in self.agents[i+1:]:
                agent1.connect_to(agent2)
                
        if self.verbose:
            self.logger.info(f"🔗 Connected {len(self.agents)} agents via A2A")
    
    def kickoff(self, inputs: Optional[Dict[str, Any]] = None) -> CrewOutput:
        """
        Inicia a execução do crew.
        
        Args:
            inputs: Dicionário com variáveis para substituir nas tasks
        
        Returns:
            CrewOutput com resultados de todas as tasks
        """
        start_time = datetime.now()
        
        if self.verbose:
            self.logger.info(f"🚀 Starting crew execution with {self.process.value} process")
        
        try:
            if self.process == Process.SEQUENTIAL:
                outputs = self._run_sequential(inputs or {})
            elif self.process == Process.HIERARCHICAL:
                outputs = self._run_hierarchical(inputs or {})
            else:
                raise NotImplementedError(f"Process {self.process.value} not yet implemented")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            crew_output = CrewOutput(
                tasks_outputs=outputs,
                process=self.process,
                duration=duration,
                crew_id=self.crew_id
            )
            
            if self.verbose:
                self.logger.info(f"✅ Crew execution completed in {duration:.2f}s")
            
            return crew_output
            
        except Exception as e:
            self.logger.error(f"❌ Crew execution failed: {e}")
            raise
    
    def _run_sequential(self, inputs: Dict[str, Any]) -> List[TaskOutput]:
        """
        Executa tasks em sequência.
        """
        outputs = []
        
        for i, task in enumerate(self.tasks, 1):
            if self.verbose:
                self.logger.info(f"📝 Executing task {i}/{len(self.tasks)}: {task.description[:60]}...")
            
            try:
                output = task.execute(inputs)
                outputs.append(output)
                
                # Adiciona output ao contexto para próximas tasks
                # (já gerenciado pelo sistema de contexto das tasks)
                
            except Exception as e:
                self.logger.error(f"❌ Task {i} failed: {e}")
                raise
        
        return outputs
    
    def _run_hierarchical(self, inputs: Dict[str, Any]) -> List[TaskOutput]:
        """
        Executa com processo hierárquico (com gerente).
        
        O primeiro agente atua como gerente, delegando tasks aos demais.
        """
        if len(self.agents) < 2:
            raise ValueError("Hierarchical process requires at least 2 agents (1 manager + workers)")
        
        manager = self.agents[0]
        workers = self.agents[1:]
        
        if self.verbose:
            self.logger.info(f"👔 Manager: {manager.role}")
            self.logger.info(f"👷 Workers: {[w.role for w in workers]}")
        
        outputs = []
        
        # Manager planeja e delega
        for i, task in enumerate(self.tasks, 1):
            if self.verbose:
                self.logger.info(f"📋 Manager delegating task {i}/{len(self.tasks)}")
            
            # Manager revisa a task e delega
            delegation_prompt = f"""
            As the manager, review and potentially refine this task before delegation:
            
            Task: {task.description}
            Expected Output: {task.expected_output}
            Assigned Worker: {task.agent.role}
            
            Provide refined instructions for the worker to execute this task effectively.
            """
            
            refined_instructions = manager.execute_task(delegation_prompt)
            
            # Worker executa com instruções refinadas
            worker_prompt = f"{refined_instructions}\n\nOriginal task: {task.description}"
            
            original_desc = task.description
            task.description = worker_prompt
            
            try:
                output = task.execute(inputs)
                outputs.append(output)
                
                # Manager revisa o resultado
                review_prompt = f"""
                Review the worker's output for this task:
                
                Task: {original_desc}
                Worker: {task.agent.role}
                Output: {output.result}
                
                Is this satisfactory? Provide approval or request revisions.
                """
                
                review = manager.execute_task(review_prompt)
                
                if self.verbose:
                    self.logger.info(f"👔 Manager review: {review[:100]}...")
                
            finally:
                task.description = original_desc
        
        return outputs
    
    def __repr__(self) -> str:
        return f"Crew(agents={len(self.agents)}, tasks={len(self.tasks)}, process={self.process.value})"
