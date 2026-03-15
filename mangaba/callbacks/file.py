"""File callback — persist events as JSONL."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from mangaba.core.events import BaseCallback, Event

log = logging.getLogger(__name__)


class FileCallback(BaseCallback):
    """Append events to a JSONL log file."""

    def __init__(self, path: str | Path = "mangaba_events.jsonl") -> None:
        super().__init__()
        self.path = Path(path)

    def handle_event(self, event: Event) -> None:
        record = {
            "event_type": event.event_type.value,
            "source_id": event.source_id,
            "source_type": event.source_type,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "data": event.data,
        }
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, default=str) + "\n")
        except OSError:
            log.warning("FileCallback: could not write to %s", self.path)
