"""
Core type definitions for Mangaba AI v3.0

Pydantic v2 models used across the entire framework for validation,
serialization, and JSON schema generation.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Role(str, Enum):
    """Message role in a conversation.

    Defines who sent a message in a chat conversation:
    - SYSTEM: System instructions/prompt
    - USER: Human user input
    - ASSISTANT: AI agent response
    - TOOL: Tool execution result
    """
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class AgentStatus(str, Enum):
    """Current execution status of an agent.

    - IDLE: Agent is not currently executing any task
    - RUNNING: Agent is actively processing a task
    - WAITING_TOOL: Agent is waiting for a tool to complete
    - COMPLETED: Agent successfully finished the task
    - ERROR: Agent encountered an error during execution
    """
    IDLE = "idle"
    RUNNING = "running"
    WAITING_TOOL = "waiting_tool"
    COMPLETED = "completed"
    ERROR = "error"


class TaskStatus(str, Enum):
    """Execution status of a task.

    - PENDING: Task is queued and waiting to start
    - RUNNING: Task is currently being executed
    - COMPLETED: Task finished successfully
    - FAILED: Task failed with an error
    - SKIPPED: Task was skipped (e.g., due to conditional logic)
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class FinishReason(str, Enum):
    """Reason why an LLM stopped generating.

    - STOP: Model naturally stopped generation
    - TOOL_CALLS: Model stopped to request tool calls
    - LENGTH: Model hit max token limit
    - ERROR: Generation failed due to an error
    - CONTENT_FILTER: Content was blocked by safety filters
    """
    STOP = "stop"
    TOOL_CALLS = "tool_calls"
    LENGTH = "length"
    ERROR = "error"
    CONTENT_FILTER = "content_filter"


# ---------------------------------------------------------------------------
# LLM related
# ---------------------------------------------------------------------------


class LLMConfig(BaseModel):
    """Configuration for an LLM provider.

    Attributes:
        provider: LLM provider name (e.g., 'openai', 'anthropic', 'google').
        model: Model name or list of models for fallback (for OpenRouter).
        api_key: API key for the provider (can be None if from env var).
        temperature: Sampling temperature (0.0 to 2.0, default 0.7).
        max_tokens: Maximum tokens in response (default 1024).
        top_p: Nucleus sampling parameter (0.0 to 1.0, default 1.0).
        stop_sequences: Optional list of sequences that stop generation.
        timeout: Request timeout in seconds (default 60).
        base_url: Optional custom API base URL.
    """

    provider: str = "google"
    model: Union[str, List[str]] = "gemini-2.5-flash"
    api_key: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    stop_sequences: Optional[List[str]] = None
    timeout: int = Field(default=60, ge=1)
    base_url: Optional[str] = None

    @field_validator("provider")
    @classmethod
    def normalize_provider(cls, v: str) -> str:
        """Normalize provider name by resolving aliases.

        Args:
            v: Provider name or alias.

        Returns:
            Normalized provider name.
        """
        aliases = {
            "gemini": "google",
            "google-ai": "google",
            "googleai": "google",
            "gpt": "openai",
            "chatgpt": "openai",
            "claude": "anthropic",
            "hf": "huggingface",
            "hugging-face": "huggingface",
            "openrouter": "openrouter",
            "open-router": "openrouter",
            "or": "openrouter",
        }
        return aliases.get(v.lower(), v.lower())


class OpenRouterConfig(LLMConfig):
    """Specialized configuration for OpenRouter with fallback support.

    Extends LLMConfig to support OpenRouter's multi-model fallback
    routing and custom headers.

    Attributes:
        provider: Always 'openrouter'.
        model: List of models for fallback routing (primary first).
        site_name: Application name for OpenRouter headers.
        site_url: Application URL for OpenRouter headers.
        route: Optional routing preference (cheap, fast, etc).
    """

    provider: str = "openrouter"

    # We can define a default fallback list here
    model: List[str] = Field(
        default_factory=lambda: [
            "google/gemini-2.5-flash",
            "anthropic/claude-3.5-sonnet",
        ]
    )

    # Specific OpenRouter headers
    site_name: str = "Mangaba AI"
    site_url: str = "https://www.mangaba.ia.br/"

    # OpenRouter routing preferences (cheap, fast, etc)
    route: Optional[str] = None


