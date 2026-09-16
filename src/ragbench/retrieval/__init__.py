"""Dense retrieval, optional reranking, and the budget fill (invariant I1).

There is no `k` in this package. The number of chunks that reach the generator
is an output of filling a constant token budget, and a function that took a
count and returned that many chunks would make the wrong experiment expressible.
"""

from __future__ import annotations

from .budget import (
    FILL_POLICIES,
    STOPPED_EMPTY,
    STOPPED_EXHAUSTED,
    STOPPED_OVERFLOW,
    fill_to_budget,
)
from .pipeline import cells, config_name, load_results, results_path, run_retrieve
from .rerank import build_reranker

__all__ = [
    "FILL_POLICIES",
    "STOPPED_EMPTY",
    "STOPPED_EXHAUSTED",
    "STOPPED_OVERFLOW",
    "build_reranker",
    "cells",
    "config_name",
    "fill_to_budget",
    "load_results",
    "results_path",
    "run_retrieve",
]
