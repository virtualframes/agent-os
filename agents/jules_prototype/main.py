"""Prototype Jules agent that consumes jobs from the shared NATS bus.

The agent contract expects all job subjects to follow the
`jobs.<command>.<agent_id>` structure. This file subscribes using the
`jobs.*.jules` wildcard so it receives any command that targets the Jules
prototype specifically. Other agents can subscribe to `jobs.<command>.*` or
`jobs.*.<agent_id>` depending on their routing needs.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

from nats.aio.client import Client as NATS
from nats.aio.msg import Msg

LOGGER = logging.getLogger(__name__)

DEFAULT_NATS_URL = "nats://127.0.0.1:4222"
AGENT_ID = "jules"
SUBJECT_PATTERN = f"jobs.*.{AGENT_ID}"


async def handle_job(msg: Msg) -> None:
    """Process an incoming job message and send a response."""

    try:
        payload = json.loads(msg.data.decode("utf-8"))
    except json.JSONDecodeError:
        LOGGER.exception("Invalid payload for subject %s", msg.subject)
        await msg.respond(
            json.dumps({"status": "error", "result": "Malformed payload"}).encode(
                "utf-8"
            )
        )
        return

    command = msg.subject.split(".")[1]
    LOGGER.info("Received command '%s' for agent '%s'", command, AGENT_ID)
    result = await execute_command(command, payload.get("payload", {}))
    response = json.dumps({"status": "ok", "result": result}).encode("utf-8")
    await msg.respond(response)


async def execute_command(command: str, payload: dict[str, Any]) -> Any:
    """Execute the provided command.

    For the prototype we simply echo back what was requested.
    """

    await asyncio.sleep(0)  # ensure this stays async-friendly
    return {"command": command, "payload": payload}


async def main() -> None:
    """Entrypoint for running the Jules prototype agent."""

    url = os.getenv("NATS_URL", DEFAULT_NATS_URL)
    client = NATS()
    LOGGER.info("Connecting to NATS at %s", url)
    await client.connect(url)
    try:
        LOGGER.info("Subscribing to %s", SUBJECT_PATTERN)
        await client.subscribe(SUBJECT_PATTERN, cb=handle_job)
        # Keep the agent alive indefinitely.
        while True:
            await asyncio.sleep(1)
    finally:
        await client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
