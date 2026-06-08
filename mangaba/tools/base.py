"""
Tool system for Mangaba AI v3.0

Professional tool abstraction with Pydantic-based input validation,
automatic JSON schema generation for LLM function calling, and
support for both sync and async execution.
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

from mangaba.core.events import EventBus, Event, EventType


class EmptyInput(BaseModel):
    """Default input schema when a tool takes no structured input."""

    pass


class BaseTool(ABC):
    """Base class for all Mangaba tools.

    Provides a professional tool abstraction with Pydantic-based input
    validation, automatic JSON schema generation for LLM function calling,
    and support for both sync and async execution.

    Subclasses must:
        - Set ``name`` and ``description`` as class attributes
        - Optionally set ``args_schema`` to a Pydantic model describing inputs
        - Implement ``_run(**kwargs)``

    Example::

        class SearchTool(BaseTool):
            name = "web_search"
            description = "Search the web for current information"
            args_schema = SearchInput  # Pydantic model

            def _run(self, query: str, max_results: int = 5) -> str:
                ...

    Attributes:
        name: The tool's name identifier.
        description: Description of what the tool does.
        args_schema: Optional Pydantic model for input validation.
        return_direct: Whether to return output directly to the user.
    """

    name: str = "base_tool"
    description: str = "Base tool"
    args_schema: Optional[Type[BaseModel]] = None
    return_direct: bool = False

    # -- public API ----------------------------------------------------------

    def run(self, **kwargs: Any) -> Any:
        """Validate inputs and execute the tool.

        Args:
            **kwargs: Input arguments for the tool.

        Returns:
            The tool's execution result.

        Raises:
            Exception: If tool execution fails.
        """
        validated = self._validate_input(kwargs)
        EventBus.emit(
            Event(
                event_type=EventType.TOOL_START,
                data={
                    "tool": self.name,
                    "args": {k: str(v)[:200] for k, v in validated.items()},
                },
            )
        )
        try:
            result = self._run(**validated)
            EventBus.emit(
                Event(
                    event_type=EventType.TOOL_END,
                    data={"tool": self.name, "result_preview": str(result)[:200]},
                )
            )
            return result
        except Exception as exc:
            EventBus.emit(
                Event(
                    event_type=EventType.TOOL_ERROR,
                    data={"tool": self.name, "error": str(exc)},
                )
            )
            raise

    @abstractmethod
    def _run(self, **kwargs: Any) -> Any:
        """Tool-specific implementation. Override in subclasses.

        Args:
            **kwargs: Validated input arguments.

        Returns:
            The tool's result.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        ...

    # -- schema / function calling helpers -----------------------------------

    def get_function_schema(self) -> Dict[str, Any]:
        """Return a JSON-schema representation for LLM function calling.

        Returns:
            Dictionary containing the function name, description, and parameters schema.
        """
        if self.args_schema is not None:
            params = self.args_schema.model_json_schema()
            # Remove the title to keep it concise
            params.pop("title", None)
        else:
            # Auto-detect from _run signature
            params = self._schema_from_signature()
        return {
            "name": self.name,
            "description": self.description,
            "parameters": params,
        }

    # -- internal ------------------------------------------------------------

    def _validate_input(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate kwargs against args_schema if defined.

        Args:
            kwargs: Raw input arguments.

        Returns:
            Validated and potentially transformed arguments.
        """
        if self.args_schema is not None:
            validated = self.args_schema(**kwargs)
            return validated.model_dump()
        return kwargs

    def _schema_from_signature(self) -> Dict[str, Any]:
        """Infer a JSON schema from the ``_run`` method signature.

        Returns:
            JSON Schema dictionary representing the function's parameters.
        """
        sig = inspect.signature(self._run)
        properties: Dict[str, Any] = {}
        required = []

        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "kwargs", "args"):
                continue
            annotation = param.annotation
            json_type = (
                type_map.get(annotation, "string")
                if annotation != inspect.Parameter.empty
                else "string"
            )
            prop: Dict[str, Any] = {"type": json_type}
            if param.default is not inspect.Parameter.empty:
                prop["default"] = param.default
            else:
                required.append(param_name)
            properties[param_name] = prop

        schema: Dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
        return schema

    def __repr__(self) -> str:
        """Return string representation of the tool.

        Returns:
            String representation showing the tool's class name and name.
        """
        return f"{self.__class__.__name__}(name='{self.name}')"
