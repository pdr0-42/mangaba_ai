"""
Guardrails for input/output validation in Mangaba AI v3.0
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Type

from pydantic import BaseModel

from mangaba.core.events import EventBus, Event, EventType


class BaseGuardrail(ABC):
    """Abstract guardrail that validates and optionally transforms text."""

    @abstractmethod
    def validate(self, text: str) -> str:
        """Validate *text*. Return the (possibly modified) text or raise ValueError."""
        ...


class LengthGuardrail(BaseGuardrail):
    """Ensures output length is within bounds."""

    def __init__(self, min_length: int = 0, max_length: int = 50_000) -> None:
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, text: str) -> str:
        if len(text) < self.min_length:
            EventBus.emit(Event(event_type=EventType.GUARDRAIL_FAIL, data={"guardrail": "length", "reason": "too_short"}))
            raise ValueError(f"Output too short ({len(text)} < {self.min_length})")
        if len(text) > self.max_length:
            EventBus.emit(Event(event_type=EventType.GUARDRAIL_FAIL, data={"guardrail": "length", "reason": "too_long"}))
            text = text[: self.max_length]
        EventBus.emit(Event(event_type=EventType.GUARDRAIL_PASS, data={"guardrail": "length"}))
        return text


class ContentFilterGuardrail(BaseGuardrail):
    """Block output containing specific patterns."""

    def __init__(self, blocked_patterns: Optional[List[str]] = None) -> None:
        defaults = [
            r'\b(?:password|secret|api[_-]?key)\s*[:=]\s*\S+',
        ]
        self.patterns = [re.compile(p, re.IGNORECASE) for p in (blocked_patterns or defaults)]

    def validate(self, text: str) -> str:
        for pattern in self.patterns:
            if pattern.search(text):
                EventBus.emit(Event(event_type=EventType.GUARDRAIL_FAIL, data={"guardrail": "content_filter"}))
                # Redact matches
                text = pattern.sub("[REDACTED]", text)
        EventBus.emit(Event(event_type=EventType.GUARDRAIL_PASS, data={"guardrail": "content_filter"}))
        return text


class SchemaGuardrail(BaseGuardrail):
    """Validate that output can be parsed into a Pydantic model."""

    def __init__(self, schema: Type[BaseModel]) -> None:
        self.schema = schema

    def validate(self, text: str) -> str:
        import json as _json
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            data = _json.loads(text[start:end])
            self.schema(**data)
            EventBus.emit(Event(event_type=EventType.GUARDRAIL_PASS, data={"guardrail": "schema"}))
            return text
        except Exception as exc:
            EventBus.emit(Event(event_type=EventType.GUARDRAIL_FAIL, data={"guardrail": "schema", "error": str(exc)}))
            raise ValueError(f"Output does not match schema {self.schema.__name__}: {exc}") from exc


class GuardrailChain(BaseGuardrail):
    """Compose multiple guardrails sequentially."""

    def __init__(self, guardrails: List[BaseGuardrail]) -> None:
        self.guardrails = guardrails

    def validate(self, text: str) -> str:
        for g in self.guardrails:
            text = g.validate(text)
        return text
