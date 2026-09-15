"""Candidate passages: the prose paragraphs a question may be drafted from.

Sampling the passage first is what makes the gold span free and honest. The
question is written *from* a known character range, so the label is a record of
where the question came from rather than a judgement about where its answer
might be found -- there is no annotator deciding after the fact which part of the
paper "counts", and so no way for that judgement to favour one chunking arm.

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
    minimum = int(params["min_passage_tokens"])
    maximum = int(params["max_passage_tokens"])

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
            )
        )
    return found


def sample(
    papers: Sequence[ParsedPaper],
    tokenizer: Tokenizer,
    params: dict[str, Any],
    seed: int,
    n_passages: int,
) -> list[Passage]:
    """Draw ``n_passages`` passages, at most ``max_per_paper`` from any one paper.

    The per-paper cap is not cosmetic. Two questions from one paper share its
    abstract, its vocabulary and its distractors, so they are not independent
    measurements of retrieval; with 100 papers available there is no reason to
    accept that correlation.

    Papers are shuffled rather than walked in manifest order, so the sample is
    not the corpus's PMCID prefix; the seed comes from base.yaml.
    """
    rng = random.Random(seed)
    per_paper = int(params.get("max_per_paper", 1))

    pool: list[list[Passage]] = []
    for paper in papers:
        found = candidates(paper, tokenizer, params)
        if found:
            rng.shuffle(found)
            pool.append(found[:per_paper])

    rng.shuffle(pool)
    drawn: list[Passage] = []
    for group in pool:
        for passage in group:
            drawn.append(passage)
            if len(drawn) == n_passages:
                return drawn
    return drawn
