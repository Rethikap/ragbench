"""Retrieval metrics computed against character-span gold labels.

Two modules, two questions. :mod:`~ragbench.eval.spans` asks whether the
generator can see the answer; :mod:`~ragbench.eval.context` asks what else is in
the window with it. The second exists because the first saturates: on a gold set
whose spans both arms hold in a single chunk, coverage, Recall@k and nDCG@10 are
all 1.0 for both, and the arms still differ in precision, position and noise.

Kept apart from ``report/`` because these are measurements, not renderings, and
apart from ``retrieval/`` because nothing here retrieves anything -- a metric
that could reach into the retriever could accidentally define correctness in
terms of it.
"""

from __future__ import annotations

from .context import (
    context_profile,
    distractor_count,
    evidence_density,
    gold_chunk_rank,
)
from .spans import (
    covering_chunks,
    minimum_cover,
    ndcg_at_k,
    recall_at_k,
    span_coverage,
)

__all__ = [
    "context_profile",
    "covering_chunks",
    "distractor_count",
    "evidence_density",
    "gold_chunk_rank",
    "minimum_cover",
    "ndcg_at_k",
    "recall_at_k",
    "span_coverage",
]
