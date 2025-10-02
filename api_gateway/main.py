# api_gateway/main.py
# The sole entrypoint for the terminal UI.
# It translates HTTPS requests into asynchronous jobs on the NATS bus.

import os
import asyncio
import uuid
from fastapi import FastAPI, HTTPException
from nats.aio.client import Client as NATS
from common.protocol import JobRequest, JobResult, JobType
import re

# --- Configuration ---
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
TOKEN_OPTIMIZER_URL = os.getenv("TOKEN_OPTIMIZER_URL", "http://localhost:8001")
REQUEST_TIMEOUT = 30.0  # seconds

# --- Application State ---
app = FastAPI(title="Agent-OS API Gateway")
nc = NATS()


# --- Lifespan Management ---
@app.on_event("startup")
async def startup_event():
    """Connect to NATS on application startup."""
    try:
        await nc.connect(servers=[NATS_URL])
        print(f"Successfully connected to NATS at {NATS_URL}")
    except Exception as e:
        print(f"FATAL: Could not connect to NATS. Error: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Drain NATS connection on application shutdown."""
    print("Draining NATS connection...")
    await nc.drain()


# --- Helper Functions ---
def parse_command(command: str) -> (str, JobType, str):
    """
    Parses a raw command string to extract agent, job type, and the actual prompt.
    Format: @<agent> <verb> <prompt>
    Example: "@claude refactor this code..."
    Returns: (target_agent, job_type, remaining_prompt)
    """
    # Default values
    target_agent = "jules"
    job_type = JobType.GENERAL_QUERY

    match = re.match(r"@(\w+)\s+(\w+)\s*(.*)", command, re.DOTALL)
    if match:
        agent, verb, prompt = match.groups()
        target_agent = agent.lower()
        verb = verb.lower()

        verb_to_job_type = {
            "generate": JobType.CODE_GENERATE,
            "refactor": JobType.CODE_REFACTOR,
            "fix": JobType.CODE_FIX,
            "query": JobType.GENERAL_QUERY,
        }
        job_type = verb_to_job_type.get(verb, JobType.GENERAL_QUERY)
        return target_agent, job_type, prompt.strip()

    # Fallback for commands without agent/verb
    return target_agent, job_type, command


# --- API Endpoints ---
@app.post("/command")
async def execute_command(command_data: dict):
    """
    Receives a command, dispatches it as a job, and waits for the result.
    """
    trace_id = str(uuid.uuid4())
    raw_command = command_data.get("command", "")

    # 1. Parse command
    target_agent, job_type, prompt = parse_command(raw_command)

    # 2. (TODO) Call Token Optimizer

    # 3. Define NATS subjects
    job_subject = f"jobs.{job_type.value}.{target_agent}"
    result_subject = f"results.{trace_id}"

    # 4. Create job request
    job = JobRequest(
        trace_id=trace_id,
        job_type=job_type,
        target_agent=target_agent,
        payload={"prompt": prompt, "context": command_data.get("context", {})},
        user_id=command_data.get("user_id", "default_user"),
    )

    # 5. Subscribe to result channel
    future = asyncio.Future()

    async def result_handler(msg):
        try:
            result = JobResult.from_bytes(msg.data)
            if result.is_complete:
                future.set_result(result.payload)
        except Exception as e:
            future.set_exception(e)

    sub = await nc.subscribe(result_subject, cb=result_handler)

    try:
        # 6. Publish job
        await nc.publish(job_subject, job.to_bytes())

        # 7. Wait for result
        print(f"[{trace_id}] Job dispatched to {job_subject}. Awaiting result...")
        result_payload = await asyncio.wait_for(future, timeout=REQUEST_TIMEOUT)
        return result_payload

    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timed out.")
    finally:
        # 8. Unsubscribe
        await sub.unsubscribe()
