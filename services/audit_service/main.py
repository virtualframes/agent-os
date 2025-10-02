"""Audit Service for Agent-OS.

This service subscribes to the NATS message bus and records every audit
``Event`` in PostgreSQL. It enforces the immutability requirements outlined in
the Agent-OS engineering protocol by appending entries to the
``audit_events`` table.

Schema definition
-----------------
The database migrations for this service must create the following table:

.. code-block:: sql

    CREATE TABLE IF NOT EXISTS audit_events (
        id SERIAL PRIMARY KEY,
        trace_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        event_timestamp TIMESTAMPTZ NOT NULL,
        source TEXT NOT NULL,
        payload JSONB NOT NULL,
        recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

The ``event_timestamp`` column stores the timestamp provided by the producer
while ``recorded_at`` reflects when the Audit Service persisted the event.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from databases import Database
from nats.aio.client import Client as NATS
from nats.aio.msg import Msg

from common.protocol import Event, EventType

LOGGER = logging.getLogger("agent_os.audit_service")

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
AUDIT_SUBJECT = os.getenv("AUDIT_SUBJECT", "agent-os.>")
DATABASE_URL = os.getenv(
    "AUDIT_DATABASE_URL", "postgresql://agentos:password@localhost/token_optimizer_db"
)


database = Database(DATABASE_URL)
nc = NATS()


async def store_event(event: Event) -> None:
    """Persist an ``Event`` to the PostgreSQL ledger."""

    query = (
        "INSERT INTO audit_events (trace_id, event_type, event_timestamp, source, payload) "
        "VALUES (:trace_id, :event_type, :event_timestamp, :source, :payload)"
    )

    await database.execute(
        query,
        values={
            "trace_id": event.trace_id,
            "event_type": event.event_type.value,
            "event_timestamp": event.timestamp,
            "source": event.source,
            "payload": event.payload,
        },
    )


async def handle_message(msg: Msg) -> None:
    """Decode an incoming NATS message and write it to the database."""

    try:
        event = Event.from_bytes(msg.data)
    except Exception as exc:  # pragma: no cover - defensive logging path
        LOGGER.exception("Failed to decode audit event: subject=%s", msg.subject)
        return

    LOGGER.debug("Recording event %s from %s", event.event_type.value, event.source)
    await store_event(event)


async def connect_nats() -> None:
    """Ensure the NATS connection is established."""

    await nc.connect(servers=[NATS_URL])
    LOGGER.info("Connected to NATS at %s", NATS_URL)


async def run() -> None:
    """Entry point for the audit service."""

    logging.basicConfig(level=logging.INFO)
    await database.connect()
    LOGGER.info("Connected to database %s", DATABASE_URL)

    try:
        await connect_nats()
        await nc.subscribe(AUDIT_SUBJECT, cb=handle_message)
        LOGGER.info("Subscribed to %s", AUDIT_SUBJECT)

        while True:
            await asyncio.sleep(1)
    finally:
        await nc.drain()
        await database.disconnect()


def build_event(
    event_type: EventType,
    *,
    trace_id: str,
    source: str,
    payload: Optional[dict] = None,
) -> Event:
    """Utility for constructing audit events with standard metadata."""

    return Event(
        trace_id=trace_id,
        event_type=event_type,
        timestamp=datetime.now(timezone.utc).isoformat(),
        source=source,
        payload=payload or {},
    )


if __name__ == "__main__":  # pragma: no cover - manual execution entrypoint
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        LOGGER.info("Audit service terminated via KeyboardInterrupt")
