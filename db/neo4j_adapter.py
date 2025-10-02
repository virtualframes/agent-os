"""Lightweight Neo4j adapter used by the spacetime graph engine.

The real implementation would wrap the official Neo4j Python driver. For the
scaffold we expose the minimal operations required by :mod:`core.graph_engine`
while storing data in memory. This keeps the API surface stable so future work
can drop in a proper database-backed adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, MutableMapping


@dataclass
class GraphNode:
    """Represents a node stored inside the adapter."""

    id: str
    label: str
    properties: MutableMapping[str, object]


@dataclass
class GraphEdge:
    """Represents a relationship between two nodes."""

    from_id: str
    to_id: str
    relationship: str
    weight: float


class Neo4jAdapter:
    """In-memory Neo4j stand-in used for development and tests."""

    def __init__(self) -> None:
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: List[GraphEdge] = []

    def create_node(
        self,
        node_id: str,
        label: str,
        **properties: object,
    ) -> GraphNode:
        node = GraphNode(id=node_id, label=label, properties=dict(properties))
        self._nodes[node_id] = node
        return node

    def create_edge(
        self, from_id: str, to_id: str, relationship: str, weight: float = 1.0
    ) -> GraphEdge:
        edge = GraphEdge(
            from_id=from_id,
            to_id=to_id,
            relationship=relationship,
            weight=weight,
        )
        self._edges.append(edge)
        return edge

    def nodes(self) -> Iterable[GraphNode]:
        return tuple(self._nodes.values())

    def edges(self) -> Iterable[GraphEdge]:
        return tuple(self._edges)
