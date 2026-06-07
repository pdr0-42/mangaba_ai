"""
Prompt template system for structured prompt construction.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Set

from pydantic import BaseModel, Field


class PromptTemplate(BaseModel):
    """A string template with named placeholders ``{variable}``."""

    template: str
    input_variables: Set[str] = Field(default_factory=set)

    def model_post_init(self, __context: Any) -> None:
        """Auto-detect input variables from the template string.

        Validates that declared variables are present in the template.

        Args:
            __context: Pydantic context (unused).

        Raises:
            ValueError: If declared variables are not found in the template.
        """
        # Auto-detect variables from template
        detected = set(re.findall(r"\{(\w+)\}", self.template))
        if self.input_variables:
            missing = self.input_variables - detected
            if missing:
                raise ValueError(f"Declared variables not in template: {missing}")
        else:
            self.input_variables = detected

    def format(self, **kwargs: Any) -> str:
        """Format the template with the provided variable values.

        Args:
            **kwargs: Variable names and their values to substitute in the template.

        Returns:
            The formatted template string with all placeholders replaced.

        Raises:
            ValueError: If required template variables are missing from kwargs.
        """
        missing = self.input_variables - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing template variables: {missing}")
        return self.template.format(**{k: str(v) for k, v in kwargs.items()})

    def partial(self, **kwargs: Any) -> PromptTemplate:
        """Return a new template with some variables already filled.

        Args:
            **kwargs: Variable names and their values to pre-fill.

        Returns:
            A new PromptTemplate with the specified variables replaced.
        """
        new_template = self.template
        for k, v in kwargs.items():
            new_template = new_template.replace(f"{{{k}}}", str(v))
        return PromptTemplate(template=new_template)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatPromptTemplate(BaseModel):
    """A template that produces a list of chat messages."""

    messages: List[ChatMessage] = Field(default_factory=list)

    def format(self, **kwargs: Any) -> List[Dict[str, str]]:
        """Format all message templates with the provided variable values.

        Args:
            **kwargs: Variable names and their values to substitute in the templates.

        Returns:
            A list of message dictionaries with 'role' and 'content' keys.
        """
        result = []
        for msg in self.messages:
            tpl = PromptTemplate(template=msg.content)
            formatted = tpl.format(**kwargs) if tpl.input_variables else msg.content
            result.append({"role": msg.role, "content": formatted})
        return result

    @classmethod
    def from_messages(cls, messages: List[tuple[str, str]]) -> ChatPromptTemplate:
        """Create a ChatPromptTemplate from a list of (role, content) tuples.

        Args:
            messages: List of (role, content) tuples defining the chat messages.

        Returns:
            A ChatPromptTemplate instance with the specified messages.
        """
        return cls(messages=[ChatMessage(role=r, content=c) for r, c in messages])


class SystemPromptBuilder:
    """Composes a system prompt from role, tools, context and guardrails."""

    def __init__(self) -> None:
        """Initialize the system prompt builder.

        Attributes:
            _sections: List of prompt sections to be joined in the final build.
        """
        self._sections: List[str] = []

    def add_role(self, role: str, goal: str, backstory: str) -> SystemPromptBuilder:
        """Add a role definition section to the system prompt.

        Args:
            role: The role name (e.g., "Senior Developer").
            goal: The goal or objective of the role.
            backstory: Background information about the role.

        Returns:
            Self for method chaining.
        """
        self._sections.append(
            f"You are: {role}\n\nYour goal: {goal}\n\nBackground: {backstory}"
        )
        return self

    def add_tools_section(self, tools: List[Any]) -> SystemPromptBuilder:
        """Add a tools section describing available functions.

        Args:
            tools: List of tool objects with get_function_schema() method.

        Returns:
            Self for method chaining.
        """
        if not tools:
            return self
        lines = ["You have access to the following tools:"]
        for t in tools:
            schema = t.get_function_schema()
            lines.append(f"- **{schema['name']}**: {schema['description']}")
        lines.append(
            "\nCall tools when needed. The framework will execute them and "
            "provide the results back to you."
        )
        self._sections.append("\n".join(lines))
        return self

    def add_context(self, context: str) -> SystemPromptBuilder:
        """Add a context section to the system prompt.

        Args:
            context: Context information to provide to the LLM.

        Returns:
            Self for method chaining.
        """
        if context:
            self._sections.append(f"Context:\n{context}")
        return self

    def add_guardrails(self, rules: List[str]) -> SystemPromptBuilder:
        """Add guardrails/rules section to the system prompt.

        Args:
            rules: List of rules or constraints the LLM should follow.

        Returns:
            Self for method chaining.
        """
        if rules:
            lines = ["IMPORTANT RULES:"] + [f"- {r}" for r in rules]
            self._sections.append("\n".join(lines))
        return self

    def add_output_format(self, instructions: str) -> SystemPromptBuilder:
        """Add output format instructions to the system prompt.

        Args:
            instructions: Instructions for how the output should be formatted.

        Returns:
            Self for method chaining.
        """
        if instructions:
            self._sections.append(f"Output Format:\n{instructions}")
        return self

    def add_section(self, title: str, content: str) -> SystemPromptBuilder:
        """Add a custom section to the system prompt.

        Args:
            title: Section title.
            content: Section content.

        Returns:
            Self for method chaining.
        """
        self._sections.append(f"{title}:\n{content}")
        return self

    def build(self) -> str:
        """Build the final system prompt from all added sections.

        Returns:
            The complete system prompt string with sections joined by double newlines.
        """
        return "\n\n".join(self._sections)
