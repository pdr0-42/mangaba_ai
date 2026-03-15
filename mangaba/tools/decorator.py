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
    """Decorator that converts a function into a :class:`BaseTool`.

    Can be used with or without arguments::

        @tool
        def my_tool(x: int) -> str: ...

        @tool(name="custom_name")
        def my_tool(x: int) -> str: ...
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
    """Create a Pydantic model from the function signature."""
    sig = inspect.signature(func)
    hints = get_type_hints(func)

    fields: Dict[str, Any] = {}
    type_map = {
        str: (str, ...),
        int: (int, ...),
        float: (float, ...),
        bool: (bool, ...),
        list: (list, ...),
        dict: (dict, ...),
    }

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
