"""Simple in-memory vector store for semantic retrieval experiments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np


@dataclass
class VectorDocument:
    """Represents a document embedding stored in the vector index."""

    doc_id: str
    embedding: np.ndarray
    metadata: Dict[str, object]


class VectorStore:
    """Minimal vector index with cosine similarity search."""

    def __init__(self) -> None:
        self._documents: Dict[str, VectorDocument] = {}

    def upsert(
        self, doc_id: str, embedding: Sequence[float], **metadata: object
    ) -> None:
        vector = np.asarray(embedding, dtype=np.float32)
        self._documents[doc_id] = VectorDocument(
            doc_id=doc_id,
            embedding=vector,
            metadata=dict(metadata),
        )

    def query(
        self, embedding: Sequence[float], top_k: int = 5
    ) -> List[Tuple[str, float]]:
        if not self._documents:
            return []
        target = np.asarray(embedding, dtype=np.float32)
        target_norm = np.linalg.norm(target)
        scores: List[Tuple[str, float]] = []
        for doc in self._documents.values():
            denom = target_norm * (np.linalg.norm(doc.embedding) + 1e-9)
            numerator = float(np.dot(target, doc.embedding))
            score = numerator / denom if denom else 0.0
            scores.append((doc.doc_id, score))
        scores.sort(key=lambda item: item[1], reverse=True)
        return scores[:top_k]

    def documents(self) -> Iterable[VectorDocument]:
        return tuple(self._documents.values())
