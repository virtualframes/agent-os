"""Audit logging utilities for Agent-OS services.

The production system persists audit events to PostgreSQL. The scaffold below
implements a lightweight file-backed logger suitable for local development and
unit testing. It exposes the same interface expected by core components so the
logic can be swapped with a database implementation without touching the call
sites.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, MutableMapping, Optional


@dataclass
class AuditRecord:
    """Represents a single audit entry."""

    timestamp: str
    source: str
    payload: MutableMapping[str, object]

    def to_json(self) -> str:
        return json.dumps(
            {
                "timestamp": self.timestamp,
                "source": self.source,
                "payload": self.payload,
            }
        )


class AuditLogger:
    """Simple append-only audit logger.

    Parameters
    ----------
    storage_path:
        Optional path to a JSON lines file used to persist events. When no
        path is provided the logger stores events in memory only, which is
        useful for tests.
    """

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self._storage_path = storage_path
        self._buffer: List[AuditRecord] = []
        if self._storage_path:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        source: str,
        payload: MutableMapping[str, object],
    ) -> AuditRecord:
        """Record an audit event and persist it if configured."""

        now = datetime.now(timezone.utc)
        timestamp = now.isoformat()
        record = AuditRecord(
            timestamp=timestamp,
            source=source,
            payload=payload,
        )
        self._buffer.append(record)
        if self._storage_path:
            with self._storage_path.open("a", encoding="utf-8") as handle:
                handle.write(record.to_json() + "\n")
        return record

    def flush(self) -> None:
        """Flush buffered records to disk (no-op for the in-memory store)."""

        if self._storage_path:
            # Records persist during writes; flushing only clears the in-memory
            # cache to avoid unbounded growth when long-running.
            self._buffer.clear()

    def records(self) -> Iterable[AuditRecord]:
        """Return an iterable view of the buffered audit entries."""

        return tuple(self._buffer)
