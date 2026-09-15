"""Chunk-length report: does the chunking factor actually vary anything?

The question this answers is whether the two arms produce materially different
length distributions on this corpus. If recursive were falling back to character
splitting on most paragraphs it would behave almost exactly like fixed, and the
chunking factor would have nothing to measure.

Nothing here tunes anything. Every number comes from the configured parameters.
"""

from __future__ import annotations

import random
import re
from pathlib import Path
from typing import Any

import numpy as np

from ..cache_keys import chunk_set_key
from ..chunking.pipeline import arm_params, load_chunks, load_meta
from ..config import chunk_set_dir
from ..tokenizers import load_tokenizer
from ..types import Chunk

#: A chunk is treated as cut mid-sentence unless it ends on sentence-final
#: punctuation, optionally followed by a closing quote or bracket, or ends on a
#: placeholder such as "[TABLE: Table 2]".
SENTENCE_END = re.compile(r"""[.!?][)"'\]]?$|\]$""")
PLACEHOLDER = re.compile(r"\[TABLE:|\[EQUATION\]")

PERCENTILES = (10, 25, 50, 75, 90)

#: Canonical-token thresholds for the tiny-chunk census. `min_chunk_tokens: 0`
#: keeps short tail chunks instead of merging them into a neighbour. Merging
#: would make a chunk's boundaries depend on the size of the chunk before it --
#: a second, undeclared chunking rule that neither factor level asked for, and
#: one that would bite the two arms unequally. The honest alternative is to keep
#: them and say how many there are, which is what this counts.
TINY_THRESHOLDS = (10, 25, 50, 100)


def distribution(values: list[int]) -> dict[str, float]:
    if not values:
        return {"n": 0}
    array = np.array(values, dtype=float)
    result: dict[str, float] = {
        "n": len(values),
        "mean": round(float(array.mean()), 1),
        "min": int(array.min()),
        "max": int(array.max()),
        "std": round(float(array.std(ddof=0)), 1),
    }
    for percentile in PERCENTILES:
        key = "median" if percentile == 50 else f"p{percentile}"
        result[key] = round(float(np.percentile(array, percentile)), 1)
    return result


def budget_fill(costs: list[int], budget: int, seed: int, trials: int) -> dict[str, Any]:
    """How many chunks fit in the budget, sampling chunks uniformly at random.

    Retrieval ranking does not exist yet, so the neutral assumption is that a
    query pulls an arbitrary set of chunks. Filling is greedy and stops at the
    first chunk that will not fit, matching ``fill_policy: stop_at_overflow`` --
    no chunk is ever truncated to make it fit.
    """
    rng = random.Random(seed)
    counts: list[int] = []
    used: list[int] = []
    oversized = sum(1 for cost in costs if cost > budget)
    for _ in range(trials):
        total = 0
        taken = 0
        while True:
            cost = costs[rng.randrange(len(costs))]
            if total + cost > budget:
                break
            total += cost
            taken += 1
        counts.append(taken)
        used.append(total)
    histogram: dict[str, int] = {}
    for count in counts:
        histogram[str(count)] = histogram.get(str(count), 0) + 1
    return {
        "chunks_per_budget": distribution(counts),
        "tokens_used": distribution(used),
        "histogram": dict(sorted(histogram.items(), key=lambda item: int(item[0]))),
        "chunks_larger_than_budget": oversized,
        "trials": trials,
    }


def tiny_census(chunks: list[Chunk], last_index: dict[str, int]) -> dict[str, Any]:
    """How many chunks are short, and how many of those are a paper's last chunk.

    The split matters: a short *final* chunk is the arithmetic remainder of a
    body that did not divide evenly and is expected in both arms. A short
    *mid-body* chunk is the chunker leaving a stub behind, which only the
    recursive arm can do -- a paragraph shorter than the target that could not be
    packed with its neighbour.
    """
    rows: dict[str, Any] = {}
    for threshold in TINY_THRESHOLDS:
        small = [chunk for chunk in chunks if chunk.n_tokens < threshold]
        final = sum(1 for chunk in small if chunk.chunk_index == last_index[chunk.pmcid])
        rows[f"under_{threshold}"] = {
            "n": len(small),
            "share": round(len(small) / len(chunks), 4) if chunks else 0.0,
            "final_chunk_of_paper": final,
            "mid_body": len(small) - final,
        }
    return rows


