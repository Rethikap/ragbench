"""Resolving a minimal evidence span inside the paragraph it came from.

The span is authored as a pair of anchors -- the first and last few words of the
evidence -- rather than as a pair of integers. Offsets typed by hand go stale
the moment anything upstream of them moves, and they go stale silently: a span
that has drifted by forty characters still looks like a valid span. An anchor
that no longer matches is an error at load time, and an anchor that matches
twice is an error too, because a human writing "15 repeats" cannot have meant
both occurrences.

Anchors are also what makes the narrowing auditable. ``configs/gold_drafts.jsonl``
records the words the author picked out; this module turns them into offsets, and
the offsets are derived, never stored by hand.
"""

from __future__ import annotations

from ..types import ParsedPaper


class EvidenceError(Exception):
    """An anchor is missing, ambiguous, or the two are the wrong way round."""


def resolve(
    paper: ParsedPaper,
    context_start: int,
    context_end: int,
    prefix: str,
    suffix: str,
    label: str,
) -> tuple[int, int]:
    """Offsets of the minimal span running from ``prefix`` through ``suffix``.

    Both anchors are matched inside ``[context_start, context_end)`` only, so a
    phrase that also occurs elsewhere in the paper cannot pull the span out of
    the paragraph it belongs to. The returned range is absolute, into
    ``paper.body``, and is always a sub-range of the context.
    """
    if not prefix or not suffix:
        raise EvidenceError(f"{label}: both an evidence prefix and a suffix are required")

    context = paper.body[context_start:context_end]
    found = context.count(prefix)
    if found != 1:
        raise EvidenceError(
            f"{label}: evidence prefix {prefix!r} occurs {found} times in the passage; "
            "it must occur exactly once"
        )
    start = context_start + context.index(prefix)

    tail = paper.body[start:context_end]
    found = tail.count(suffix)
    if found != 1:
        raise EvidenceError(
            f"{label}: evidence suffix {suffix!r} occurs {found} times at or after the "
            "prefix; it must occur exactly once"
        )
    return start, start + tail.index(suffix) + len(suffix)


def sentence_count(text: str) -> int:
    """Sentences in a span, counted the blunt way: terminator followed by space.

    Only ever used to describe a span, never to cut one.
    """
    stripped = text.strip()
    if not stripped:
        return 0
    interior = sum(stripped.count(mark) for mark in (". ", "? ", "! "))
    return interior + 1


def contiguity_note(text: str) -> str:
    """Why a span is wider than one sentence, when it is.

    A question whose answer is stated in two non-adjacent sentences forces the
    minimal *contiguous* span to swallow whatever sits between them. That is not
    a defect in the span; it is a signal about the question, and the author
    should see it while verifying rather than discover it afterwards.
    """
    count = sentence_count(text)
    if count <= 1:
        return ""
    return f"{count} sentences -- the answer is stated in more than one place"
