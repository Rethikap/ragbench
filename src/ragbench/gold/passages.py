"""Candidate passages: the prose paragraphs a question may be drafted from.

Sampling the passage first is what makes the gold span free and honest. The
question is written *from* a known character range, so the label is a record of
where the question came from rather than a judgement about where its answer
might be found -- there is no annotator deciding after the fact which part of the
paper "counts", and so no way for that judgement to favour one chunking arm.

Passages are drawn in **tiers**, not uniformly. A uniform draw over a paper's
paragraphs is a draw over its Methods section, because that is where most of the
paragraphs are, and a question drafted from Methods asks which microscope was
used. Tier order is: on-topic paper and a findings section first, then on-topic
anywhere, then off-topic findings, then the rest. Within a tier the order is
seeded and the sample is reproducible; between tiers it is not random at all,
and is not meant to be.

Selection is seeded and reads only the parsed bodies, so the same config draws
the same passages on any machine.
"""

from __future__ import annotations

import random
import re
from collections.abc import Sequence
from typing import Any, NamedTuple

from ..tokenizers import Tokenizer
from ..types import ParsedPaper
from .relevance import kind_of_span, topic_score

#: Blocks in render_body are separated by a blank line; a section's title is
#: emitted as its own block.
BLOCK_SEPARATOR = "\n\n"
PLACEHOLDER = re.compile(r"\[TABLE:|\[EQUATION\]")
#: A passage has to be prose someone could answer a question from. A block with
#: no sentence-final punctuation is a heading, a list stub or a stray label.
SENTENCE_END = re.compile(r"[.!?][)\"'\]]?\s*$")


class Passage(NamedTuple):
    """One prose paragraph, addressed the way a gold span is."""

    passage_id: str
    pmcid: str
    char_start: int
    char_end: int
    section: str
    text: str
    section_kind: str = "other"
    topic_score: int = 0


def blocks(body: str) -> list[tuple[int, int]]:
    """Offsets of every blank-line-separated block, with surrounding space trimmed."""
    spans: list[tuple[int, int]] = []
    cursor = 0
    for piece in body.split(BLOCK_SEPARATOR):
        start = cursor
        cursor += len(piece) + len(BLOCK_SEPARATOR)
        stripped = piece.strip()
        if not stripped:
            continue
        lead = len(piece) - len(piece.lstrip())
        spans.append((start + lead, start + lead + len(stripped)))
    return spans


def deepest_section(paper: ParsedPaper, start: int, end: int) -> str:
    """Title of the most specific section containing the span.

    Sections nest, so a Methods sub-section is inside Methods; the sub-section is
    what tells a reader where the passage is. Recorded on the gold label because
    the reader of the gold set should be able to place the span without opening
    the paper.
    """
    best = ""
    best_depth = -1
    for section in paper.sections:
        if section.char_start <= start and end <= section.char_end:
            if section.depth > best_depth and section.title:
                best, best_depth = section.title, section.depth
    return best


def _is_heading(paper: ParsedPaper, start: int, end: int) -> bool:
    return any(
        section.char_start == start and section.title == paper.body[start:end]
        for section in paper.sections
    )


def candidates(
    paper: ParsedPaper,
    tokenizer: Tokenizer,
    params: dict[str, Any],
) -> list[Passage]:
    """Every block of this paper eligible to become a gold passage.

    Rejections here are structural -- what a passage *is* -- as opposed to the
    content checks in :mod:`ragbench.gold.validate`, which judge a drafted
    question. Both are recorded; neither is a matter of taste.
    """
    excluded = [pattern.lower() for pattern in params.get("excluded_section_patterns", [])]
    kinds = dict(params.get("section_kinds", {}))
    minimum = int(params["min_passage_tokens"])
    maximum = int(params["max_passage_tokens"])
    score = topic_score(paper, params.get("topic_terms", []))

    found: list[Passage] = []
    for start, end in blocks(paper.body):
        text = paper.body[start:end]
        if _is_heading(paper, start, end):
            continue
        if PLACEHOLDER.search(text):
            # Prose only: a question whose answer sits behind "[TABLE: Table 3]"
            # is unanswerable from the corpus as parsed.
            continue
        if not SENTENCE_END.search(text):
            continue
        section = deepest_section(paper, start, end)
        if any(pattern in section.lower() for pattern in excluded):
            continue
        if not minimum <= tokenizer.count(text) <= maximum:
            continue
        found.append(
            Passage(
                passage_id=f"{paper.pmcid}:{start}-{end}",
                pmcid=paper.pmcid,
                char_start=start,
                char_end=end,
                section=section,
                text=text,
                section_kind=kind_of_span(paper, start, end, kinds),
                topic_score=score,
            )
        )
    return found


def tier_of(passage: Passage, params: dict[str, Any]) -> int:
    """Lower is drawn first. Topic dominates section, because a precise question
    about the wrong subject is still a question about the wrong subject."""
    preferred = set(params.get("preferred_section_kinds", []))
    on_topic = passage.topic_score >= int(params.get("min_topic_terms", 0))
    findings = passage.section_kind in preferred
    return (0 if on_topic else 2) + (0 if findings else 1)


def sample(
    papers: Sequence[ParsedPaper],
    tokenizer: Tokenizer,
    params: dict[str, Any],
    seed: int,
    n_passages: int,
    pinned: Sequence[str] = (),
) -> list[Passage]:
    """Draw ``n_passages``, at most ``max_per_paper`` from any one paper.

    ``pinned`` passage ids are always included and are emitted first. They are
    how a passage already reviewed by hand survives a change to the sampling
    rules: re-sampling from scratch would discard the review, and the review is
    the expensive part. Papers a pinned passage comes from are then excluded
    from the fresh draw, so the one-per-paper rule still holds across both.

    The per-paper cap is not cosmetic. Two questions from one paper share its
    abstract, its vocabulary and its distractors, so they are not independent
    measurements of retrieval; with 100 papers available there is no reason to
    accept that correlation.
    """
    rng = random.Random(seed)
    per_paper = int(params.get("max_per_paper", 1))
    wanted = set(pinned)

    by_paper: dict[str, list[Passage]] = {}
    for paper in papers:
        found = candidates(paper, tokenizer, params)
        if found:
            by_paper[paper.pmcid] = found

    held: list[Passage] = []
    for group in by_paper.values():
        held.extend(passage for passage in group if passage.passage_id in wanted)
    held.sort(key=lambda passage: pinned.index(passage.passage_id))
    missing = wanted - {passage.passage_id for passage in held}
    if missing:
        raise ValueError(
            f"{len(missing)} pinned passages are no longer eligible "
            f"(first: {sorted(missing)[0]}). The sampling parameters moved under a "
            "passage that has already been reviewed; restore them or unpin it."
        )

    spoken_for = {passage.pmcid for passage in held}
    pool: list[list[Passage]] = []
    for pmcid, group in by_paper.items():
        if pmcid in spoken_for:
            continue
        shuffled = list(group)
        rng.shuffle(shuffled)
        pool.append(shuffled[:per_paper])

    rng.shuffle(pool)
    pool.sort(key=lambda group: tier_of(group[0], params))

    drawn: list[Passage] = list(held)
    for group in pool:
        for passage in group:
            if len(drawn) >= n_passages:
                return drawn
            drawn.append(passage)
    return drawn
