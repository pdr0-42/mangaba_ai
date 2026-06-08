"""
Guardrails for input/output validation in Mangaba AI v3.0
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import List, Optional, Type

from pydantic import BaseModel

from mangaba.core.events import EventBus, Event, EventType


class BaseGuardrail(ABC):
    """Abstract guardrail that validates and optionally transforms text.

    Guardrails are validation rules that can be applied to agent inputs
    or outputs to ensure they meet certain criteria (length, content filters,
    schema validation, etc.).

    Subclasses must implement the validate() method.
    """

    @abstractmethod
    def validate(self, text: str) -> str:
        """Validate text and optionally transform it.

        Args:
            text: The text to validate.

        Returns:
            The validated (and possibly modified) text.

        Raises:
            ValueError: If the text fails validation.
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError("validate() must be implemented")


class LengthGuardrail(BaseGuardrail):
    """Ensures output length is within bounds.

    Validates that text length is between min_length and max_length.
    If text is too long, it is truncated to max_length.
    """

    def __init__(self, min_length: int = 0, max_length: int = 50_000) -> None:
        """Initialize the length guardrail.

        Args:
            min_length: Minimum allowed length (default 0).
            max_length: Maximum allowed length (default 50,000).
        """
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, text: str) -> str:
        """Validate text length and truncate if too long.

        Args:
            text: The text to validate.

        Returns:
            The validated text, truncated if too long.

        Raises:
            ValueError: If text is shorter than min_length.
        """
        if len(text) < self.min_length:
            EventBus.emit(
                Event(
                    event_type=EventType.GUARDRAIL_FAIL,
                    data={"guardrail": "length", "reason": "too_short"},
                )
            )
            raise ValueError(f"Output too short ({len(text)} < {self.min_length})")
        if len(text) > self.max_length:
            EventBus.emit(
                Event(
                    event_type=EventType.GUARDRAIL_FAIL,
                    data={"guardrail": "length", "reason": "too_long"},
                )
            )
            text = text[: self.max_length]
        EventBus.emit(
            Event(event_type=EventType.GUARDRAIL_PASS, data={"guardrail": "length"})
        )
        return text


class ContentFilterGuardrail(BaseGuardrail):
    """Block output containing specific patterns.

    Scans text for regex patterns (e.g., passwords, API keys) and
    redacts any matches with [REDACTED].
    """

    def __init__(self, blocked_patterns: Optional[List[str]] = None) -> None:
        """Initialize the content filter guardrail.

        Args:
            blocked_patterns: Optional list of regex patterns to block.
                Defaults to common sensitive patterns (passwords, API keys).
        """
        defaults = [
            r"\b(?:password|secret|api[_-]?key)\s*[:=]\s*\S+",
        ]
        self.patterns = [
            re.compile(p, re.IGNORECASE) for p in (blocked_patterns or defaults)
        ]

    def validate(self, text: str) -> str:
        """Validate text and redact any blocked patterns.

        Args:
            text: The text to validate.

        Returns:
            The text with any blocked patterns redacted.
        """
        for pattern in self.patterns:
            if pattern.search(text):
                EventBus.emit(
                    Event(
                        event_type=EventType.GUARDRAIL_FAIL,
                        data={"guardrail": "content_filter"},
                    )
                )
                # Redact matches
                text = pattern.sub("[REDACTED]", text)
        EventBus.emit(
            Event(
                event_type=EventType.GUARDRAIL_PASS,
                data={"guardrail": "content_filter"},
            )
        )
        return text


class SchemaGuardrail(BaseGuardrail):
    """Validate that output can be parsed into a Pydantic model.

    Extracts JSON from the text and validates it against the provided
    Pydantic schema, raising an error if validation fails.
    """

    def __init__(self, schema: Type[BaseModel]) -> None:
        """Initialize the schema guardrail.

        Args:
            schema: The Pydantic model class to validate against.
        """
        self.schema = schema

    def validate(self, text: str) -> str:
        """Validate text can be parsed into the Pydantic schema.

        Args:
            text: The text to validate.

        Returns:
            The original text if validation succeeds.

        Raises:
            ValueError: If the text cannot be parsed or doesn't match the schema.
        """
        import json as _json

        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            data = _json.loads(text[start:end])
            self.schema(**data)
            EventBus.emit(
                Event(event_type=EventType.GUARDRAIL_PASS, data={"guardrail": "schema"})
            )
            return text
        except Exception as exc:
            EventBus.emit(
                Event(
                    event_type=EventType.GUARDRAIL_FAIL,
                    data={"guardrail": "schema", "error": str(exc)},
                )
            )
            raise ValueError(
                f"Output does not match schema {self.schema.__name__}: {exc}"
            ) from exc


class GuardrailChain(BaseGuardrail):
    """Compose multiple guardrails sequentially.

    Applies a chain of guardrails in order, passing the output of each
    as input to the next. Useful for combining multiple validation rules.
    """

    def __init__(self, guardrails: List[BaseGuardrail]) -> None:
        """Initialize the guardrail chain.

        Args:
            guardrails: List of guardrails to apply in sequence.
        """
        self.guardrails = guardrails

    def validate(self, text: str) -> str:
        """Apply all guardrails in sequence.

        Args:
            text: The text to validate.

        Returns:
            The text after passing through all guardrails.

        Raises:
            ValueError: If any guardrail in the chain fails validation.
        """
        for g in self.guardrails:
            text = g.validate(text)
        return text
