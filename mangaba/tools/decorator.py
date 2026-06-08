"""
@tool decorator for Mangaba AI v3.0

Turns a plain function into a BaseTool instance, auto-inferring
name, description (from docstring), and args_schema (from type hints).

Example::

    @tool
    def search_web(query: str, max_results: int = 5) -> str:
        \"\"\"Search the web for current information.\"\"\"
        ...

    @tool(name="calculator", description="Evaluate math expressions")
    def calc(expression: str) -> str:
        ...
"""

from __future__ import annotations

import inspect
from typing import Any, Callable, Dict, Optional, Type, get_type_hints

from pydantic import BaseModel, Field, create_model

from mangaba.tools.base import BaseTool


def tool(
    fn: Optional[Callable[..., Any]] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    return_direct: bool = False,
) -> Any:
    """Decorator that converts a function into a BaseTool.

    Automatically infers the tool name, description (from docstring),
    and arguments schema (from type hints and defaults).

    Can be used with or without arguments::

        @tool
        def my_tool(x: int) -> str: ...

        @tool(name="custom_name", description="Custom description")
        def my_tool(x: int) -> str: ...

    Args:
        fn: The function to convert. If None, returns a decorator.
        name: Optional custom name for the tool. Defaults to function name.
        description: Optional custom description. Defaults to function docstring.
        return_direct: Whether to return the tool output directly to the user.

    Returns:
        Either a decorator function or a BaseTool instance.
    """

    def _wrap(func: Callable[..., Any]) -> BaseTool:
        tool_name = name or func.__name__
        tool_desc = description or (inspect.getdoc(func) or func.__name__)
        schema = _build_pydantic_model(func, tool_name)

        # Build a concrete BaseTool subclass dynamically
        cls_attrs: Dict[str, Any] = {
            "name": tool_name,
            "description": tool_desc,
            "args_schema": schema,
            "return_direct": return_direct,
            "_fn": staticmethod(func),
        }

        def _run_impl(self: Any, **kwargs: Any) -> Any:
            return self._fn(**kwargs)

        cls_attrs["_run"] = _run_impl

        tool_cls = type(
            f"Tool_{tool_name}",
            (BaseTool,),
            cls_attrs,
        )
        return tool_cls()

    if fn is not None:
        # @tool without parentheses
        return _wrap(fn)
    # @tool(...) with parentheses
    return _wrap


def _build_pydantic_model(func: Callable[..., Any], tool_name: str) -> Type[BaseModel]:
    """Create a Pydantic model from the function signature.

    Analyzes the function's signature and type hints to build a Pydantic
    BaseModel that represents the tool's input schema.

    Args:
        func: The function to analyze.
        tool_name: Name of the tool (used for model naming).

    Returns:
        A Pydantic BaseModel class representing the function's input schema.
    """
    sig = inspect.signature(func)
    hints = get_type_hints(func)

    fields: Dict[str, Any] = {}

    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue
        annotation = hints.get(param_name, str)
        if param.default is not inspect.Parameter.empty:
            fields[param_name] = (annotation, Field(default=param.default))
        else:
            fields[param_name] = (annotation, Field(...))

    model_name = f"{tool_name.title().replace('_', '')}Input"
    return create_model(model_name, **fields)
