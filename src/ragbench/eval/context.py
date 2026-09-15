"""What else is in the window besides the evidence.

:mod:`ragbench.eval.spans` asks whether the generator can see the answer. Once
both arms answer yes, it has stopped measuring -- and on the current gold set
both arms cover every span in a single chunk, so coverage, Recall@k and nDCG@10
all saturate at 1.0. That is not a finding that chunking has no retrieval
effect. It is the metric running out of room: the arms retrieve the *same span*
inside *different context*, and coverage is blind to the difference by design.

These three measure the difference:

``evidence_density``
    Gold-span characters as a share of everything in the window. Precision at
    the budget level. A 200-character answer inside a 512-token chunk is a
    different prompt from the same answer inside a 180-token chunk, and this is
    the number that says so.
``gold_chunk_rank``
    Where the evidence sits in the assembled context, by rank and by token
    offset from the start of the window. Position drives attention, so an answer
    at token 1600 of 2000 is not in the same place as one at token 40 -- and the
    offset for a given rank is a function of how big the arm's chunks are.
``distractor_count``
    How many chunks in the window do not touch the gold span at all. The budget
    is constant (I1), so a finer arm fits more chunks in it; whether that is
    more context or more noise is exactly what RQ1 is asking.

All three take the context *in the order it will be assembled into the prompt*,
because two of them are meaningless without it. None reads the gold span's
context paragraph -- relevance is the minimal span only (I5).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from ..types import Chunk, GoldSpan
from .spans import covering_chunks, span_coverage

TokenCost = Callable[[Chunk], int]


def _canonical_tokens(chunk: Chunk) -> int:
    """Default cost: the chunk's own canonical token count.

    Retrieval measures the budget in *generator* tokens (I1) and records them on
    each ScoredChunk; pass that as ``token_cost`` once those records exist. The
    default keeps the metric computable from a chunk set alone.
    """
    return chunk.n_tokens


def evidence_density(gold: GoldSpan, retrieved: Sequence[Chunk]) -> float:
    """Share of the retrieved context that is gold-span text.

    The complement of "how much of the window is something else". Measured in
    characters rather than tokens so that it is comparable with
    :func:`~.spans.span_coverage`, which is also a character fraction -- density
    is the precision to coverage's recall, and the two should be readable side by
    side without a unit conversion in the reader's head.

    Returns 0.0 for an empty context: nothing retrieved is nothing relevant.
    """
    total = sum(len(chunk.text) for chunk in retrieved)
    if total <= 0:
        return 0.0
    covered = span_coverage(gold, retrieved) * len(gold)
    return covered / total


def gold_chunk_rank(
    gold: GoldSpan, retrieved: Sequence[Chunk], token_cost: TokenCost | None = None
) -> dict[str, int | None]:
    """Where the evidence sits in the assembled window.

    ``rank`` is 1-based over the context as ordered for the prompt, and is
    ``None`` when no retrieved chunk touches the span -- absent is not rank 0,
    and reporting it as 0 would make it sort ahead of a first-place hit.

    ``tokens_before`` and ``chars_before`` are the offsets of that chunk from the
    start of the window, which is the quantity position effects actually act on:
    rank 3 of five 180-token chunks and rank 3 of five 512-token chunks put the
    evidence in very different places.
    """
    cost = token_cost or _canonical_tokens
    relevant = {chunk.chunk_id for chunk in covering_chunks(gold, retrieved)}

    tokens = 0
    chars = 0
    for position, chunk in enumerate(retrieved, start=1):
        if chunk.chunk_id in relevant:
            return {
                "rank": position,
                "tokens_before": tokens,
                "chars_before": chars,
                "n_gold_chunks": len(relevant),
            }
        tokens += cost(chunk)
        chars += len(chunk.text)
    return {"rank": None, "tokens_before": None, "chars_before": None, "n_gold_chunks": 0}


def distractor_count(gold: GoldSpan, retrieved: Sequence[Chunk]) -> int:
    """Chunks in the window that do not overlap the gold span.

    Includes chunks from the right paper that miss the span, which are the
    interesting distractors: same vocabulary, same authors, wrong sentences.
    """
    relevant = {chunk.chunk_id for chunk in covering_chunks(gold, retrieved)}
    return sum(1 for chunk in retrieved if chunk.chunk_id not in relevant)


def context_profile(
    gold: GoldSpan, retrieved: Sequence[Chunk], token_cost: TokenCost | None = None
) -> dict[str, float | int | None]:
    """Every window measurement for one query, in one pass."""
    cost = token_cost or _canonical_tokens
    position = gold_chunk_rank(gold, retrieved, cost)
    return {
        "n_chunks": len(retrieved),
        "context_tokens": sum(cost(chunk) for chunk in retrieved),
        "context_chars": sum(len(chunk.text) for chunk in retrieved),
        "span_coverage": round(span_coverage(gold, retrieved), 6),
        "evidence_density": round(evidence_density(gold, retrieved), 6),
        "distractor_count": distractor_count(gold, retrieved),
        **position,
    }
