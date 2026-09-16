"""Vector indexes: four of them, one per (chunk set, embedding arm) pair.

Chroma is imported inside `store.ChromaStore`, and torch inside the embedders,
so importing this package costs numpy and nothing more.
"""

from __future__ import annotations

from .pipeline import build_one_index, load_index_meta, run_index, truncation_census

__all__ = ["build_one_index", "load_index_meta", "run_index", "truncation_census"]
