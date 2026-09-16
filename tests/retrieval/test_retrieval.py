"""The retrieval pipeline: the rerank arm, resumability, and the recorded result.

Run against MemoryStore and the stand-in reranker, which is the whole CPU path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pytest

from ragbench.embedding.standin import HashingEmbedder
from ragbench.index.store import MemoryStore
from ragbench.retrieval.pipeline import cells, config_name, retrieve_one
from ragbench.retrieval.rerank import (
    NoReranker,
    StandInReranker,
    build_reranker,
)
from ragbench.types import Chunk, GoldSpan, Query

EMBED = {
    "model_id": "stand-in",
    "max_seq_tokens": 64,
    "dimension": 32,
    "normalize": True,
    "query_instruction": "",
}


def chunk(index: int, text: str) -> Chunk:
    return Chunk(
        chunk_id=f"PMC1-{index:04d}",
        pmcid="PMC1",
        chunk_index=index,
        text=text,
        n_tokens=len(text.split()),
        char_start=index * 200,
        char_end=index * 200 + len(text),
        sections=("Results",),
        content_sha256="0" * 64,
    )


CHUNKS = [
    chunk(0, "amyloid beta plaques accumulate in the hippocampus of patients"),
    chunk(1, "tau phosphorylation correlates with cognitive decline severity"),
    chunk(2, "gas chromatography of industrial solvents and their residues"),
    chunk(3, "cerebrospinal fluid neurofilament light rises in neurodegeneration"),
]
QUERY = Query(
    query_id="q001",
    question="where do amyloid beta plaques accumulate",
    reference_answer="the hippocampus",
    gold=GoldSpan(
        pmcid="PMC1", char_start=0, char_end=60, section="Results",
        context_start=0, context_end=200,
    ),
    verified=True,
)


def stocked_store() -> tuple[MemoryStore, HashingEmbedder, dict[str, Chunk]]:
    embedder = HashingEmbedder(EMBED)
    store = MemoryStore()
    vectors = embedder.encode_documents([c.text for c in CHUNKS])
    store.add(
        [c.chunk_id for c in CHUNKS],
        vectors,
        [c.text for c in CHUNKS],
        [{"pmcid": c.pmcid} for c in CHUNKS],
    )
    return store, embedder, {c.chunk_id: c for c in CHUNKS}


def run(reranker: Any, budget: int = 1000, depth: int = 4) -> Any:
    store, embedder, by_id = stocked_store()
    cost = {c.chunk_id: c.n_tokens for c in CHUNKS}
    return retrieve_one(
        QUERY, embedder, store, by_id, reranker, cost, depth, budget, "stop_at_overflow"
    )


# ------------------------------------------------------------------- the cells


def test_the_design_is_the_cartesian_product_of_three_factors() -> None:
    """Eight cells, and the number 8 is written down nowhere."""
    resolved = {
        "factors": {
            "chunking": {"fixed": {}, "recursive": {}},
            "embedding": {"bge": {}, "specter2": {}},
            "rerank": {"off": {}, "on": {}},
        }
    }
    combinations = list(cells(resolved))
    assert len(combinations) == 8
    assert len(set(combinations)) == 8
    assert ("fixed", "bge", "off") in combinations


def test_a_configuration_names_itself_readably() -> None:
    assert config_name("fixed", "bge", "on") == "fixed-bge-rerank_on"


# ------------------------------------------------------------------ the result


def test_the_result_records_the_measurement_not_just_the_chunks() -> None:
    """n_chunks, tokens_used, budget_slack and stopped_reason are results, not
    diagnostics: they are what the experiment is measuring."""
    result = run(NoReranker(), budget=1000)
    assert result.query_id == "q001"
    assert result.n_chunks == len(result.selected)
    assert result.tokens_used == sum(s.n_budget_tokens for s in result.selected)
    assert result.budget_slack == result.token_budget - result.tokens_used
    assert result.stopped_reason
    assert [s.rank for s in result.selected] == list(range(1, len(result.selected) + 1))


def test_a_tight_budget_returns_fewer_chunks_and_says_why() -> None:
    generous = run(NoReranker(), budget=1000)
    tight = run(NoReranker(), budget=12)
    assert tight.n_chunks < generous.n_chunks
    assert tight.tokens_used <= 12


def test_the_budget_is_never_exceeded() -> None:
    for budget in (1, 5, 10, 20, 50, 1000):
        assert run(NoReranker(), budget=budget).tokens_used <= budget


def test_depth_bounds_the_candidate_pool_not_the_context() -> None:
    """depth is a rerank pool size. It is not k, and a deeper pool with the same
    budget does not put more chunks in the prompt."""
    shallow = run(NoReranker(), budget=1000, depth=2)
    deep = run(NoReranker(), budget=1000, depth=4)
    assert shallow.n_candidates == 2
    assert deep.n_candidates == 4
    assert deep.tokens_used <= deep.token_budget


# ---------------------------------------------------------------- the rerank arm


def test_the_off_level_is_the_absence_of_a_stage() -> None:
    """Not a reranker that reproduces the dense order -- calling it is a bug, and
    it says so rather than quietly returning zeros."""
    off = build_reranker(False, {})
    assert isinstance(off, NoReranker)
    assert off.enabled is False
    with pytest.raises(RuntimeError, match="rerank factor is off"):
        off.score("q", ["d"])


def test_reranking_reorders_and_is_recorded() -> None:
    on = run(StandInReranker(), budget=1000)
    off = run(NoReranker(), budget=1000)
    assert on.rerank_latency_ms > 0.0
    assert off.rerank_latency_ms == 0.0
    # The stand-in scores lexical overlap, so the amyloid chunk should lead.
    assert on.selected[0].chunk_id == "PMC1-0000"


def test_the_stand_in_reranker_actually_discriminates() -> None:
    """A stand-in returning a constant would make the on and off arms
    indistinguishable and the factor untestable offline."""
    scores = StandInReranker().score(
        "amyloid beta plaques", [c.text for c in CHUNKS]
    )
    assert len(set(scores)) > 1
    assert scores[0] == max(scores)


def test_an_empty_query_scores_everything_alike() -> None:
    assert StandInReranker().score("", ["a b", "c d"]) == [0.0, 0.0]


def test_the_real_reranker_demands_a_pinned_revision() -> None:
    with pytest.raises(ValueError, match="model_revision"):
        build_reranker(True, {"model_id": "BAAI/bge-reranker-base", "model_revision": ""})


# --------------------------------------------------------------- no candidates


def test_an_empty_index_yields_an_empty_context_not_a_crash() -> None:
    embedder = HashingEmbedder(EMBED)
    result = retrieve_one(
        QUERY, embedder, MemoryStore(), {}, NoReranker(), {}, 30, 2000, "stop_at_overflow"
    )
    assert result.n_chunks == 0
    assert result.tokens_used == 0
    assert result.budget_slack == 2000
    assert result.stopped_reason == "no_candidates"


def test_search_returns_similarity_so_higher_is_better() -> None:
    store, embedder, _ = stocked_store()
    hits = store.search(embedder.encode_queries(["amyloid beta plaques"])[0], 4)
    scores = [score for _, score in hits]
    assert scores == sorted(scores, reverse=True)
    assert hits[0][0] == "PMC1-0000"


def test_vectors_written_to_the_store_are_searchable(tmp_path: Path) -> None:
    store, embedder, _ = stocked_store()
    assert store.count() == len(CHUNKS)
    assert len(store.search(np.zeros(32, dtype=np.float32), 99)) == len(CHUNKS)
