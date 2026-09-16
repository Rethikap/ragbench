"""Retrieval orchestration: dense search, optional rerank, fill to the budget.

One `RetrievalResult` per query per configuration, appended to JSONL keyed by
query id. Re-running skips what is already there, so an interrupted run
continues and a finished one does nothing.

The three factor levels reach this module as names, and the artefacts they
select reach it as ids. Nothing here knows how a chunk was cut or how a vector
was made; what it does know is the token budget, and that is the one number the
experiment holds constant.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import Any

from ..cache_keys import chunk_set_key, index_key
from ..chunking.pipeline import arm_params as chunking_params
from ..chunking.pipeline import load_chunks
from ..config import chunk_set_dir, index_dir
from ..embedding.base import arm_params as embedding_params
from ..embedding.base import build_embedder
from ..gold.freeze import GOLD_SET_FILENAME, verify_frozen
from ..index.store import ChromaStore, VectorStore
from ..jsonl import append_jsonl, read_jsonl
from ..tokenizers import load_tokenizer
from ..types import Chunk, Query, RetrievalResult, ScoredChunk
from .budget import fill_to_budget
from .rerank import build_reranker

Progress = Callable[[str], None] | None


def config_name(chunking: str, embedding: str, rerank: str) -> str:
    """The filename one configuration writes to. Readable on purpose: a run
    directory should say which of the 8 cells each file holds."""
    return f"{chunking}-{embedding}-rerank_{rerank}"


def results_path(run_directory: Path, chunking: str, embedding: str, rerank: str) -> Path:
    return Path(run_directory) / "retrieve" / f"{config_name(chunking, embedding, rerank)}.jsonl"


def load_results(path: Path) -> list[RetrievalResult]:
    return [RetrievalResult.from_dict(record) for record in read_jsonl(path)]


def retrieve_one(
    query: Query,
    embedder: Any,
    store: VectorStore,
    chunks_by_id: dict[str, Chunk],
    reranker: Any,
    cost: dict[str, int],
    depth: int,
    budget: int,
    fill_policy: str,
) -> RetrievalResult:
    """One query, one configuration. The only place the budget is spent."""
    started = time.perf_counter()
    vector = embedder.encode_queries([query.question])[0]
    hits = store.search(vector, depth)
    dense_ms = (time.perf_counter() - started) * 1000.0

    rerank_ms = 0.0
    if reranker.enabled and hits:
        started = time.perf_counter()
        documents = [chunks_by_id[identifier].text for identifier, _ in hits]
        scores = reranker.score(query.question, documents)
        # Stable within equal scores: sorted() is stable, so the dense order
        # survives a tie rather than being shuffled by the sort.
        order = sorted(range(len(hits)), key=lambda i: -scores[i])
        hits = [(hits[i][0], float(scores[i])) for i in order]
        rerank_ms = (time.perf_counter() - started) * 1000.0

    # THE fill. How many chunks come back is the answer, not the question.
    filled = fill_to_budget(hits, lambda hit: cost[hit[0]], budget, fill_policy)

    selected = tuple(
        ScoredChunk(
            chunk_id=identifier,
            score=round(float(score), 6),
            rank=position,
            n_budget_tokens=cost[identifier],
        )
        for position, (identifier, score) in enumerate(filled.selected, start=1)
    )
    return RetrievalResult(
        query_id=query.query_id,
        selected=selected,
        n_candidates=len(hits),
        n_chunks=len(selected),
        tokens_used=filled.tokens_used,
        token_budget=budget,
        budget_slack=budget - filled.tokens_used,
        stopped_reason=filled.stopped_reason,
        dense_latency_ms=round(dense_ms, 2),
        rerank_latency_ms=round(rerank_ms, 2),
    )


def retrieve_one_config(
    resolved: dict[str, Any],
    chunking_level: str,
    embedding_level: str,
    rerank_level: str,
    configs_dir: Path,
    data_root: Path,
    run_directory: Path,
    store: VectorStore | None = None,
    on_progress: Progress = None,
) -> dict[str, Any]:
    """One of the 8 cells, resumable at query granularity."""
    corpus = resolved["corpus"]
    digest = str(corpus.get("manifest_sha", ""))
    retrieval = resolved["base"]["retrieval"]
    budget = int(retrieval["context_token_budget"])
    depth = int(retrieval["depth"])

    queries = verify_frozen(
        Path(configs_dir) / GOLD_SET_FILENAME, str(resolved["gold"].get("gold_set_sha", ""))
    )

    chunk_params = chunking_params(resolved, chunking_level)
    chunk_set_id = chunk_set_key(digest, chunk_params)
    chunks = load_chunks(chunk_set_dir(chunk_set_id, data_root))
    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}

    embed_params = embedding_params(resolved, embedding_level)
    identifier = index_key(
        chunk_set_id,
        str(embed_params["model_id"]),
        str(embed_params.get("model_revision") or ""),
        embed_params.get("adapter_id"),
        embed_params.get("adapter_revision"),
    )
    target = index_dir(identifier, data_root)
    if store is None:
        if not (target / "index.json").is_file():
            raise ValueError(
                f"index for {chunking_level}/{embedding_level} not built; "
                "run `ragbench index` first"
            )
        store = ChromaStore(target / "chroma", identifier)

    # The budget is measured with the GENERATOR's tokenizer, because it is the
    # generator's context being controlled -- not the embedder's, not the
    # chunker's. Computed once per configuration and passed in, so the fill
    # cannot reach for a different one.
    budget_tokenizer = load_tokenizer(
        retrieval["budget_tokenizer_id"], retrieval["budget_tokenizer_revision"]
    )
    cost = {chunk.chunk_id: budget_tokenizer.count(chunk.text) for chunk in chunks}

    rerank_params = {**resolved["base"]["rerank"], **resolved["factors"]["rerank"][rerank_level]}
    reranker = build_reranker(bool(rerank_params.get("enabled")), rerank_params)
    embedder = build_embedder(embed_params)

    path = results_path(run_directory, chunking_level, embedding_level, rerank_level)
    done = {record["query_id"] for record in read_jsonl(path)}
    written = 0
    for position, query in enumerate(queries, start=1):
        if query.query_id in done:
            continue
        result = retrieve_one(
            query, embedder, store, chunks_by_id, reranker, cost, depth, budget,
            str(retrieval["fill_policy"]),
        )
        append_jsonl(path, result.to_dict())
        written += 1
        if on_progress:
            on_progress(
                f"{config_name(chunking_level, embedding_level, rerank_level)}: "
                f"{position}/{len(queries)} queries"
            )

    results = load_results(path)
    return {
        "config": config_name(chunking_level, embedding_level, rerank_level),
        "chunking_level": chunking_level,
        "embedding_level": embedding_level,
        "rerank_level": rerank_level,
        "chunk_set_id": chunk_set_id,
        "index_id": identifier,
        "embedder": embedder.name,
        "reranker": reranker.name,
        "depth": depth,
        "token_budget": budget,
        "fill_policy": retrieval["fill_policy"],
        "n_queries": len(results),
        "queries_written": written,
        "queries_reused": len(results) - written,
        "path": str(path),
    }


def cells(resolved: dict[str, Any]) -> Iterator[tuple[str, str, str]]:
    """The Cartesian product of the three factors, in a stable order. The number
    8 appears nowhere: adding a level changes the experiment's size here."""
    for chunking in resolved["factors"]["chunking"]:
        for embedding in resolved["factors"]["embedding"]:
            for rerank in resolved["factors"]["rerank"]:
                yield chunking, embedding, rerank


def run_retrieve(
    resolved: dict[str, Any],
    configs_dir: Path,
    data_root: Path,
    run_directory: Path,
    levels: Sequence[tuple[str, str, str]] | None = None,
    on_progress: Progress = None,
) -> list[dict[str, Any]]:
    wanted = list(levels) if levels else list(cells(resolved))
    reports = [
        retrieve_one_config(
            resolved, chunking, embedding, rerank, configs_dir, data_root,
            run_directory, on_progress=on_progress,
        )
        for chunking, embedding, rerank in wanted
    ]
    summary = Path(run_directory) / "retrieve" / "summary.json"
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(
        json.dumps(reports, indent=2, sort_keys=True), encoding="utf-8", newline=""
    )
    return reports
