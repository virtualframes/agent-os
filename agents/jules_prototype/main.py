# agents/jules_prototype/main.py
# A prototype of a distributed, asynchronous agent.

import os
import asyncio
from nats.aio.client import Client as NATS
from common.protocol import JobRequest, JobResult

# --- Configuration ---
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
AGENT_ID = os.getenv("AGENT_ID", "jules-prototype-01")
SUBSCRIBE_SUBJECT = "jobs.*.jules"  # Listen for all job types targeting 'jules'


async def run():
    """Main execution function for the agent."""
    nc = NATS()

    async def disconnected_cb():
        print(f"[{AGENT_ID}] Got disconnected from NATS...")

    async def reconnected_cb():
        print(f"[{AGENT_ID}] Got reconnected to NATS at {nc.connected_url.netloc}...")

    try:
        await nc.connect(
            servers=[NATS_URL],
            reconnected_cb=reconnected_cb,
            disconnected_cb=disconnected_cb,
            max_reconnect_attempts=-1,
            name=AGENT_ID,
        )
        print(f"[{AGENT_ID}] Connected to NATS. Subscribing to '{SUBSCRIBE_SUBJECT}'...")
    except Exception as e:
        print(f"[{AGENT_ID}] FATAL: Could not connect to NATS. Error: {e}")
        return

    async def message_handler(msg):
        """Processes incoming job requests."""
        try:
            job = JobRequest.from_bytes(msg.data)
            print(
                f"[{AGENT_ID}][{job.trace_id}] Received job: {job.job_type.value} on subject {msg.subject}"
            )

            # --- Agent Logic ---
            await asyncio.sleep(2)  # Simulate work

            result_payload = {
                "message": f"Hello from {AGENT_ID}. Your job '{job.job_type.value}' was received.",
                "original_payload": job.payload,
            }
            # --- End Logic ---

            result = JobResult(
                trace_id=job.trace_id,
                is_complete=True,
                is_error=False,
                payload=result_payload,
            )

            result_subject = f"results.{job.trace_id}"
            await nc.publish(result_subject, result.to_bytes())
            print(f"[{AGENT_ID}][{job.trace_id}] Published result to {result_subject}")

        except Exception as e:
            print(f"[{AGENT_ID}] Error processing message: {e}")
            # TODO: Publish an error result back to the gateway.

    await nc.subscribe(SUBSCRIBE_SUBJECT, cb=message_handler)

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Agent shutting down.")
