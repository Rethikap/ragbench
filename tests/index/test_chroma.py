"""Chroma persistence, tested against the real database.

One test file, deliberately thin: everything about the index *pipeline* is
tested against MemoryStore, and what is left to check here is that Chroma keeps
what it is given across a process boundary, which is the only reason it is in
the design at all.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

chromadb = pytest.importorskip("chromadb")

from ragbench.index.store import ChromaStore  # noqa: E402


def vectors(count: int, dimension: int = 8) -> np.ndarray:
    rows = np.arange(count * dimension, dtype=np.float32).reshape(count, dimension)
    return rows / np.linalg.norm(rows, axis=1, keepdims=True)


def test_a_collection_survives_being_reopened(tmp_path: Path) -> None:
    """The point of persistence: a run that stopped can be continued by a
    different process, which is what resumability means once the data is on disk
    rather than in a dict."""
    store = ChromaStore(tmp_path / "chroma", "ix0123456789")
    store.add(["a", "b"], vectors(2), ["alpha", "beta"], [{"pmcid": "PMC1"}] * 2)
    assert store.count() == 2

    reopened = ChromaStore(tmp_path / "chroma", "ix0123456789")
    assert reopened.count() == 2
    assert reopened.existing_ids(["a", "b", "c"]) == {"a", "b"}


def test_the_collection_is_named_by_the_index_id(tmp_path: Path) -> None:
    """One collection per index, named from the cache key, so two of the four
    cannot land in the same place."""
    first = ChromaStore(tmp_path / "chroma", "aaaa11112222")
    second = ChromaStore(tmp_path / "chroma", "bbbb33334444")
    first.add(["x"], vectors(1), ["one"], [{"pmcid": "PMC1"}])
    assert first.count() == 1
    assert second.count() == 0
    assert second.existing_ids(["x"]) == set()


def test_rewriting_an_id_does_not_fail(tmp_path: Path) -> None:
    """A run interrupted between embedding a batch and recording it retries that
    batch; upsert is what stops the retry dying on a duplicate id."""
    store = ChromaStore(tmp_path / "chroma", "cccc55556666")
    store.add(["a"], vectors(1), ["alpha"], [{"pmcid": "PMC1"}])
    store.add(["a"], vectors(1), ["alpha"], [{"pmcid": "PMC1"}])
    assert store.count() == 1


def test_an_empty_batch_is_a_no_op(tmp_path: Path) -> None:
    store = ChromaStore(tmp_path / "chroma", "dddd77778888")
    store.add([], np.zeros((0, 8), dtype=np.float32), [], [])
    assert store.count() == 0
    assert store.existing_ids([]) == set()
