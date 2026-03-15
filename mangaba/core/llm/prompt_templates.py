"""
Prompt template system for structured prompt construction.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field


class PromptTemplate(BaseModel):
    """A string template with named placeholders ``{variable}``."""

    template: str
    input_variables: Set[str] = Field(default_factory=set)

    def model_post_init(self, __context: Any) -> None:
        # Auto-detect variables from template
        detected = set(re.findall(r"\{(\w+)\}", self.template))
        if self.input_variables:
            missing = self.input_variables - detected
            if missing:
                raise ValueError(f"Declared variables not in template: {missing}")
        else:
            self.input_variables = detected

    def format(self, **kwargs: Any) -> str:
        missing = self.input_variables - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing template variables: {missing}")
        return self.template.format(**{k: str(v) for k, v in kwargs.items()})

    def partial(self, **kwargs: Any) -> PromptTemplate:
        """Return a new template with some variables already filled."""
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
        result = []
        for msg in self.messages:
            tpl = PromptTemplate(template=msg.content)
            formatted = tpl.format(**kwargs) if tpl.input_variables else msg.content
            result.append({"role": msg.role, "content": formatted})
        return result

    @classmethod
    def from_messages(cls, messages: List[tuple[str, str]]) -> ChatPromptTemplate:
        return cls(messages=[ChatMessage(role=r, content=c) for r, c in messages])


class SystemPromptBuilder:
    """Composes a system prompt from role, tools, context and guardrails."""

    def __init__(self) -> None:
        self._sections: List[str] = []

    def add_role(self, role: str, goal: str, backstory: str) -> SystemPromptBuilder:
        self._sections.append(
            f"You are: {role}\n\nYour goal: {goal}\n\nBackground: {backstory}"
        )
        return self

    def add_tools_section(self, tools: List[Any]) -> SystemPromptBuilder:
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
        if context:
            self._sections.append(f"Context:\n{context}")
        return self

    def add_guardrails(self, rules: List[str]) -> SystemPromptBuilder:
        if rules:
            lines = ["IMPORTANT RULES:"] + [f"- {r}" for r in rules]
            self._sections.append("\n".join(lines))
        return self

    def add_output_format(self, instructions: str) -> SystemPromptBuilder:
        if instructions:
            self._sections.append(f"Output Format:\n{instructions}")
        return self

    def add_section(self, title: str, content: str) -> SystemPromptBuilder:
        self._sections.append(f"{title}:\n{content}")
        return self

    def build(self) -> str:
        return "\n\n".join(self._sections)