class TokenUsage(BaseModel):
    """Token usage statistics from an LLM call.

    Attributes:
        prompt_tokens: Number of tokens in the prompt.
        completion_tokens: Number of tokens in the completion.
        total_tokens: Total tokens used (prompt + completion).
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ToolCall(BaseModel):
    """A tool call requested by the LLM.

    Attributes:
        id: Unique identifier for this tool call.
        tool_name: Name of the tool to call.
        arguments: Dictionary of arguments to pass to the tool.
    """

    id: str = Field(default_factory=lambda: f"call_{uuid.uuid4().hex[:12]}")
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Result from executing a tool.

    Attributes:
        call_id: ID of the tool call this result corresponds to.
        tool_name: Name of the tool that was executed.
        output: The output from the tool execution.
        error: Error message if execution failed.
        success: Whether the tool execution succeeded.
    """

    call_id: str
    tool_name: str = ""
    output: Any = None
    error: Optional[str] = None
    success: bool = True


class Message(BaseModel):
    """A single message in a conversation.

    Attributes:
        role: The role of the message sender (SYSTEM, USER, ASSISTANT, TOOL).
        content: The text content of the message.
        tool_calls: List of tool calls requested by the assistant.
        tool_results: List of tool execution results.
        metadata: Additional metadata about the message.
        timestamp: ISO format timestamp of when the message was created.
    """

    role: Role
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_results: Optional[List[ToolResult]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

    @classmethod
    def system(cls, content: str) -> Message:
        """Create a system message.

        Args:
            content: The system instruction content.

        Returns:
            A Message with role=SYSTEM.
        """
        return cls(role=Role.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str) -> Message:
        """Create a user message.

        Args:
            content: The user's input content.

        Returns:
            A Message with role=USER.
        """
        return cls(role=Role.USER, content=content)

    @classmethod
    def assistant(
        cls, content: Optional[str] = None, tool_calls: Optional[List[ToolCall]] = None
    ) -> Message:
        """Create an assistant message.

        Args:
            content: The assistant's response content.
            tool_calls: Optional tool calls requested by the assistant.

        Returns:
            A Message with role=ASSISTANT.
        """
        return cls(role=Role.ASSISTANT, content=content, tool_calls=tool_calls)

    @classmethod
    def tool(cls, results: List[ToolResult]) -> Message:
        """Create a tool result message.

        Args:
            results: List of tool execution results.

        Returns:
            A Message with role=TOOL containing tool results.
        """
        return cls(role=Role.TOOL, tool_results=results)


class LLMResponse(BaseModel):
    """Standardised response from any LLM provider.

    Attributes:
        content: The text content of the response.
        tool_calls: List of tool calls requested by the LLM.
        usage: Token usage statistics.
        model: The model that generated the response.
        finish_reason: Why the LLM stopped generating.
        raw: Raw response object from the provider (excluded from serialization).
    """

    content: Optional[str] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)
    usage: TokenUsage = Field(default_factory=TokenUsage)
    model: str = ""
    finish_reason: FinishReason = FinishReason.STOP
    raw: Any = Field(default=None, exclude=True)

    @property
    def text(self) -> str:
        """Get the text content, defaulting to empty string.

        Returns:
            The content as a string, or empty string if content is None.
        """
        return self.content or ""

    @property
    def has_tool_calls(self) -> bool:
        """Check if the response contains tool calls.

        Returns:
            True if there are tool calls, False otherwise.
        """
        return len(self.tool_calls) > 0


# ---------------------------------------------------------------------------
# Agent / Task / Crew configuration
# ---------------------------------------------------------------------------


class MemoryConfig(BaseModel):
    """Memory configuration for an agent.

    Attributes:
        short_term: Enable short-term memory (in-conversation context).
        long_term: Enable long-term persistent memory storage.
        entity: Enable entity extraction and tracking.
        max_short_term_items: Maximum items in short-term memory.
        storage_path: Optional path for persistent storage.
    """

    short_term: bool = True
    long_term: bool = False
    entity: bool = False
    max_short_term_items: int = Field(default=50, ge=1)
    storage_path: Optional[str] = None


