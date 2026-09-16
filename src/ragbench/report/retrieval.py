"""Scoring what retrieval returned, with the metrics that already exist.

The retriever records what it retrieved; this scores it. Keeping the two apart
is the reason :mod:`ragbench.eval` imports nothing from the retrieval path — a
metric that could reach into the retriever could define correctness in terms of
it.

Six metrics per query, aggregated per configuration. Span coverage is primary
and the two rank metrics are secondary (I5); the three window metrics are what
still discriminate once coverage saturates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..cache_keys import chunk_set_key
from ..chunking.pipeline import arm_params as chunking_params
from ..chunking.pipeline import load_chunks
from ..config import chunk_set_dir
from ..eval.context import distractor_count, evidence_density, gold_chunk_rank
from ..eval.spans import ndcg_at_k, recall_at_k, span_coverage
from ..gold.freeze import GOLD_SET_FILENAME, verify_frozen
from ..retrieval.pipeline import load_results, results_path
from ..types import Chunk, Query, RetrievalResult
from .chunks import distribution

RANK_K = 10


def score_query(
    query: Query, result: RetrievalResult, chunks_by_id: dict[str, Chunk], chunks: list[Chunk]
) -> dict[str, Any]:
    """Every metric for one query, over the context as it was assembled."""
    ordered = [chunks_by_id[scored.chunk_id] for scored in result.selected]
    position = gold_chunk_rank(query.gold, ordered, lambda chunk: chunk.n_tokens)
    return {
        "query_id": query.query_id,
        "pmcid": query.gold.pmcid,
        "n_chunks": result.n_chunks,
        "tokens_used": result.tokens_used,
        "budget_slack": result.budget_slack,
        "stopped_reason": result.stopped_reason,
        "n_candidates": result.n_candidates,
        # Primary.
        "span_coverage": round(span_coverage(query.gold, ordered), 6),
        # What still moves once coverage saturates.
        "evidence_density": round(evidence_density(query.gold, ordered), 6),
        "distractor_count": distractor_count(query.gold, ordered),
        "gold_rank": position["rank"],
        "tokens_before_gold": position["tokens_before"],
        # Secondary, reported for comparability with the literature.
        "recall_at_10": round(recall_at_k(query.gold, ordered, chunks, RANK_K), 6),
        "ndcg_at_10": round(ndcg_at_k(query.gold, ordered, chunks, RANK_K), 6),
    }


def _aggregate(rows: list[dict[str, Any]], budget: int) -> dict[str, Any]:
    def mean(key: str) -> float:
        values = [float(row[key]) for row in rows]
        return round(sum(values) / len(values), 4) if values else 0.0

    found = [row for row in rows if row["gold_rank"] is not None]
    stopped: dict[str, int] = {}
    for row in rows:
        stopped[row["stopped_reason"]] = stopped.get(row["stopped_reason"], 0) + 1
    return {
        "n_queries": len(rows),
        "chunks_per_context": distribution([int(row["n_chunks"]) for row in rows]),
        "tokens_used": distribution([int(row["tokens_used"]) for row in rows]),
        "budget_slack": distribution([int(row["budget_slack"]) for row in rows]),
        # Realised against nominal: how much of the constant budget each
        # configuration actually managed to spend. The gap is a granularity
        # cost, and stop_at_overflow is what turns chunk size into slack.
        "realised_budget_share": round(mean("tokens_used") / budget, 4) if budget else 0.0,
        "span_coverage": mean("span_coverage"),
        "evidence_density": mean("evidence_density"),
        "distractor_count": mean("distractor_count"),
        "recall_at_10": mean("recall_at_10"),
        "ndcg_at_10": mean("ndcg_at_10"),
        "gold_found": len(found),
        "mean_gold_rank": round(
            sum(int(row["gold_rank"]) for row in found) / len(found), 2
        )
        if found
        else None,
        "mean_tokens_before_gold": round(
            sum(int(row["tokens_before_gold"]) for row in found) / len(found), 1
        )
        if found
        else None,
        "stopped_reason": dict(sorted(stopped.items())),
    }


def build_report(
    resolved: dict[str, Any], configs_dir: Path, data_root: Path, run_directory: Path
) -> dict[str, Any]:
    queries = verify_frozen(
        Path(configs_dir) / GOLD_SET_FILENAME, str(resolved["gold"].get("gold_set_sha", ""))
    )
    by_id = {query.query_id: query for query in queries}
    digest = str(resolved["corpus"].get("manifest_sha", ""))
    budget = int(resolved["base"]["retrieval"]["context_token_budget"])

    chunk_sets: dict[str, list[Chunk]] = {}
    configs: list[dict[str, Any]] = []
    from ..retrieval.pipeline import cells, config_name

    for chunking, embedding, rerank in cells(resolved):
        path = results_path(run_directory, chunking, embedding, rerank)
        results = load_results(path)
        if not results:
            raise ValueError(
                f"no retrieval results for {config_name(chunking, embedding, rerank)}; "
                "run `ragbench retrieve` first"
            )
        if chunking not in chunk_sets:
            params = chunking_params(resolved, chunking)
            chunk_sets[chunking] = load_chunks(
                chunk_set_dir(chunk_set_key(digest, params), data_root)
            )
        chunks = chunk_sets[chunking]
        chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
        rows = [
            score_query(by_id[result.query_id], result, chunks_by_id, chunks)
            for result in results
            if result.query_id in by_id
        ]
        configs.append(
            {
                "config": config_name(chunking, embedding, rerank),
                "chunking": chunking,
                "embedding": embedding,
                "rerank": rerank,
                "per_query": rows,
                **_aggregate(rows, budget),
            }
        )

    return {
        "gold_set_sha": resolved["gold"].get("gold_set_sha"),
        "manifest_sha": digest,
        "token_budget": budget,
        "depth": int(resolved["base"]["retrieval"]["depth"]),
        "fill_policy": resolved["base"]["retrieval"]["fill_policy"],
        "rank_k": RANK_K,
        "configs": configs,
    }
