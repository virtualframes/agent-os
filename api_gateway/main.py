"""FastAPI application for publishing agent jobs via NATS.

This module exposes a `/command` endpoint that accepts job requests for
downstream agents. Requests are forwarded to NATS using the standardized
three-token subject format (`jobs.<command>.<agent>`). The layout lets
agents subscribe using wildcard patterns like `jobs.*.<agent>` or
`jobs.<command>.*` without needing bespoke routing tables.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrNoServers, ErrTimeout
from nats.aio.msg import Msg
from pydantic import BaseModel, Field, validator

LOGGER = logging.getLogger(__name__)

DEFAULT_NATS_URL = "nats://127.0.0.1:4222"


class CommandRequest(BaseModel):
    """Incoming job request body."""

    agent: str = Field(..., description="Identifier of the target agent")
    command: str = Field(..., description="Command/job name to run")
    payload: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary command parameters"
    )
    timeout_seconds: float = Field(
        default=5.0,
        ge=0.1,
        le=60.0,
        description="How long to wait for an agent response before timing out",
    )

    @validator("agent", "command")
    @classmethod
    def _ensure_token_is_safe(cls, token: str) -> str:
        """Reject subject tokens that would break the contract.

        The NATS subject layout is `jobs.<command>.<agent>`. Each token must be a
        single dot-free string composed of alphanumeric characters plus `-` and
        `_`.
        """

        if not re.fullmatch(r"[A-Za-z0-9_-]+", token):
            msg = (
                "Subject tokens must be alphanumeric (plus '-' and '_') and contain "
                "no periods"
            )
            raise ValueError(msg)
        return token


class CommandResponse(BaseModel):
    """Response payload returned to the HTTP client."""

    status: str
    result: Any | None = None
    agent: str
    command: str


class NATSClient:
    """Thin wrapper around the shared NATS connection."""

    def __init__(self, url: str = DEFAULT_NATS_URL) -> None:
        self._url = url
        self._connection: NATS | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """Ensure a connection is established."""

        if self._connection and self._connection.is_connected:
            return
        async with self._lock:
            if self._connection and self._connection.is_connected:
                return
            try:
                LOGGER.info("Connecting to NATS server at %s", self._url)
                connection = NATS()
                await connection.connect(self._url)
                self._connection = connection
            except ErrNoServers as exc:  # pragma: no cover - depends on external service
                raise RuntimeError("Unable to connect to NATS") from exc

    async def close(self) -> None:
        """Close the underlying connection."""

        if self._connection is None:
            return
        await self._connection.close()
        self._connection = None

    async def request(self, subject: str, payload: dict[str, Any], timeout: float) -> Msg:
        """Send a request and await the response."""

        if self._connection is None:
            await self.connect()
        assert self._connection is not None  # for type-checkers
        data = json.dumps(payload).encode("utf-8")
        return await self._connection.request(subject, data, timeout=timeout)


nats_client = NATSClient(url=os.getenv("NATS_URL", DEFAULT_NATS_URL))


def get_nats_client() -> NATSClient:
    """Dependency hook for FastAPI routes."""

    return nats_client


app = FastAPI(title="Agent OS API Gateway")


@app.on_event("startup")
async def _startup_event() -> None:
    await nats_client.connect()


@app.on_event("shutdown")
async def _shutdown_event() -> None:
    await nats_client.close()


@app.post("/command", response_model=CommandResponse)
async def submit_command(
    request: CommandRequest, client: NATSClient = Depends(get_nats_client)
) -> JSONResponse:
    """Publish a job to NATS and relay the agent's response.

    The request subject strictly follows the `jobs.<command>.<agent>` format so
    that downstream agents can subscribe using wildcard patterns like
    `jobs.*.jules` or `jobs.code_generate.*`.
    """

    try:
        subject = f"jobs.{request.command}.{request.agent}"
        LOGGER.info("Publishing job to subject %s", subject)
        response_msg = await client.request(
            subject, {"payload": request.payload}, timeout=request.timeout_seconds
        )
    except ErrTimeout as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timed out waiting for agent response",
        ) from exc
    except (ErrConnectionClosed, RuntimeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="NATS connection unavailable",
        ) from exc

    agent_response = json.loads(response_msg.data.decode("utf-8"))
    response_body = CommandResponse(
        status=agent_response.get("status", "ok"),
        result=agent_response.get("result"),
        agent=request.agent,
        command=request.command,
    )
    return JSONResponse(status_code=status.HTTP_200_OK, content=response_body.dict())


__all__ = ["app", "get_nats_client", "CommandRequest", "CommandResponse"]