class AgentConfig(BaseModel):
    """Full configuration for an Agent.

    Attributes:
        role: The agent's role/profession.
        goal: The agent's primary objective.
        backstory: Context and background about the agent.
        llm_config: Optional LLM provider configuration.
        tools: List of tool names available to the agent.
        memory_config: Memory configuration for the agent.
        max_iterations: Maximum ReAct reasoning loop iterations.
        max_retry_on_error: Maximum retry attempts on errors.
        verbose: Enable verbose logging.
        allow_delegation: Allow agent to delegate to other agents.
        step_callback: Optional callback function for each step.
        guardrails: List of guardrail names to apply.
        output_parser: Optional output parser name to use.
    """

    role: str
    goal: str
    backstory: str
    llm_config: Optional[LLMConfig] = None
    tools: List[str] = Field(default_factory=list)
    memory_config: MemoryConfig = Field(default_factory=MemoryConfig)
    max_iterations: int = Field(default=15, ge=1)
    max_retry_on_error: int = Field(default=3, ge=0)
    verbose: bool = False
    allow_delegation: bool = True
    step_callback: Optional[str] = None
    guardrails: List[str] = Field(default_factory=list)
    output_parser: Optional[str] = None

    @field_validator("role", "goal", "backstory")
    @classmethod
    def not_empty(cls, v: str) -> str:
        """Validate that string fields are not empty or whitespace-only.

        Args:
            v: The string value to validate.

        Returns:
            The stripped string value.

        Raises:
            ValueError: If the string is empty or whitespace-only.
        """
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class TaskConfig(BaseModel):
    """Full configuration for a Task.

    Attributes:
        description: What the task should accomplish.
        expected_output: Expected format of the task output.
        agent_id: Optional ID of the agent assigned to this task.
        context_ids: List of context IDs to include as input.
        tools: List of tool names available for this task.
        output_file: Optional file path to save output to.
        async_execution: Whether the task should run asynchronously.
        human_input: Whether human input is required during execution.
        guardrails: List of guardrail names to apply.
        output_parser: Optional output parser name to use.
        retry_on_failure: Number of retries on failure (0 = no retry).
    """

    description: str
    expected_output: str
    agent_id: Optional[str] = None
    context_ids: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    output_file: Optional[str] = None
    async_execution: bool = False
    human_input: bool = False
    guardrails: List[str] = Field(default_factory=list)
    output_parser: Optional[str] = None
    retry_on_failure: int = Field(default=0, ge=0)

    @field_validator("description", "expected_output")
    @classmethod
    def not_empty(cls, v: str) -> str:
        """Validate that string fields are not empty or whitespace-only.

        Args:
            v: The string value to validate.

        Returns:
            The stripped string value.

        Raises:
            ValueError: If the string is empty or whitespace-only.
        """
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


# ---------------------------------------------------------------------------
# Agent runtime state
# ---------------------------------------------------------------------------


class ReActStep(BaseModel):
    """A single step in the ReAct reasoning loop.

    Represents one iteration of the Thought-Action-Observation cycle:
    - Thought: What the agent is thinking
    - Action: What tool the agent decides to use
    - Observation: The result from the tool execution

    Attributes:
        step_number: The step number in the reasoning sequence.
        thought: The agent's reasoning at this step.
        action: The tool call (if any) made at this step.
        observation: The result from tool execution (if any).
        timestamp: ISO format timestamp of when this step occurred.
    """

    step_number: int
    thought: Optional[str] = None
    action: Optional[ToolCall] = None
    observation: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class AgentState(BaseModel):
    """Runtime state of an agent during task execution.

    Tracks the agent's progress, conversation history, and reasoning steps
    throughout the execution of a task.

    Attributes:
        agent_id: Unique identifier for the agent.
        messages: Complete conversation history including all messages.
        steps: List of ReAct reasoning steps taken so far.
        current_step: Current step number in the reasoning sequence.
        iteration_count: Total number of iterations completed.
        status: Current execution status of the agent.
        metadata: Additional runtime information.
    """

    agent_id: str
    messages: List[Message] = Field(default_factory=list)
    steps: List[ReActStep] = Field(default_factory=list)
    current_step: int = 0
    iteration_count: int = 0
    status: AgentStatus = AgentStatus.IDLE
    metadata: Dict[str, Any] = Field(default_factory=dict)
