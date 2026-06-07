"""Schemas for LLM provider tool declarations"""

from pydantic import BaseModel
from typing import Any, Dict, List
import json


class GoogleToolSchemaDeclaration(BaseModel):
    name: str
    description: str
    parameters: dict


class OpenAIToolSchemaDeclaration(BaseModel):
    type: str
    function: dict


class AnthropicToolSchemaDeclaration(BaseModel):
    name: str
    description: str
    input_schema: dict


def _tool_to_google_declaration(tool: Any) -> Dict[str, Any]:
    """Convert a BaseTool to Google function declaration format.

    Args:
        tool: A BaseTool instance with get_function_schema() method.

    Returns:
        Dictionary in Google function declaration format.
    """
    schema = tool.get_function_schema()
    return GoogleToolSchemaDeclaration(**schema).model_dump()


def _tool_to_openai_schema(tool: Any) -> Dict[str, Any]:
    """Convert a BaseTool to OpenAI function calling format.

    Args:
        tool: A BaseTool instance with get_function_schema() method.

    Returns:
        Dictionary in OpenAI function calling format.
    """
    schema = tool.get_function_schema()
    return OpenAIToolSchemaDeclaration(**schema).model_dump()


def _tool_to_anthropic_schema(tool: Any) -> Dict[str, Any]:
    """Convert a BaseTool to Anthropic tool-use format.

    Args:
        tool: A BaseTool instance with get_function_schema() method.

    Returns:
        Dictionary in Anthropic tool-use format.
    """
    schema = tool.get_function_schema()
    return AnthropicToolSchemaDeclaration(**schema).model_dump()


def _tools_to_hf_prompt_section(tools: List[Any]) -> str:
    """Render available tools as a system-prompt section for Hugging Face.

    Creates a formatted text section describing available tools and their
    parameters for Hugging Face models that use prompt-based tool calling.

    Args:
        tools: List of BaseTool instances with get_function_schema() method.

    Returns:
        Formatted string describing available tools, or empty string if no tools.
    """
    if not tools:
        return ""
    lines = ["You have access to the following tools:\n"]
    for t in tools:
        schema = t.get_function_schema()
        params = json.dumps(schema.get("parameters", {}), indent=2)
        lines.append(
            f"### {schema['name']}\n{schema['description']}\nParameters: {params}\n"
        )
    lines.append(
        "To use a tool, respond ONLY with a JSON block:\n"
        '```json\n{"tool_calls": [{"tool_name": "<name>", "arguments": {<args>}}]}\n```\n'
        "If no tool is needed, respond normally."
    )
    return "\n".join(lines)
