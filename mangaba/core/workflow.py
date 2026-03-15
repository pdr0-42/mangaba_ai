"""
Workflow engine — compose tasks into pipelines, conditional branches, and parallel stages.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from mangaba.core.task import Task, TaskOutput
from mangaba.core.events import EventBus, Event, EventType

log = logging.getLogger(__name__)


@dataclass
class StageResult:
    """Output produced by a pipeline stage."""
    stage_name: str
    outputs: List[TaskOutput]
    duration: float = 0.0


class Stage:
    """A named group of tasks within a pipeline."""

    def __init__(self, name: str, tasks: List[Task]) -> None:
        self.name = name
        self.tasks = tasks

    def run(self, inputs: Dict[str, Any]) -> StageResult:
        start = time.monotonic()
        outputs = [t.execute(inputs) for t in self.tasks]
        return StageResult(stage_name=self.name, outputs=outputs, duration=time.monotonic() - start)


class ParallelStage(Stage):
    """Execute tasks concurrently."""

    def run(self, inputs: Dict[str, Any]) -> StageResult:
        start = time.monotonic()

        async def _go():
            return list(await asyncio.gather(*(t.aexecute(inputs) for t in self.tasks)))

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            outputs = [t.execute(inputs) for t in self.tasks]
        else:
            outputs = asyncio.run(_go())

        return StageResult(stage_name=self.name, outputs=outputs, duration=time.monotonic() - start)


class ConditionalStage:
    """Pick one of two stages based on a condition evaluated at runtime."""

    def __init__(
        self,
        name: str,
        condition: Callable[[Dict[str, Any]], bool],
        if_true: Stage,
        if_false: Optional[Stage] = None,
    ) -> None:
        self.name = name
        self.condition = condition
        self.if_true = if_true
        self.if_false = if_false

    def run(self, inputs: Dict[str, Any]) -> StageResult:
        branch = self.if_true if self.condition(inputs) else self.if_false
        if branch is None:
            return StageResult(stage_name=self.name, outputs=[])
        return branch.run(inputs)


@dataclass
class PipelineResult:
    """Aggregated output of an entire pipeline run."""
    stages: List[StageResult] = field(default_factory=list)
    duration: float = 0.0

    @property
    def final_output(self) -> str:
        for sr in reversed(self.stages):
            if sr.outputs:
                return sr.outputs[-1].result
        return ""


class Pipeline:
    """Execute a sequence of stages, feeding context forward.

    Example::

        pipeline = Pipeline(stages=[
            Stage("research", [task1]),
            ParallelStage("analysis", [task2a, task2b]),
            ConditionalStage("expand", cond, Stage("deep", [task3])),
            Stage("report", [task4]),
        ])
        result = pipeline.run({"topic": "AI"})
    """

    def __init__(self, stages: list, name: str = "pipeline") -> None:
        self.name = name
        self.stages = stages

    def run(self, inputs: Optional[Dict[str, Any]] = None) -> PipelineResult:
        inputs = dict(inputs or {})
        start = time.monotonic()
        result = PipelineResult()

        EventBus.emit(Event(event_type=EventType.CREW_START, source_id=self.name, data={"type": "pipeline"}))

        for stage in self.stages:
            sr = stage.run(inputs)
            result.stages.append(sr)

        result.duration = time.monotonic() - start
        EventBus.emit(Event(event_type=EventType.CREW_END, source_id=self.name, data={"duration": result.duration}))
        return result
