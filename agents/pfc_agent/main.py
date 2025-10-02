from __future__ import annotations

"""Pre-Flight Check (PFC) Agent v3.

The PFC agent validates a branch prior to merge. It executes the local pytest
suite and reports the outcome via audit ``Event`` messages on the NATS bus.
"""

import argparse
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

from nats.aio.client import Client as NATS

from common.protocol import Event, EventType

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
AUDIT_SUBJECT_BASE = os.getenv("AUDIT_EVENT_SUBJECT", "agent-os.pfc")
SOURCE_ID = os.getenv("PFC_SOURCE_ID", "pfc_agent_v3")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_event(
    event_type: EventType, trace_id: str, payload: Optional[dict] = None
) -> Event:
    return Event(
        trace_id=trace_id,
        event_type=event_type,
        timestamp=_now_iso(),
        source=SOURCE_ID,
        payload=payload or {},
    )


async def publish_event(nc: NATS, event: Event) -> None:
    subject = f"{AUDIT_SUBJECT_BASE}.{event.event_type.value}"
    await nc.publish(subject, event.to_bytes())


async def run_pytest(trace_id: str) -> dict:
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "pytest",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return {
        "exit_code": process.returncode,
        "stdout": stdout.decode("utf-8", errors="replace"),
        "stderr": stderr.decode("utf-8", errors="replace"),
        "trace_id": trace_id,
    }


async def execute_preflight(trace_id: str) -> int:
    nc = NATS()
    await nc.connect(servers=[NATS_URL])
    try:
        await publish_event(nc, build_event(EventType.PFC_STARTED, trace_id))
        results = await run_pytest(trace_id)

        if results["exit_code"] != 0:
            await publish_event(
                nc,
                build_event(
                    EventType.PFC_TEST_FAILED,
                    trace_id,
                    payload={
                        "exit_code": results["exit_code"],
                        "stdout": results["stdout"],
                        "stderr": results["stderr"],
                    },
                ),
            )
            return results["exit_code"]

        await publish_event(
            nc,
            build_event(
                EventType.PFC_CERTIFIED,
                trace_id,
                payload={"stdout": results["stdout"]},
            ),
        )
        return 0
    finally:
        await nc.drain()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the PFC agent")
    parser.add_argument(
        "--trace-id",
        dest="trace_id",
        default=str(uuid.uuid4()),
        help="Trace identifier shared with downstream services.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return asyncio.run(execute_preflight(args.trace_id))
    except KeyboardInterrupt:  # pragma: no cover - manual interruption
        return 130


if __name__ == "__main__":
    sys.exit(main())
