"""Gold-set report: the questions, why candidates were rejected, and what each
chunking arm would have to retrieve to cover each span.

The third part is the one that matters for the design. A gold span is a fixed
range of characters, but the *units* an arm must win to cover it are not: a span
one arm holds in a single chunk may take two or three in the other. That count is
exactly the denominator Recall@k divides by, which is why this report exists
before any retrieval does -- the granularity asymmetry is a property of the
corpus, the chunkers and the span length, measurable now, not a result to be
discovered later and argued about.

The report reads the working candidate set, not the frozen file, and says so at
the top. An evaluation set is read most often in the state where it is not yet
frozen, because that is the state someone is deciding about it in.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from ..cache_keys import chunk_set_key
from ..chunking.pipeline import arm_params, load_chunks
from ..config import chunk_set_dir
from ..eval.context import context_profile
from ..eval.spans import covering_chunks, minimum_cover, ndcg_at_k, recall_at_k
from ..gold.pipeline import selected_queries
from ..tokenizers import load_tokenizer
from ..types import Chunk, Query
from .chunks import distribution

#: Ranks the gold-bearing chunk is placed at when measuring where in the window
#: the evidence lands. 1 is the oracle; the rest say what a worse ranker costs.
PROBE_RANKS = (1, 2, 3, 5)


def _per_arm_cover(
    queries: list[Query], chunks: list[Chunk]
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    by_query = {query.query_id: minimum_cover(query.gold, chunks) for query in queries}
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


def assemble_window(
    gold: Any,
    chunks: list[Chunk],
    budget: int,
    cost: dict[str, int],
    rng: random.Random,
    gold_rank: int = 1,
) -> list[Chunk]:
    """Build one context the way retrieval will: to a token budget, no truncation.

    Retrieval does not exist yet, so ranking quality is held fixed rather than
    guessed at -- the gold-bearing chunks are placed at ``gold_rank`` and the
    other slots are filled from the same chunk set at random. That isolates what
    this report is for: the *geometry* the arm imposes on the window, which is a
    property of the chunk set and is measurable now. Nothing here predicts what a
    retriever will rank; the numbers are what each arm makes possible.

    Fills greedily and stops at the first chunk that will not fit, matching
    ``fill_policy: stop_at_overflow`` (I1). No chunk is ever truncated.
    """
    needed = covering_chunks(gold, chunks)
    pool = [chunk for chunk in chunks if chunk not in needed]
    window: list[Chunk] = []
    used = 0
    position = 1

    def fits(chunk: Chunk) -> bool:
        return used + cost[chunk.chunk_id] <= budget

    while True:
        if position == gold_rank:
            if not all(fits(chunk) for chunk in needed):
                break
            for chunk in needed:
                window.append(chunk)
                used += cost[chunk.chunk_id]
            position += len(needed)
            continue
        filler = pool[rng.randrange(len(pool))]
        if not fits(filler):
            break
        window.append(filler)
        used += cost[filler.chunk_id]
        position += 1
    return window


def _window_metrics(
    queries: list[Query],
    chunks: list[Chunk],
    budget: int,
    cost: dict[str, int],
    seed: int,
    trials: int,
) -> dict[str, Any]:
    """Per-arm window measurements, averaged over seeded fills of the budget."""
    rng = random.Random(seed)
    token_cost = lambda chunk: cost[chunk.chunk_id]  # noqa: E731

    density: list[float] = []
    distractors: list[int] = []
    n_chunks: list[int] = []
    tokens_used: list[int] = []
    recall: list[float] = []
    ndcg: list[float] = []
    offsets: dict[int, list[int]] = {rank: [] for rank in PROBE_RANKS}

    for query in queries:
        for _ in range(trials):
            window = assemble_window(query.gold, chunks, budget, cost, rng, gold_rank=1)
            profile = context_profile(query.gold, window, token_cost)
            density.append(float(profile["evidence_density"]))
            distractors.append(int(profile["distractor_count"]))
            n_chunks.append(int(profile["n_chunks"]))
            tokens_used.append(int(profile["context_tokens"]))
            recall.append(recall_at_k(query.gold, window, chunks, 10))
            ndcg.append(ndcg_at_k(query.gold, window, chunks, 10))
        for rank in PROBE_RANKS:
            window = assemble_window(query.gold, chunks, budget, cost, rng, gold_rank=rank)
            position = context_profile(query.gold, window, token_cost)
            if position["rank"] is not None:
                offsets[rank].append(int(position["tokens_before"]))

    return {
        "trials_per_query": trials,
        "evidence_density": distribution([round(value * 10000) for value in density]),
        "distractor_count": distribution(distractors),
        "chunks_in_window": distribution(n_chunks),
        "tokens_used": distribution(tokens_used),
        "recall_at_10": round(sum(recall) / len(recall), 4) if recall else 0.0,
        "ndcg_at_10": round(sum(ndcg) / len(ndcg), 4) if ndcg else 0.0,
        "mean_evidence_density": round(sum(density) / len(density), 6) if density else 0.0,
        "mean_distractor_count": round(sum(distractors) / len(distractors), 2)
        if distractors
        else 0.0,
        "tokens_before_gold_at_rank": {
            str(rank): round(sum(values) / len(values), 1) if values else None
            for rank, values in offsets.items()
        },
    }


def build_report(
    resolved: dict[str, Any],
    candidates: list[dict[str, Any]],
    data_root: Path,
    trials: int = 200,
) -> dict[str, Any]:
    queries = selected_queries(candidates)
    if not queries:
        raise ValueError("no candidates are selected; run `ragbench gold build` first")
    digest = str(resolved["corpus"].get("manifest_sha", ""))
    by_id = {record["query_id"]: record for record in candidates}

    retrieval = resolved["base"]["retrieval"]
    budget = int(retrieval["context_token_budget"])
    budget_tokenizer = load_tokenizer(
        retrieval["budget_tokenizer_id"], retrieval["budget_tokenizer_revision"]
    )
    seed = int(resolved["base"]["seed"])

    arms: dict[str, Any] = {}
    per_query_cover: dict[str, dict[str, Any]] = {}
    for level in resolved["factors"]["chunking"]:
        params = arm_params(resolved, level)
        directory = chunk_set_dir(chunk_set_key(digest, params), data_root)
        if not (directory / "chunk_set.json").is_file():
            raise ValueError(f"chunk set for {level!r} not built; run `ragbench chunk` first")
        chunks = load_chunks(directory)
        by_query, summary = _per_arm_cover(queries, chunks)
        cost = {chunk.chunk_id: budget_tokenizer.count(chunk.text) for chunk in chunks}
        arms[level] = {
            "strategy": params["strategy"],
            "n_chunks": len(chunks),
            **summary,
            "window": _window_metrics(queries, chunks, budget, cost, seed, trials),
        }
        for query_id, row in by_query.items():
            per_query_cover.setdefault(query_id, {})[level] = row

    # What the same table looked like when the label was the whole paragraph.
    # Kept so the effect of narrowing is visible rather than asserted.
    context_arms: dict[str, Any] = {}
    context_queries = [_as_context(query) for query in queries]
    for level in arms:
        params = arm_params(resolved, level)
        chunks = load_chunks(chunk_set_dir(chunk_set_key(digest, params), data_root))
        _, summary = _per_arm_cover(context_queries, chunks)
        context_arms[level] = summary

    return {
        "gold_set_sha": str(resolved["gold"].get("gold_set_sha", "")),
        "frozen": str(resolved["gold"].get("gold_set_sha", "")) not in ("", "unfrozen"),
        "manifest_sha": digest,
        "n_questions": len(queries),
        "n_papers": len({query.gold.pmcid for query in queries}),
        "n_verified": sum(1 for query in queries if query.verified),
        "unverified": sorted(query.query_id for query in queries if not query.verified),
        "questions": [
            {
                **query.to_dict(),
                "span_chars": len(query.gold),
                "context_chars": query.gold.context_end - query.gold.context_start,
                "evidence": by_id[query.query_id]["evidence"],
                "context": by_id[query.query_id]["context"],
                "evidence_sentences": by_id[query.query_id]["evidence_sentences"],
                "contiguity_note": by_id[query.query_id]["contiguity_note"],
                "cover": per_query_cover.get(query.query_id, {}),
            }
            for query in queries
        ],
        "span_chars": distribution([len(query.gold) for query in queries]),
        "context_chars": distribution(
            [query.gold.context_end - query.gold.context_start for query in queries]
        ),
        "selection": _selection(candidates),
        "budget": {
            "context_token_budget": budget,
            "budget_tokenizer_id": retrieval["budget_tokenizer_id"],
            "fill_policy": retrieval["fill_policy"],
        },
        "arms": arms,
        "arms_if_labelled_by_paragraph": context_arms,
    }


def _as_context(query: Query) -> Query:
    """The same question labelled by its paragraph, for the before/after table."""
    from ..types import GoldSpan

    gold = query.gold
    return Query(
        query_id=query.query_id,
        question=query.question,
        reference_answer=query.reference_answer,
        gold=GoldSpan(
            pmcid=gold.pmcid,
            char_start=gold.context_start,
            char_end=gold.context_end,
            section=gold.section,
            context_start=gold.context_start,
            context_end=gold.context_end,
        ),
        verified=query.verified,
    )


def _selection(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Where the drafted candidates went, and why."""
    reasons: dict[str, int] = {}
    notes: dict[str, list[str]] = {}
    for record in candidates:
        if record.get("selected"):
            continue
        reason = record.get("rejection_reason") or ",".join(record.get("reasons", []))
        reasons[reason] = reasons.get(reason, 0) + 1
        if record.get("note"):
            notes.setdefault(reason, []).append(f"{record['query_id']}: {record['note']}")
    return {
        "n_candidates": len(candidates),
        "n_selected": sum(1 for r in candidates if r.get("selected")),
        "n_rejected": sum(1 for r in candidates if not r.get("selected")),
        "n_auto_rejected": sum(1 for r in candidates if r.get("auto_rejected")),
        "rejected_by_reason": dict(sorted(reasons.items())),
        "notes": {reason: sorted(lines) for reason, lines in sorted(notes.items())},
        "drafters": sorted({str(r.get("drafted_by", "")) for r in candidates}),
    }


