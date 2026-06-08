"""
Output parsers for Mangaba AI v3.0

Parse raw LLM text output into structured Python objects.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type

from pydantic import BaseModel


class BaseOutputParser(ABC):
    """Abstract parser that converts raw text into a structured value.

    Subclasses must implement the parse() method to convert LLM output
    into specific data types (JSON, Pydantic models, lists, etc.).
    """

    @abstractmethod
    def parse(self, text: str) -> Any:
        """Parse raw text into a structured value.

        Args:
            text: The raw text output from an LLM.

        Returns:
            The parsed structured value (dict, list, model instance, etc.).

        Raises:
            ValueError: If the text cannot be parsed into the expected format.
        """
        ...

    def get_format_instructions(self) -> str:
        """Return instructions to include in the prompt so the LLM formats
        its output correctly.

        Returns:
            String containing format instructions for the LLM.
        """
        return ""


class JSONOutputParser(BaseOutputParser):
    """Extract the first JSON object or array from the text.

    Attempts to find JSON in markdown code blocks or as the first
    JSON-like structure in the text.
    """

    def parse(self, text: str) -> Any:
        """Extract and parse JSON from the text.

        Args:
            text: The raw text output from an LLM.

        Returns:
            Parsed JSON object or array.

        Raises:
            ValueError: If no valid JSON is found in the text.
        """
        # Try to find JSON block
        for pattern in [r"```json\s*([\s\S]*?)```", r"```([\s\S]*?)```"]:
            m = re.search(pattern, text)
            if m:
                return json.loads(m.group(1).strip())
        # Fallback: find first { or [
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = text.find(start_char)
            end = text.rfind(end_char)
            if start >= 0 and end > start:
                return json.loads(text[start : end + 1])
        raise ValueError("No JSON found in output")

    def get_format_instructions(self) -> str:
        """Return format instructions for JSON output.

        Returns:
            Instructions string requesting JSON format.
        """
        return "Respond with a valid JSON object."


class PydanticOutputParser(BaseOutputParser):
    """Parse output into a Pydantic model instance.

    Uses JSONOutputParser internally to extract JSON, then validates
    it against the provided Pydantic model schema.
    """

    def __init__(self, model: Type[BaseModel]) -> None:
        """Initialize the Pydantic output parser.

        Args:
            model: The Pydantic model class to parse output into.
        """
        self.model = model

    def parse(self, text: str) -> BaseModel:
        """Parse text into a Pydantic model instance.

        Args:
            text: The raw text output from an LLM.

        Returns:
            An instance of the configured Pydantic model.

        Raises:
            ValueError: If the parsed JSON is not a dict or doesn't match the schema.
        """
        json_parser = JSONOutputParser()
        data = json_parser.parse(text)
        if isinstance(data, dict):
            return self.model(**data)
        raise ValueError(
            f"Expected a JSON object for {self.model.__name__}, got {type(data).__name__}"
        )

    def get_format_instructions(self) -> str:
        """Return format instructions with the Pydantic schema.

        Returns:
            String containing the JSON schema for the model.
        """
        schema = self.model.model_json_schema()
        return (
            f"Respond with a JSON object matching this schema:\n"
            f"```json\n{json.dumps(schema, indent=2)}\n```"
        )


class ListOutputParser(BaseOutputParser):
    """Extract a list of items from the text (numbered or bulleted).

    Parses numbered lists (1., 2., 3.) or bulleted lists (-, *, •) from
    the text and returns them as a list of strings.
    """

    def parse(self, text: str) -> List[str]:
        """Extract list items from numbered or bulleted text.

        Args:
            text: The raw text output from an LLM.

        Returns:
            List of extracted items as strings.
        """
        lines = text.strip().splitlines()
        items: List[str] = []
        for line in lines:
            cleaned = re.sub(r"^[\s]*[-*•\d.)\]]+[\s]*", "", line).strip()
            if cleaned:
                items.append(cleaned)
        return items

    def get_format_instructions(self) -> str:
        """Return format instructions for list output.

        Returns:
            Instructions string requesting numbered list format.
        """
        return "Respond with a numbered list, one item per line."


class MarkdownOutputParser(BaseOutputParser):
    """Split markdown text into sections by headings.

    Parses markdown text and returns a dictionary mapping heading
    names to their content sections.
    """

    def parse(self, text: str) -> Dict[str, str]:
        """Parse markdown text into sections by headings.

        Args:
            text: The raw markdown text output from an LLM.

        Returns:
            Dictionary mapping heading names to their content sections.
        """
        sections: Dict[str, str] = {}
        current_heading = "intro"
        buffer: List[str] = []

        for line in text.splitlines():
            heading_match = re.match(r"^(#{1,6})\s+(.*)", line)
            if heading_match:
                # Save previous section
                if buffer:
                    sections[current_heading] = "\n".join(buffer).strip()
                current_heading = heading_match.group(2).strip()
                buffer = []
            else:
                buffer.append(line)

        if buffer:
            sections[current_heading] = "\n".join(buffer).strip()
        return sections

    def get_format_instructions(self) -> str:
        """Return format instructions for markdown output.

        Returns:
            Instructions string requesting markdown format with headings.
        """
        return "Respond in Markdown format with clear section headings."
