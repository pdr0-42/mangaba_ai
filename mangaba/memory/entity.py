"""
Entity memory for Mangaba AI v3.0

Extracts and tracks entities (people, places, concepts) mentioned
during conversations, keeping a running summary for each entity.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from mangaba.memory.base import BaseMemory


class EntityMemory(BaseMemory):
    """In-memory entity store that maintains per-entity summaries."""

    def __init__(self) -> None:
        # entity_name (lower) -> {id, name, facts: [str], last_updated}
        self._entities: Dict[str, Dict[str, Any]] = {}

    def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Extract entities from *content* and store facts about them.

        ``metadata`` may contain ``{"entities": ["Alice", "Berlin"]}`` to
        explicitly list entities.  If absent, a simple heuristic (capitalised
        words) is used.
        """
        meta = metadata or {}
        entities = meta.get("entities") or self._extract_entities(content)

        ids: List[str] = []
        for name in entities:
            key = name.lower().strip()
            if not key:
                continue
            if key not in self._entities:
                eid = uuid.uuid4().hex[:12]
                self._entities[key] = {
                    "id": eid,
                    "name": name,
                    "facts": [],
                    "last_updated": datetime.now().isoformat(),
                }
            entry = self._entities[key]
            entry["facts"].append(content)
            entry["last_updated"] = datetime.now().isoformat()
            ids.append(entry["id"])

        return ",".join(ids) if ids else ""

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        q_lower = query.lower()
        scored = []
        for key, entry in self._entities.items():
            score = 0
            if q_lower in key:
                score += 10
            for w in q_lower.split():
                if w in key:
                    score += 3
                for fact in entry["facts"]:
                    if w in fact.lower():
                        score += 1
            if score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:top_k]]

    def get_entity(self, name: str) -> Optional[Dict[str, Any]]:
        return self._entities.get(name.lower())

    def get_all(self) -> List[Dict[str, Any]]:
        return list(self._entities.values())

    def clear(self) -> None:
        self._entities.clear()

    @staticmethod
    def _extract_entities(text: str) -> List[str]:
        """Naive entity extraction via capitalised multi-word groups."""
        # Matches sequences of capitalised words (2+ chars) not at sentence start
        pattern = r'(?<!\.\s)(?<!\n)\b([A-Z][a-z]{1,}\b(?:\s+[A-Z][a-z]{1,}\b)*)'
        matches = re.findall(pattern, text)
        seen: Dict[str, str] = {}
        for m in matches:
            key = m.lower()
            if key not in seen and len(m) > 2:
                seen[key] = m
        return list(seen.values())
