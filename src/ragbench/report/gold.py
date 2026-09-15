"""Gold-set report: the questions, why candidates were rejected, and what each
chunking arm would have to retrieve to cover each span.

The third part is the one that matters for the design. A gold span is a fixed
range of characters, but the *units* an arm must win to cover it are not: a span
one arm holds in a single chunk may take two or three in the other. That count is
exactly the denominator Recall@k divides by, which is why this report exists
before any retrieval does -- the granularity asymmetry is a property of the
corpus and the chunkers, measurable now, not a result to be discovered later and
argued about.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..cache_keys import chunk_set_key
from ..chunking.pipeline import arm_params, load_chunks
from ..config import chunk_set_dir
from ..eval.spans import minimum_cover
from ..gold.freeze import GOLD_SET_FILENAME, read_gold_set
from ..jsonl import read_jsonl
from ..types import Chunk, Query
from .chunks import distribution


def _per_arm_cover(
    queries: list[Query], chunks: list[Chunk]
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    by_query: dict[str, dict[str, Any]] = {}
    for query in queries:
        by_query[query.query_id] = minimum_cover(query.gold, chunks)
    counts = [int(row["n_chunks_to_cover"]) for row in by_query.values()]
    histogram: dict[str, int] = {}
    for count in counts:
        histogram[str(count)] = histogram.get(str(count), 0) + 1
    summary = {
        "chunks_to_cover": distribution(counts),
        "histogram": dict(sorted(histogram.items(), key=lambda item: int(item[0]))),
        "spans_needing_more_than_one_chunk": sum(1 for count in counts if count > 1),
        # The ceiling every retrieval in this arm is scored against: below 1.0
        # only where a span straddles a boundary and loses the whitespace that
        # belongs to neither chunk.
        "mean_max_coverage": round(
            sum(float(row["max_coverage"]) for row in by_query.values()) / len(by_query), 6
        )
        if by_query
        else 0.0,
        "covering_chunk_tokens": distribution(
            [int(row["covering_chunk_tokens"]) for row in by_query.values()]
        ),
    }
    return by_query, summary


def build_report(
    resolved: dict[str, Any], configs_dir: Path, data_root: Path
) -> dict[str, Any]:
    configs_dir = Path(configs_dir)
    queries = read_gold_set(configs_dir / GOLD_SET_FILENAME)
    candidates = list(read_jsonl(configs_dir / "gold_candidates.jsonl"))
    digest = str(resolved["corpus"].get("manifest_sha", ""))

    arms: dict[str, Any] = {}
    per_query_cover: dict[str, dict[str, Any]] = {}
    for level in resolved["factors"]["chunking"]:
        params = arm_params(resolved, level)
        directory = chunk_set_dir(chunk_set_key(digest, params), data_root)
        if not (directory / "chunk_set.json").is_file():
            raise ValueError(f"chunk set for {level!r} not built; run `ragbench chunk` first")
        chunks = load_chunks(directory)
        by_query, summary = _per_arm_cover(queries, chunks)
        arms[level] = {"strategy": params["strategy"], "n_chunks": len(chunks), **summary}
        for query_id, row in by_query.items():
            per_query_cover.setdefault(query_id, {})[level] = row

    return {
        "gold_set_sha": str(resolved["gold"].get("gold_set_sha", "")),
        "manifest_sha": digest,
        "n_questions": len(queries),
        "n_papers": len({query.gold.pmcid for query in queries}),
        "questions": [
            {
                **query.to_dict(),
                "span_chars": len(query.gold),
                "cover": per_query_cover.get(query.query_id, {}),
            }
            for query in queries
        ],
        "span_chars": distribution([len(query.gold) for query in queries]),
        "selection": _selection(candidates),
        "arms": arms,
    }


def _selection(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Where the 40 drafted candidates went, and why."""
    reasons: dict[str, int] = {}
    notes: dict[str, list[str]] = {}
    for record in candidates:
        if record.get("verified"):
            continue
        reason = record.get("hand_reject_reason") or ",".join(record.get("reasons", []))
        reasons[reason] = reasons.get(reason, 0) + 1
        note = record.get("hand_reject_note")
        if note:
            notes.setdefault(reason, []).append(f"{record['query_id']}: {note}")
    auto = [r for r in candidates if r.get("auto_rejected")]
    return {
        "n_candidates": len(candidates),
        "n_accepted": sum(1 for r in candidates if r.get("verified")),
        "n_rejected": sum(1 for r in candidates if not r.get("verified")),
        "n_auto_rejected": len(auto),
        "rejected_by_reason": dict(sorted(reasons.items())),
        "notes": {reason: sorted(lines) for reason, lines in sorted(notes.items())},
        "drafters": sorted({str(r.get("drafted_by", "")) for r in candidates}),
    }
