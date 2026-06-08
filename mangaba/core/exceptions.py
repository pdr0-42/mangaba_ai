"""
Exception hierarchy for Mangaba AI v3.0

Typed exceptions for each subsystem, enabling granular error handling
and automatic retry of transient failures.
"""

from __future__ import annotations

from typing import Optional


class MangabaError(Exception):
    """Base exception for all Mangaba errors.

    All custom exceptions in the framework inherit from this class,
    enabling granular error handling and catching of framework-specific errors.

    Attributes:
        cause: Optional original exception that caused this error.
    """

    def __init__(self, message: str, *, cause: Optional[Exception] = None) -> None:
        """Initialize the base Mangaba error.

        Args:
            message: Human-readable error message.
            cause: Optional original exception that caused this error.

        Attributes:
            cause: The original exception if provided.
        """
        self.cause = cause
        super().__init__(message)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class ConfigurationError(MangabaError):
    """Invalid or missing configuration.

    Raised when required configuration values are missing, invalid,
    or cannot be loaded from environment variables or config files.
    """


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------


class LLMError(MangabaError):
    """Generic LLM provider error.

    Base class for all LLM-related errors including authentication,
    rate limiting, token limits, and content filtering issues.
    """


class AuthenticationError(LLMError):
    """Invalid or expired API key.

    Raised when the API key provided to an LLM provider is invalid,
    expired, or does not have sufficient permissions.
    """


class RetryableError(LLMError):
    """Transient error that may succeed on retry.

    Indicates a temporary failure (network issues, timeout, service unavailable)
    that may resolve if the request is retried with backoff.
    """


class RateLimitError(RetryableError):
    """Provider rate-limit hit.

    Raised when the LLM provider's rate limit has been exceeded.
    Includes optional retry_after information for backoff timing.

    Attributes:
        retry_after: Optional seconds to wait before retrying.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: Optional[float] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize the rate limit error.

        Args:
            message: Human-readable error message.
            retry_after: Optional seconds to wait before retrying.
            cause: Optional original exception that caused this error.

        Attributes:
            retry_after: The suggested retry delay in seconds.
        """
        self.retry_after = retry_after
        super().__init__(message, cause=cause)


class TokenLimitError(LLMError):
    """Prompt or response exceeds token limit.

    Raised when the combined prompt and response would exceed the
    model's maximum token context window.
    """


class ContentFilterError(LLMError):
    """Content blocked by safety filter.

    Raised when the LLM provider's content moderation system
    blocks the input or output for policy violations.
    """


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


class ToolError(MangabaError):
    """Error during tool execution.

    Base class for errors that occur when executing tools,
    including validation failures and execution errors.

    Attributes:
        tool_name: Name of the tool that caused the error.
    """

    def __init__(
        self,
        message: str,
        *,
        tool_name: str = "",
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize the tool error.

        Args:
            message: Human-readable error message.
            tool_name: Name of the tool that caused the error.
            cause: Optional original exception that caused this error.

        Attributes:
            tool_name: The name of the tool that caused the error.
        """
        self.tool_name = tool_name
        super().__init__(message, cause=cause)


class ToolValidationError(ToolError):
    """Tool input validation failed.

    Raised when the provided input parameters do not match
    the tool's expected schema or type constraints.
    """


class ToolNotFoundError(ToolError):
    """Requested tool does not exist.

    Raised when attempting to use a tool that has not been
    registered or is not available to the agent.
    """


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class AgentError(MangabaError):
    """Error in agent execution.

    Base class for errors that occur during agent operations,
    including iteration limits, delegation failures, and execution errors.
    """


class MaxIterationsError(AgentError):
    """Agent hit the maximum iteration limit.

    Raised when the ReAct reasoning loop exceeds the configured
    max_iterations without reaching a final answer.
    """


class DelegationError(AgentError):
    """Failed to delegate task to another agent.

    Raised when an agent attempts to delegate a task but the delegation
    cannot be completed (e.g., no suitable delegate agent available).
    """


# ---------------------------------------------------------------------------
# Task / Crew
# ---------------------------------------------------------------------------


class TaskError(MangabaError):
    """Error during task execution.

    Raised when a task cannot be completed successfully,
    including agent failures, timeout, or execution errors.
    """


class CrewError(MangabaError):
    """Error in crew orchestration.

    Raised when errors occur during crew-level operations such as
    process execution, agent coordination, or task distribution.
    """


class ValidationError(MangabaError):
    """Generic data validation failure.

    Raised when input data fails validation checks, including
    schema validation, type mismatches, or constraint violations.
    """


# ---------------------------------------------------------------------------
# Memory / RAG
# ---------------------------------------------------------------------------


class MemoryError(MangabaError):
    """Error in memory subsystem.

    Raised when errors occur in memory operations such as storage,
    retrieval, or search in short-term or long-term memory systems.
    """


class EmbeddingError(MangabaError):
    """Error computing embeddings.

    Raised when the embedding model fails to generate embeddings
    for text, due to model errors, API issues, or invalid input.
    """


class VectorStoreError(MangabaError):
    """Error in vector storage subsystem.

    Raised when errors occur in vector database operations such as
    insertion, search, or deletion of vector embeddings.
    """
