"""
Autonomous task planner for Mangaba AI v3.0

Uses the LLM to decompose a complex task into an ordered list of
executable steps.
"""

from __future__ import annotations

import json
import logging
from typing import Any, List, Optional

from pydantic import BaseModel, Field

log = logging.getLogger(__name__)


class PlanStep(BaseModel):
    """A single step in an execution plan.

    Represents one actionable step in a decomposed task plan,
    including which tool to use (if any) and expected results.

    Attributes:
        step_number: The sequential order of this step in the plan.
        description: What this step should accomplish.
        tool: Optional tool name to use for this step.
        expected_result: What the output of this step should look like.
        dependencies: List of step numbers this step depends on.
    """

    step_number: int
    description: str
    tool: Optional[str] = None
    expected_result: str = ""
    dependencies: List[int] = Field(default_factory=list)


class ExecutionPlan(BaseModel):
    """An ordered plan produced by the TaskPlanner.

    Contains the overall goal and a sequence of PlanSteps to achieve it.

    Attributes:
        goal: The overall task or objective to accomplish.
        steps: Ordered list of steps to execute.
    """

    goal: str
    steps: List[PlanStep] = Field(default_factory=list)

    @property
    def total_steps(self) -> int:
        """Get the total number of steps in the plan.

        Returns:
            The number of steps in the plan.
        """
        return len(self.steps)


class TaskPlanner:
    """Decomposes a complex task into a sequence of PlanSteps using an LLM.

    Uses the LLM to analyze a task and break it down into concrete,
    sequential steps that can be executed by agents or tools.

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
        """Initialize the task planner.

        Args:
            llm: LLM client instance for generating plans.
            tools: Optional list of available tools for the plan.
        """
        self.llm = llm
        self.tools = tools or []

    def plan(self, task: str) -> ExecutionPlan:
        """Generate an execution plan for the given task.

        Args:
            task: The task description to decompose.

        Returns:
            An ExecutionPlan containing the goal and ordered steps.

        Raises:
            ValueError: If the plan cannot be generated or parsed.
        """
        tools_str = ", ".join(t.name for t in self.tools) if self.tools else "none"
        prompt = self.PLAN_PROMPT.format(tools=tools_str, task=task)
        raw = self.llm.generate_text(prompt)

        steps = self._parse_steps(raw)
        return ExecutionPlan(goal=task, steps=steps)

    @staticmethod
    def _parse_steps(raw: str) -> List[PlanStep]:
        """Parse the LLM response into PlanStep objects.

        Args:
            raw: The raw text response from the LLM.

        Returns:
            List of PlanStep objects parsed from the response.

        Raises:
            ValueError: If the JSON cannot be parsed.
        """
        # Try to find a JSON array in the response
        try:
            start = raw.index("[")
            end = raw.rindex("]") + 1
            data = json.loads(raw[start:end])
        except (ValueError, json.JSONDecodeError):
            # Fallback: single step
            return [
                PlanStep(step_number=1, description=raw.strip(), expected_result="")
            ]

        steps = []
        for item in data:
            if isinstance(item, dict):
                steps.append(
                    PlanStep(
                        step_number=item.get("step_number", len(steps) + 1),
                        description=item.get("description", ""),
                        tool=item.get("tool"),
                        expected_result=item.get("expected_result", ""),
                        dependencies=item.get("dependencies", []),
                    )
                )
        return steps
