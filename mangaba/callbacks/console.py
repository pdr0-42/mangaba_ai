"""Console callback — prints agent/task/tool events to stdout."""

from __future__ import annotations

import logging
from mangaba.core.events import BaseCallback, Event, EventType

log = logging.getLogger(__name__)

_ICONS = {
    EventType.AGENT_START: "▶",
    EventType.AGENT_END: "✔",
    EventType.AGENT_ERROR: "✖",
    EventType.TASK_START: "📋",
    EventType.TASK_END: "📋",
    EventType.TOOL_START: "🔧",
    EventType.TOOL_END: "🔧",
    EventType.TOOL_ERROR: "🔧✖",
    EventType.LLM_START: "🤖",
    EventType.LLM_END: "🤖",
    EventType.REACT_THOUGHT: "💭",
    EventType.REACT_ACTION: "⚡",
    EventType.REACT_OBSERVATION: "👁",
    EventType.CREW_START: "🚀",
    EventType.CREW_END: "🏁",
}


class ConsoleCallback(BaseCallback):
    """Callback handler that prints agent/task/tool events to the console.

    This callback provides real-time visibility into the execution flow by
    logging events with appropriate icons and formatting.

    Attributes:
        level: The logging level to use for output (default: INFO).
    """

    def __init__(self, level: int = logging.INFO) -> None:
        """Initialize the ConsoleCallback.

        Args:
            level: The logging level to use for output (default: INFO).
        """
        super().__init__()
        self.level = level

    def on_event(self, event: Event) -> None:
        """Handle an event by logging it to the console.

        Args:
            event: The event to log.
        """
        icon = _ICONS.get(event.event_type, "•")
        msg = f"{icon} [{event.event_type.value}]"
        if event.source_id:
            msg += f" ({event.source_id})"
        if event.data:
            summary = ", ".join(f"{k}={v!r}" for k, v in list(event.data.items())[:4])
            msg += f" {summary}"
        log.log(self.level, msg)
