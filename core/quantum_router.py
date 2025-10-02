"""Adaptive agent routing engine used by the terminal."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional

from db.audit_log import AuditLogger
from common.protocol import EventType


@dataclass
class AgentCapability:
    """Represents the capabilities of a registered agent."""

    strengths: Iterable[str]
    token_efficiency: float
    latency_ms: int


class QuantumRouter:
    """Selects the most appropriate agent for a given command."""

    def __init__(
        self,
        audit_logger: Optional[AuditLogger] = None,
        capability_matrix: Optional[Mapping[str, AgentCapability]] = None,
    ) -> None:
        self.audit_logger = audit_logger or AuditLogger()
        self.agent_matrix: Dict[str, AgentCapability]
        if capability_matrix:
            self.agent_matrix = dict(capability_matrix)
        else:
            self.agent_matrix = self._default_matrix()

    async def route(
        self,
        command: str,
        context: Mapping[str, Any],
    ) -> Dict[str, Any]:
        candidate = context.get("trace_id") or context.get("traceId")
        trace_id = str(candidate or "trace-unknown")
        self._audit(
            EventType.AI_SYNTHESIS_REQUEST,
            trace_id,
            {"command": command},
        )
        intent = self._extract_intent(command)
        agent_scores = {
            agent_id: self._score_agent(capabilities, intent)
            for agent_id, capabilities in self.agent_matrix.items()
        }
        optimal_agent = max(agent_scores, key=agent_scores.get)
        result = await self._execute(optimal_agent, command, context)
        self._audit(
            EventType.AI_SYNTHESIS_COMPLETED,
            trace_id,
            {
                "agent": optimal_agent,
                "alternatives": agent_scores,
                "intent": intent,
            },
        )
        return {
            "agent": optimal_agent,
            "result": result,
            "alternatives": agent_scores,
        }

    def register_agent(
        self,
        agent_id: str,
        capabilities: AgentCapability,
    ) -> None:
        self.agent_matrix[agent_id] = capabilities

    def _score_agent(
        self, capabilities: AgentCapability, intent: Dict[str, Any]
    ) -> float:
        keywords = set(intent.get("keywords", []))
        strengths = set(capabilities.strengths)
        overlap = len(keywords.intersection(strengths))
        return overlap * capabilities.token_efficiency

    def _extract_intent(self, command: str) -> Dict[str, Any]:
        lowered = command.lower()
        keywords = [
            keyword
            for keyword in ("code", "security", "graph", "query")
            if keyword in lowered
        ]
        complexity = 5 if len(command) > 200 else 2
        return {"keywords": keywords, "complexity": complexity}

    async def _execute(
        self, agent: str, command: str, context: Mapping[str, Any]
    ) -> Dict[str, Any]:
        await asyncio.sleep(0)  # Placeholder for network I/O
        return {
            "status": "ok",
            "echo": command,
            "context": dict(context),
        }

    def _audit(
        self, event_type: EventType, trace_id: str, payload: Dict[str, Any]
    ) -> None:
        self.audit_logger.log(
            "quantum_router",
            {"event": event_type.value, "trace_id": trace_id, **payload},
        )

    def _default_matrix(self) -> Dict[str, AgentCapability]:
        return {
            "@claude": AgentCapability(
                strengths=("reasoning", "code_analysis", "security"),
                token_efficiency=0.92,
                latency_ms=1200,
            ),
            "@openai": AgentCapability(
                strengths=("function_calling", "vision", "structured_output"),
                token_efficiency=0.88,
                latency_ms=800,
            ),
            "@diego": AgentCapability(
                strengths=("domain_context", "decision_authority"),
                token_efficiency=1.0,
                latency_ms=0,
            ),
        }
