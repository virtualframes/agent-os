"""3D spacetime knowledge graph utilities."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np

from db.neo4j_adapter import Neo4jAdapter
from db.vector_store import VectorStore


@dataclass
class Node3D:
    """Represents a node inside the spacetime graph."""

    id: str
    x: float
    y: float
    z: float
    label: str
    color: str
    weight: float
    node_type: str


@dataclass
class Edge:
    """Represents a relationship between two graph nodes."""

    from_id: str
    to_id: str
    weight: float
    relationship: str


class SpacetimeGraph:
    """Maintains an in-memory spacetime knowledge graph.

    The scaffold stores nodes inside the :class:`Neo4jAdapter` stand-in while
    exposing ergonomic helper methods for higher-level services.
    """

    DEFAULT_PALETTE: Tuple[str, ...] = (
        "#89b4fa",
        "#f38ba8",
        "#a6e3a1",
        "#cba6f7",
        "#fab387",
        "#94e2d5",
    )

    def __init__(
        self,
        adapter: Optional[Neo4jAdapter] = None,
        vector_store: Optional[VectorStore] = None,
    ) -> None:
        self.adapter = adapter or Neo4jAdapter()
        self.vector_store = vector_store or VectorStore()

    def add_node(
        self, label: str, node_type: str, metadata: Dict[str, object]
    ) -> Node3D:
        node_id = self._node_id(label, metadata)
        color = self._select_color(node_id)
        x, y = self._semantic_position(label, metadata)
        z = self._time_decay(metadata.get("created_at"))
        weight = float(metadata.get("importance", 0.5))
        node = Node3D(
            id=node_id,
            x=x,
            y=y,
            z=z,
            label=label,
            color=color,
            weight=weight,
            node_type=node_type,
        )
        self.adapter.create_node(node_id, label, **node.__dict__)
        embedding = metadata.get("embedding")
        if isinstance(embedding, (list, tuple, np.ndarray)):
            self.vector_store.upsert(
                node_id,
                embedding,
                label=label,
                node_type=node_type,
            )
        return node

    def connect(
        self, from_id: str, to_id: str, relationship: str, weight: float = 1.0
    ) -> Edge:
        edge = Edge(
            from_id=from_id,
            to_id=to_id,
            relationship=relationship,
            weight=weight,
        )
        self.adapter.create_edge(from_id, to_id, relationship, weight)
        return edge

    def validate_color_consistency(self) -> List[Tuple[str, str]]:
        mismatches: List[Tuple[str, str]] = []
        type_to_color: Dict[str, str] = {}
        for node in self.adapter.nodes():
            node_type = str(node.properties.get("node_type"))
            color = str(node.properties.get("color"))
            if (
                node_type in type_to_color
                and type_to_color[node_type] != color
            ):
                mismatches.append((node_type, node.id))
            else:
                type_to_color.setdefault(node_type, color)
        return mismatches

    def _node_id(self, label: str, metadata: Dict[str, object]) -> str:
        raw = f"{label}|{sorted(metadata.items())}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:16]

    def _select_color(self, node_id: str) -> str:
        idx = int(node_id[:2], 16) % len(self.DEFAULT_PALETTE)
        return self.DEFAULT_PALETTE[idx]

    def _semantic_position(
        self, label: str, metadata: Dict[str, object]
    ) -> Tuple[float, float]:
        seed = hashlib.sha256(
            f"{label}{metadata.get('node_type', '')}".encode("utf-8")
        ).digest()
        rng = np.random.default_rng(int.from_bytes(seed[:8], "big"))
        vec = rng.normal(size=2)
        return float(vec[0]), float(vec[1])

    def _time_decay(self, created_at: Optional[object]) -> float:
        if isinstance(created_at, str):
            try:
                timestamp = datetime.fromisoformat(created_at)
            except ValueError:
                timestamp = datetime.now(timezone.utc)
        elif isinstance(created_at, datetime):
            timestamp = created_at
        else:
            timestamp = datetime.now(timezone.utc)
        delta = datetime.now(timezone.utc) - timestamp
        return delta.total_seconds() / 86400.0
