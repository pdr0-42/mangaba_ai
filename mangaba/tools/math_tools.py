"""
Math tools for Mangaba AI v3.0
"""

from __future__ import annotations

import ast
import operator
from typing import Any

from pydantic import BaseModel, Field

from mangaba.tools.base import BaseTool


class CalculatorInput(BaseModel):
    """Input schema for the calculator tool."""

    expression: str = Field(
        ..., description="Mathematical expression to evaluate, e.g. '2 + 3 * 4'"
    )


class CalculatorTool(BaseTool):
    """Safely evaluate mathematical expressions.

    Supports basic arithmetic operations: addition, subtraction, multiplication,
    division, floor division, modulo, and exponentiation. Uses AST parsing to
    ensure safe evaluation without executing arbitrary code.
    """

    name = "calculator"
    description = "Evaluate a mathematical expression and return the numeric result"
    args_schema = CalculatorInput

    _SAFE_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def _run(self, expression: str) -> str:
        """Evaluate a mathematical expression.

        Args:
            expression: The mathematical expression to evaluate.

        Returns:
            The numeric result as a string, or an error message if evaluation fails.
        """
        try:
            tree = ast.parse(expression, mode="eval")
            result = self._eval_node(tree.body)
            return str(result)
        except (ValueError, TypeError, ZeroDivisionError, SyntaxError) as exc:
            return f"Error: {exc}"

    def _eval_node(self, node: ast.AST) -> Any:
        """Recursively evaluate an AST node.

        Args:
            node: The AST node to evaluate.

        Returns:
            The evaluated value of the node.

        Raises:
            ValueError: If the node type or value is not supported.
        """
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float, complex)):
                return node.value
            raise ValueError(f"Unsupported constant: {node.value!r}")
        if isinstance(node, ast.BinOp):
            op_fn = self._SAFE_OPS.get(type(node.op))
            if op_fn is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op_fn(self._eval_node(node.left), self._eval_node(node.right))
        if isinstance(node, ast.UnaryOp):
            op_fn = self._SAFE_OPS.get(type(node.op))
            if op_fn is None:
                raise ValueError(
                    f"Unsupported unary operator: {type(node.op).__name__}"
                )
            return op_fn(self._eval_node(node.operand))
        raise ValueError(f"Unsupported expression node: {type(node).__name__}")
