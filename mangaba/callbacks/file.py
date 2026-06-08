"""File callback — persist events as JSONL."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from mangaba.core.events import BaseCallback, Event

log = logging.getLogger(__name__)


class FileCallback(BaseCallback):
    """Callback handler that persists events to a JSONL log file.

    This callback writes each event as a JSON line to a log file for
    persistent storage and later analysis.

    Attributes:
        path: The file path where events will be written.
    """

    def __init__(self, path: str | Path = "mangaba_events.jsonl") -> None:
        """Initialize the FileCallback.

        Args:
            path: The file path where events will be written
                (default: "mangaba_events.jsonl").
        """
        super().__init__()
        self.path = Path(path)

    def on_event(self, event: Event) -> None:
        """Handle an event by appending it to the log file.

        Args:
            event: The event to log.
        """
        record = {
            "event_type": event.event_type.value,
            "source_id": event.source_id,
            "source_type": event.source_type,
            "timestamp": event.timestamp,
            "data": event.data,
        }
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, default=str) + "\n")
        except OSError:
            log.warning("FileCallback: could not write to %s", self.path)
