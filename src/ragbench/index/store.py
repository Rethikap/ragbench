"""Chroma persistence, behind a small interface.

One collection per index, named by the index cache key, so the four indexes of
the 2x2 design cannot collide and a collection's name says exactly what is in
it. The collection is opened with cosine space because both arms emit
L2-normalised vectors and cosine over those is a dot product.

The interface exists for one reason: `existing_ids` and `add`, which is all the
index stage needs, and which lets the pipeline be tested without a database.
Nothing here knows what an embedder is.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Protocol

import numpy as np


class VectorStore(Protocol):
    def existing_ids(self, ids: Sequence[str]) -> set[str]:
        """Which of ``ids`` are already stored. The basis of resumability."""

    def add(
        self,
        ids: Sequence[str],
        vectors: np.ndarray,
        documents: Sequence[str],
        metadatas: Sequence[dict[str, Any]],
    ) -> None:
        """Write a batch. Must be safe to call after an interrupted run."""

    def count(self) -> int:
        """Vectors stored."""


class ChromaStore:
    """A persistent Chroma collection. chromadb is imported here, not at module
    scope, so `import ragbench.index` stays cheap."""

    def __init__(self, directory: Path, collection: str) -> None:
        import chromadb

        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(directory))
        self._collection = self._client.get_or_create_collection(
            name=collection,
            # Both arms normalise, so cosine is a dot product; saying so lets
            # Chroma pick the right distance rather than defaulting to L2.
            metadata={"hnsw:space": "cosine"},
        )
        self.name = collection

    def existing_ids(self, ids: Sequence[str]) -> set[str]:
        if not ids:
            return set()
        found = self._collection.get(ids=list(ids), include=[])
        return set(found.get("ids", []))

    def add(
        self,
        ids: Sequence[str],
        vectors: np.ndarray,
        documents: Sequence[str],
        metadatas: Sequence[dict[str, Any]],
    ) -> None:
        if not len(ids):
            return
        # upsert rather than add: a run interrupted between embedding a batch
        # and recording it must not fail on the retry with a duplicate id.
        self._collection.upsert(
            ids=list(ids),
            embeddings=[vector.tolist() for vector in vectors],
            documents=list(documents),
            metadatas=list(metadatas),
        )

    def count(self) -> int:
        return int(self._collection.count())


class MemoryStore:
    """In-process stand-in with the same contract, for tests that are about the
    pipeline's resumability rather than about Chroma."""

    def __init__(self) -> None:
        self.vectors: dict[str, np.ndarray] = {}
        self.documents: dict[str, str] = {}
        self.metadatas: dict[str, dict[str, Any]] = {}
        self.name = "memory"

    def existing_ids(self, ids: Sequence[str]) -> set[str]:
        return {identifier for identifier in ids if identifier in self.vectors}

    def add(
        self,
        ids: Sequence[str],
        vectors: np.ndarray,
        documents: Sequence[str],
        metadatas: Sequence[dict[str, Any]],
    ) -> None:
        for position, identifier in enumerate(ids):
            self.vectors[identifier] = vectors[position]
            self.documents[identifier] = documents[position]
            self.metadatas[identifier] = metadatas[position]

    def count(self) -> int:
        return len(self.vectors)
