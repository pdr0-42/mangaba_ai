"""
Task implementation for structured workflow orchestration
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
import uuid

from utils.logger import get_logger


@dataclass
class TaskOutput:
    """Resultado da execução de uma task"""
    description: str
    result: str
    agent: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    success: bool = True
    
    def __str__(self) -> str:
        return self.result


class Task:
    """
    Representa uma tarefa estruturada a ser executada por um agente.
    
    Exemplo:
        task = Task(
            description="Research market trends for {topic}",
            expected_output="A detailed report with 10 key findings",
            agent=researcher_agent,
            context=[previous_task],
            output_file="report.md"
        )
    """
    
    def __init__(
        self,
        description: str,
        expected_output: str,
        agent: Optional['Agent'] = None,
        context: Optional[List['Task']] = None,
        tools: Optional[List['BaseTool']] = None,
        output_file: Optional[str] = None,
        callback: Optional[Callable] = None,
        async_execution: bool = False,
        task_id: Optional[str] = None
    ):
        """
        Inicializa uma Task.
        
        Args:
            description: Descrição detalhada da tarefa (pode usar templates {var})
            expected_output: Descrição do output esperado
            agent: Agente responsável pela execução
            context: Lista de tasks que devem ser executadas antes (dependências)
            tools: Ferramentas específicas para esta task
            output_file: Se especificado, salva o resultado neste arquivo
            callback: Função callback executada após conclusão
            async_execution: Se True, executa de forma assíncrona
            task_id: ID único da task (gerado automaticamente se None)
        """
        if not description or not description.strip():
            raise ValueError("Task description cannot be empty")
        if not expected_output or not expected_output.strip():
            raise ValueError("Expected output cannot be empty")
        
        self.task_id = task_id or f"task_{uuid.uuid4().hex[:8]}"
        self.description = description.strip()
        self.expected_output = expected_output.strip()
        self.agent = agent
        self.context = context or []
        self.tools = tools or []
        self.output_file = output_file
        self.callback = callback
        self.async_execution = async_execution
        
        # Estado da execução
        self.status = "pending"  # pending, running, completed, failed
        self.output: Optional[TaskOutput] = None
        self.error: Optional[str] = None
        
        self.logger = get_logger(f"Task[{self.task_id}]")
    
    def execute(self, inputs: Optional[Dict[str, Any]] = None) -> TaskOutput:
        """
        Executa a task usando o agente designado.
        
        Args:
            inputs: Dicionário com variáveis para substituir na descrição
        
        Returns:
            TaskOutput com o resultado da execução
        """
        if not self.agent:
            raise ValueError("No agent assigned to this task")
        
        self.status = "running"
        self.logger.info(f"▶️ Starting task execution")
        
        try:
            # Processa template na descrição
            task_description = self._process_template(self.description, inputs or {})
            
            # Coleta contexto de tasks anteriores
            context_str = self._build_context()
            
            # Executa a task
            result = self.agent.execute_task(
                task_description=task_description,
                context=context_str
            )
            
            # Cria output
            self.output = TaskOutput(
                description=task_description,
                result=result,
                agent=self.agent.role,
                success=True
            )
            
            # Salva em arquivo se especificado
            if self.output_file:
                self._save_to_file(result)
            
            # Executa callback se definido
            if self.callback:
                self.callback(self.output)
            
            self.status = "completed"
            self.logger.info(f"✅ Task completed successfully")
            
            return self.output
            
        except Exception as e:
            self.status = "failed"
            self.error = str(e)
            self.logger.error(f"❌ Task failed: {e}")
            
            self.output = TaskOutput(
                description=self.description,
                result=f"Error: {str(e)}",
                agent=self.agent.role if self.agent else "unknown",
                success=False
            )
            
            raise
    
    def _process_template(self, text: str, inputs: Dict[str, Any]) -> str:
        """
        Processa templates tipo {variable} na descrição.
        """
        result = text
        for key, value in inputs.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    def _build_context(self) -> str:
        """
        Constrói string de contexto a partir de tasks anteriores.
        """
        if not self.context:
            return ""
        
        context_parts = []
        for task in self.context:
            if task.output:
                context_parts.append(f"Previous task: {task.description}")
                context_parts.append(f"Result: {task.output.result}")
                context_parts.append("---")
        
        return "\n".join(context_parts)
    
    def _save_to_file(self, content: str):
        """
        Salva o resultado em arquivo.
        """
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            self.logger.info(f"💾 Output saved to {self.output_file}")
        except Exception as e:
            self.logger.error(f"❌ Failed to save output: {e}")
    
    def __repr__(self) -> str:
        agent_name = self.agent.role if self.agent else "unassigned"
        return f"Task(description='{self.description[:50]}...', agent='{agent_name}', status='{self.status}')"
