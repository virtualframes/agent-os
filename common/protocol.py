# common/protocol.py
# This file defines the canonical message structures for the NATS bus.
# It is the single source of truth for inter-service communication.
# A failure to adhere to this contract is a failure of the system.

import msgpack
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, Any


class JobType(str, Enum):
    """Enumerates the types of jobs agents can perform."""

    CODE_GENERATE = "code.generate"
    CODE_REFACTOR = "code.refactor"
    CODE_FIX = "code.fix"
    GENERAL_QUERY = "general.query"


@dataclass
class JobRequest:
    """
    Message published by the Gateway to request work from an agent.
    """

    trace_id: str
    job_type: JobType
    target_agent: str  # e.g., "claude", "codex", "jules"
    payload: Dict[str, Any]  # Job-specific data, e.g., {"code": "...", "language": "python"}
    user_id: str

    def to_bytes(self) -> bytes:
        # Use a dict factory to handle enum serialization
        data = asdict(
            self,
            dict_factory=lambda d: {
                k: v.value if isinstance(v, Enum) else v for k, v in d
            },
        )
        return msgpack.packb(data)

    @classmethod
    def from_bytes(cls, data: bytes):
        payload = msgpack.unpackb(data, raw=False)
        payload["job_type"] = JobType(payload["job_type"])
        return cls(**payload)


@dataclass
class JobResult:
    """
    Message published by an agent to signal completion or stream a result.
    """

    trace_id: str
    is_complete: bool
    is_error: bool
    payload: Dict[str, Any]  # The result, e.g., {"code": "...", "explanation": "..."} or {"error": "..."}

    def to_bytes(self) -> bytes:
        return msgpack.packb(asdict(self))

    @classmethod
    def from_bytes(cls, data: bytes):
        return cls(**msgpack.unpackb(data, raw=False))
