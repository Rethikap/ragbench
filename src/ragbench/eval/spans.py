"""Span coverage, and the two rank metrics kept beside it for comparability.

The primary retrieval metric here is **span coverage**: of the characters in a
gold span, what fraction did the retrieved context actually contain? It is
computed from character offsets, so it does not know or care how either arm drew
its chunk boundaries.

That neutrality is the point. Recall@k asks "how many of the relevant *chunks*
were retrieved", and the relevant chunks are whatever the arm's own boundaries
happen to produce. An arm that needs three chunks to hold a span scores 0.67 for
retrieving two of them -- for work that put two thirds of the answer in front of
the generator -- while an arm that holds the same span in one chunk scores 1.0,
inside a chunk that may be mostly about something else. The denominator is the
arm's own granularity, so the two arms are not being asked the same question.

Which arm the bias favours is not fixed; it follows whichever arm's boundaries
happen to align with the unit the gold spans were drawn from. On this corpus the
spans are prose paragraphs, and the recursive arm splits on paragraphs, so it
covers all 20 spans in one chunk while the fixed arm needs two for 6 of them --
here Recall@k flatters the *finer* arm. Sample the spans differently and the
direction would change, which is the argument against relying on it. Span
coverage asks the question retrieval is actually for: can the generator see the
answer?

Recall@k and nDCG@10 are still computed and reported, because they are what the
literature reports and dropping them would make this work harder to situate.
They are secondary, and the asymmetry above is why.

Gold labels are character spans, never chunk ids (invariant I5). The per-arm
relevant chunk set is *derived* here, at eval time, from whichever chunk set is
loaded -- it is never stored.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from ..types import Chunk, GoldSpan

Interval = tuple[int, int]


def _merge(intervals: Iterable[Interval]) -> list[Interval]:
    """Union of possibly-overlapping intervals, in ascending order.

    Chunks do not overlap while ``overlap_tokens`` is 0, but the metric must not
    depend on that: with overlap configured, counting a doubly-covered character
    twice would let an arm score above 1.0 by retrieving the same text twice.
    """
    merged: list[Interval] = []
    for start, end in sorted(intervals):
        if end <= start:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _overlap(first: Interval, second: Interval) -> int:
    return max(0, min(first[1], second[1]) - max(first[0], second[0]))


def covering_chunks(gold: GoldSpan, chunks: Sequence[Chunk]) -> list[Chunk]:
    """The chunks of one arm that overlap the gold span: that arm's relevant set.

    Derived, not stored. Membership is *any* overlap rather than containment,
    because a chunk holding one sentence of a three-sentence answer is genuinely
    relevant -- it is simply not sufficient, which is what coverage measures and
    a binary relevant/not-relevant label cannot.
    """
    target = (gold.char_start, gold.char_end)
    return [
        chunk
        for chunk in chunks
        if chunk.pmcid == gold.pmcid and _overlap((chunk.char_start, chunk.char_end), target)
    ]


def span_coverage(gold: GoldSpan, retrieved: Sequence[Chunk]) -> float:
    """Fraction of the gold span's characters present in the retrieved context.

    THE primary retrieval metric. Chunks from other papers contribute nothing,
    however high they ranked.

    Returns 0.0 for an empty retrieval. A zero-length gold span is a malformed
    label rather than a degenerate score, so it raises.
    """
    width = gold.char_end - gold.char_start
    if width <= 0:
        raise ValueError(
            f"gold span for {gold.pmcid} is empty ({gold.char_start}..{gold.char_end}); "
            "a label with no characters cannot be covered"
        )
    target = (gold.char_start, gold.char_end)
    covered = sum(
        _overlap(interval, target)
        for interval in _merge(
            (chunk.char_start, chunk.char_end)
            for chunk in retrieved
            if chunk.pmcid == gold.pmcid
        )
    )
    return covered / width


def minimum_cover(gold: GoldSpan, chunks: Sequence[Chunk]) -> dict[str, float | int]:
    """What this arm would need to cover the span, and the best it could do.

    Chunks tile the body in order, so every chunk that overlaps the span is
    needed to cover it and no other chunk helps: the overlapping set *is* the
    minimum cover, and its size is the number of slots the arm must win.

    ``max_coverage`` is what that whole set achieves. It is normally 1.0 and
    slightly below it when a span straddles a chunk boundary, because the
    whitespace between two chunks belongs to neither -- worth reporting rather
    than rounding away, since it is the ceiling every retrieval is scored
    against.
    """
    needed = covering_chunks(gold, chunks)
    return {
        "n_chunks_to_cover": len(needed),
        "max_coverage": round(span_coverage(gold, needed), 6),
        "covering_chunk_tokens": sum(chunk.n_tokens for chunk in needed),
    }


def recall_at_k(gold: GoldSpan, ranked: Sequence[Chunk], chunks: Sequence[Chunk], k: int) -> float:
    """Share of the arm's relevant chunks that appear in the top ``k``.

    Secondary. See the module docstring for why: the denominator is the arm's own
    chunk count for the span, so a finer arm is scored against a larger target.
    """
    relevant = {chunk.chunk_id for chunk in covering_chunks(gold, chunks)}
    if not relevant:
        return 0.0
    found = sum(1 for chunk in ranked[:k] if chunk.chunk_id in relevant)
    return found / len(relevant)


def ndcg_at_k(gold: GoldSpan, ranked: Sequence[Chunk], chunks: Sequence[Chunk], k: int) -> float:
    """Binary-relevance nDCG over the derived relevant set. Secondary.

    Binary rather than graded: grading by how much of the span a chunk holds
    would make the gain depend on chunk size, reintroducing exactly the
    granularity bias that span coverage exists to avoid.
    """
    relevant = {chunk.chunk_id for chunk in covering_chunks(gold, chunks)}
    if not relevant:
        return 0.0
    gains = [1.0 if chunk.chunk_id in relevant else 0.0 for chunk in ranked[:k]]
    actual = sum(gain / math.log2(rank + 1) for rank, gain in enumerate(gains, start=1))
    ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(len(relevant), k) + 1))
    return actual / ideal if ideal else 0.0