def _arm_report(
    level: str,
    directory: Path,
    chunks: list[Chunk],
    meta: dict[str, Any],
    budget_costs: list[int],
    budget: int,
    seed: int,
    trials: int,
) -> dict[str, Any]:
    lengths = [chunk.n_tokens for chunk in chunks]
    per_paper: dict[str, int] = {}
    for chunk in chunks:
        per_paper[chunk.pmcid] = per_paper.get(chunk.pmcid, 0) + 1

    with_placeholder = [c for c in chunks if PLACEHOLDER.search(c.text)]
    prose = [c for c in chunks if not PLACEHOLDER.search(c.text)]

    last_index = {}
    for chunk in chunks:
        last_index[chunk.pmcid] = max(last_index.get(chunk.pmcid, 0), chunk.chunk_index)
    truncated = [c for c in chunks if not SENTENCE_END.search(c.text.rstrip())]
    truncated_midbody = [c for c in truncated if c.chunk_index != last_index[c.pmcid]]

    return {
        "level": level,
        "strategy": meta["strategy"],
        "chunk_set_id": meta["chunk_set_id"],
        "directory": str(directory),
        "n_chunks": len(chunks),
        "n_papers": len(per_paper),
        "canonical_tokens": distribution(lengths),
        "chunks_per_paper": distribution(list(per_paper.values())),
        "chars": distribution([len(c.text) for c in chunks]),
        "budget_tokens": distribution(budget_costs),
        "separator_levels": meta.get("separator_levels", {}),
        "over_target": sum(1 for c in chunks if c.n_tokens > meta["params"]["target_tokens"]),
        "tiny": tiny_census(chunks, last_index),
        "budget_fill": budget_fill(budget_costs, budget, seed, trials),
        "mid_sentence": {
            "n": len(truncated),
            "share": round(len(truncated) / len(chunks), 4) if chunks else 0.0,
            "excluding_final_chunk_of_paper": len(truncated_midbody),
        },
        "placeholders": {
            "n_chunks_with_placeholder": len(with_placeholder),
            "share": round(len(with_placeholder) / len(chunks), 4) if chunks else 0.0,
            "placeholder_tokens": distribution([c.n_tokens for c in with_placeholder]),
            "prose_tokens": distribution([c.n_tokens for c in prose]),
        },
    }


def build_report(
    resolved: dict[str, Any], data_root: Path, trials: int = 20000
) -> dict[str, Any]:
    corpus = resolved["corpus"]
    digest = str(corpus.get("manifest_sha", ""))
    retrieval = resolved["base"]["retrieval"]
    budget = int(retrieval["context_token_budget"])
    budget_tokenizer = load_tokenizer(
        retrieval["budget_tokenizer_id"], retrieval["budget_tokenizer_revision"]
    )
    seed = int(resolved["base"]["seed"])

    arms: list[dict[str, Any]] = []
    for level in resolved["factors"]["chunking"]:
        params = arm_params(resolved, level)
        directory = chunk_set_dir(chunk_set_key(digest, params), data_root)
        if not (directory / "chunk_set.json").is_file():
            raise ValueError(f"chunk set for {level!r} not built; run `ragbench chunk` first")
        chunks = load_chunks(directory)
        meta = load_meta(directory)
        costs = [budget_tokenizer.count(chunk.text) for chunk in chunks]
        arms.append(
            _arm_report(level, directory, chunks, meta, costs, budget, seed, trials)
        )

    return {
        "manifest_sha": digest,
        "budget": {
            "context_token_budget": budget,
            "budget_tokenizer_id": retrieval["budget_tokenizer_id"],
            "chunk_tokenizer_id": resolved["base"]["chunking"]["tokenizer_id"],
            "target_tokens": int(resolved["base"]["chunking"]["target_tokens"]),
            "min_chunk_tokens": int(resolved["base"]["chunking"]["min_chunk_tokens"]),
            "fill_policy": retrieval["fill_policy"],
        },
        "arms": arms,
        "comparison": _compare(arms),
    }


def _compare(arms: list[dict[str, Any]]) -> dict[str, Any]:
    """Blunt summary of whether the arms differ, for the reader in a hurry."""
    if len(arms) != 2:
        return {}
    first, second = arms
    medians = (first["canonical_tokens"]["median"], second["canonical_tokens"]["median"])
    fills = (
        first["budget_fill"]["chunks_per_budget"]["mean"],
        second["budget_fill"]["chunks_per_budget"]["mean"],
    )
    spread = (first["canonical_tokens"]["std"], second["canonical_tokens"]["std"])
    return {
        "levels": [first["level"], second["level"]],
        "median_tokens": list(medians),
        "median_ratio": round(max(medians) / min(medians), 2) if min(medians) else None,
        "std_tokens": list(spread),
        "mean_chunks_per_budget": list(fills),
        "chunk_count": [first["n_chunks"], second["n_chunks"]],
    }
