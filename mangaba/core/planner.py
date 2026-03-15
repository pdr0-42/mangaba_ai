"""
Autonomous task planner for Mangaba AI v3.0

Uses the LLM to decompose a complex task into an ordered list of
executable steps.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

log = logging.getLogger(__name__)


class PlanStep(BaseModel):
    """A single step in an execution plan."""

    step_number: int
    description: str
    tool: Optional[str] = None
    expected_result: str = ""
    dependencies: List[int] = Field(default_factory=list)


class ExecutionPlan(BaseModel):
    """An ordered plan produced by the TaskPlanner."""

    goal: str
    steps: List[PlanStep] = Field(default_factory=list)

    @property
    def total_steps(self) -> int:
        return len(self.steps)


class TaskPlanner:
    """Decomposes a complex task into a sequence of PlanSteps using an LLM.

    Example::

        planner = TaskPlanner(llm=llm_client)
        plan = planner.plan("Build a comprehensive market report for Q4")
    """

    PLAN_PROMPT = (
        "You are a task planning assistant.\n"
        "Decompose the following task into concrete, sequential steps.\n"
        "If tools are available, indicate which tool to use for each step.\n\n"
        "Respond ONLY with a JSON array of objects with keys: "
        '"step_number", "description", "tool" (or null), "expected_result", "dependencies" (list of step numbers).\n\n'
        "Available tools: {tools}\n\n"
        "Task: {task}\n\n"
        "JSON plan:"
    )

    def __init__(self, llm: Any, tools: Optional[List[Any]] = None) -> None:
        self.llm = llm
        self.tools = tools or []

    def plan(self, task: str) -> ExecutionPlan:
        tools_str = ", ".join(t.name for t in self.tools) if self.tools else "none"
        prompt = self.PLAN_PROMPT.format(tools=tools_str, task=task)
        raw = self.llm.generate_text(prompt)

        steps = self._parse_steps(raw)
        return ExecutionPlan(goal=task, steps=steps)

    @staticmethod
    def _parse_steps(raw: str) -> List[PlanStep]:
        # Try to find a JSON array in the response
        try:
            start = raw.index("[")
            end = raw.rindex("]") + 1
            data = json.loads(raw[start:end])
        except (ValueError, json.JSONDecodeError):
            # Fallback: single step
            return [PlanStep(step_number=1, description=raw.strip(), expected_result="")]

        steps = []
        for item in data:
            if isinstance(item, dict):
                steps.append(PlanStep(
                    step_number=item.get("step_number", len(steps) + 1),
                    description=item.get("description", ""),
                    tool=item.get("tool"),
                    expected_result=item.get("expected_result", ""),
                    dependencies=item.get("dependencies", []),
                ))
        return steps
