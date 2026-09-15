"""Retrieval metrics computed against character-span gold labels.

Kept apart from ``report/`` because these are measurements, not renderings, and
apart from ``retrieval/`` because nothing here retrieves anything -- a metric
that could reach into the retriever could accidentally define correctness in
terms of it.
"""

from __future__ import annotations

from .spans import (
    covering_chunks,
    minimum_cover,
    ndcg_at_k,
    recall_at_k,
    span_coverage,
)

__all__ = [
    "covering_chunks",
    "minimum_cover",
    "ndcg_at_k",
    "recall_at_k",
    "span_coverage",
]