def verification_sheet(report: dict[str, Any]) -> str:
    """The 20 questions in the form someone can actually check them in.

    Question, reference answer, the exact span text, the paragraph it sits in,
    pmcid and section -- everything needed to say yes or no without opening the
    paper, and nothing else.
    """
    lines: list[str] = []
    add = lines.append
    add(f"# Gold set verification sheet — {report['n_questions']} questions")
    add("")
    add(f"corpus manifest_sha : {report['manifest_sha']}")
    add(f"gold_set_sha        : {report['gold_set_sha']}")
    add(f"verified            : {report['n_verified']}/{report['n_questions']}")
    add(f"drafted by          : {'; '.join(report['selection']['drafters'])}")
    add("")
    add("For each: does the question have exactly one answer, is that answer the")
    add("reference answer, and is it stated inside SPAN (not merely in CONTEXT)?")
    add('Set "verified": true on that record in configs/gold_drafts.jsonl.')
    add("")

    for question in report["questions"]:
        gold = question["gold"]
        add("-" * 78)
        state = "VERIFIED" if question["verified"] else "UNVERIFIED"
        add(f"## {question['query_id']}   {gold['pmcid']}   [{state}]")
        add(f"section : {gold['section'] or '(untitled)'}")
        add(
            f"span    : chars {gold['char_start']}-{gold['char_end']}"
            f" ({question['span_chars']} chars, {question['evidence_sentences']} sentence(s))"
            f"   context {gold['context_start']}-{gold['context_end']}"
            f" ({question['context_chars']} chars)"
        )
        covers = "  ".join(
            f"{level}: {row['n_chunks_to_cover']}" for level, row in question["cover"].items()
        )
        add(f"chunks  : {covers}")
        if question["contiguity_note"]:
            add(f"NOTE    : {question['contiguity_note']}")
        add("")
        add(f"Q       : {question['question']}")
        add(f"A       : {question['reference_answer']}")
        add("")
        add("SPAN    | " + question["evidence"])
        add("")
        add("CONTEXT | " + question["context"])
        add("")
    return "\n".join(lines)
