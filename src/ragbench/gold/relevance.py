"""Which passages are worth asking a question about.

Two orthogonal judgements, both made from the parsed paper alone and both
configured rather than hardcoded:

**Which part of the paper.** A passage's section kind -- results, discussion,
methods, introduction -- decides whether it is likely to carry a finding or the
provenance of a method. Results and Discussion are sampled first; Methods
passages are eligible but come last, because a Methods passage only earns a
question when its answer is a design choice that changes how a result is read
(which covariates a model adjusted for, what threshold defined a positive case),
not the identity of a reagent or an instrument.

**Which paper.** The frozen corpus query was looser than intended: it selected on
"alzheimer AND biomarker" as free text, which admits papers whose subject is a
glioma cell line, a rat sciatic nerve, or Drosophila, and which merely mention
Alzheimer's. The corpus is frozen and is not re-queried (I4), so the drift is
handled where it can be handled honestly -- by sampling gold passages from
on-topic papers first, and by recording the drift as a limitation rather than
papering over it.

Neither judgement discards anything. They order the pool; the sampler takes from
the front.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ..types import ParsedPaper, SectionSpan

OTHER = "other"


def section_kind(title: str, sec_type: str, patterns: dict[str, Sequence[str]]) -> str:
    """Classify a section, preferring JATS's own ``sec-type`` over its title.

    ``sec-type`` is the publisher's declaration and is right when it is present;
    it is absent often enough -- especially in numbered headings like
    "2.4. Statistical Analysis" -- that a title fallback is not optional.
    """
    declared = (sec_type or "").strip().lower()
    for kind, needles in patterns.items():
        if any(declared == needle or declared.startswith(needle) for needle in needles):
            return kind
    lowered = (title or "").strip().lower()
    for kind, needles in patterns.items():
        if any(needle in lowered for needle in needles):
            return kind
    return OTHER


def kind_of_span(paper: ParsedPaper, start: int, end: int, patterns: dict[str, Any]) -> str:
    """Kind of the most specific *classifiable* section containing the span.

    Deepest-first, but a sub-section titled "Cresyl Violet Staining" classifies as
    ``other`` while its parent is Methods -- so an unclassifiable child defers to
    its parent instead of hiding it.
    """
    containing: list[SectionSpan] = [
        section
        for section in paper.sections
        if section.char_start <= start and end <= section.char_end
    ]
    for section in sorted(containing, key=lambda s: s.depth, reverse=True):
        kind = section_kind(section.title, section.sec_type, patterns)
        if kind != OTHER:
            return kind
    return OTHER


def topic_score(paper: ParsedPaper, terms: Sequence[str]) -> int:
    """How many distinct topic terms appear in the title and abstract.

    Title and abstract rather than the body: a paper about something else that
    cites the Alzheimer's literature will use the vocabulary in its introduction
    and discussion, which is exactly the false positive to avoid. What a paper is
    *about* is what it says it is about in front.
    """
    haystack = f"{paper.title}\n{paper.abstract}".lower()
    return sum(1 for term in terms if term.lower() in haystack)


def corpus_drift(papers: Sequence[ParsedPaper], params: dict[str, Any]) -> dict[str, Any]:
    """How much of the frozen corpus is off-topic, as a reportable number.

    A limitation is only a limitation if it is quantified; this is the figure the
    write-up should carry, not an impression.
    """
    terms = list(params.get("topic_terms", []))
    minimum = int(params.get("min_topic_terms", 0))
    scores = {paper.pmcid: topic_score(paper, terms) for paper in papers}
    off_topic = sorted(pmcid for pmcid, score in scores.items() if score < minimum)
    return {
        "n_papers": len(papers),
        "min_topic_terms": minimum,
        "n_on_topic": len(papers) - len(off_topic),
        "n_off_topic": len(off_topic),
        "off_topic_share": round(len(off_topic) / len(papers), 4) if papers else 0.0,
        "off_topic_pmcids": off_topic,
        "score_histogram": {
            str(score): sum(1 for value in scores.values() if value == score)
            for score in sorted(set(scores.values()))
        },
    }
