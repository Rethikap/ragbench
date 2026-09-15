"""The four rejection checks, made mechanical wherever they can be.

A hand-verified gold set is only as trustworthy as the reasons it was filtered
by. "I read it and it seemed fine" is not a reason another person can audit, so
each ground for rejection gets a computed signal, a configured threshold, and its
numbers recorded on the candidate:

1. **Answerable without the span.** A question the generator can answer from what
   it already knows measures the generator's memory, not retrieval.
2. **Methods provenance, not a finding.** The answer identifies a reagent, an
   instrument, a software version or a housing condition. That is a string
   lookup dressed as scientific QA, and it is answerable by near-verbatim
   matching, so every configuration scores alike and the set stops
   discriminating between arms.
3. **Answer needs a placeholder.** ``[TABLE: Table 3]`` and ``[EQUATION]`` stand
   in for content the parse policy dropped; a question answered by one is
   unanswerable from the corpus as it exists.
4. **Answer is also in the abstract.** Abstracts are not chunked, but an answer
   restated there means the span is a near-duplicate of text elsewhere in the
   paper, which is the labelling ambiguity abstracts were excluded to avoid.

These auto-reject. Everything that survives is still read by a person: the checks
are a floor, not the verification.

Note what check 1 no longer is. It used to require the answer to contain a token
rare across the corpus, on the theory that a rare token means a passage-specific
answer. It does -- and the rarest tokens in a paper are catalogue numbers,
instrument model numbers and software versions, so the check quietly selected
*for* Methods provenance and steered nine of the first twenty questions into the
wrong part of the paper. The goal was right and the proxy was backwards. The test
is now direct: could this answer be produced without reading this span?
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from typing import Any

#: Deliberately small and closed. A long stoplist would start deciding which
#: domain words count as content, which is a judgement these checks must not make.
STOPWORDS = frozenset(
    """
    a an the and or but if then than that this these those of in on at to for from by with
    without into over under between among during before after above below is are was were be
    been being has have had do does did not no nor so such as it its their there here which
    who whom whose what when where why how all any both each few more most other some only own
    same too very can will just should now we our us they them he she his her you your i
    """.split()
)

WORD = re.compile(r"[A-Za-z][A-Za-z0-9\-']*|\d+(?:\.\d+)?")
PLACEHOLDER = re.compile(r"\[TABLE:|\[EQUATION\]")
#: A question or answer that talks about an artefact the parse policy removed.
ARTEFACT_REFERENCE = re.compile(
    r"\b(table|tables|figure|figures|fig\.?|equation|equations|supplementary|"
    r"supplemental|panel)\b",
    re.IGNORECASE,
)
#: "version 0.90", "v1.0.0", "3.7.3" -- a software version, never a measurement.
#: Deliberately not a bare `\d+\.\d+`, which would match every p-value.
VERSION = re.compile(r"\bversion\s+[\w.]+|\bv\d+(\.\d+)+\b|\b\d+\.\d+\.\d+\b", re.IGNORECASE)


def content_tokens(text: str) -> list[str]:
    """Lowercased word and number tokens, stopwords removed, order preserved."""
    return [
        token
        for token in (match.group(0).lower() for match in WORD.finditer(text))
        if token not in STOPWORDS
    ]


def corpus_tokens(papers: Iterable[tuple[str, str]]) -> dict[str, set[str]]:
    """``{pmcid: set of content tokens}`` for the whole corpus.

    The corpus stands in for "what could be known without this span". It is the
    right reference precisely because it is the same literature: a fact every
    Alzheimer's paper states is not a fact this passage taught anyone.
    """
    return {pmcid: set(content_tokens(body)) for pmcid, body in papers}


def document_frequency(token_sets: dict[str, set[str]]) -> dict[str, int]:
    """How many papers each content token appears in. Used only by the stand-in
    drafter, which needs *some* ordering to pick a token to mask."""
    frequency: dict[str, int] = {}
    for tokens in token_sets.values():
        for token in tokens:
            frequency[token] = frequency.get(token, 0) + 1
    return frequency


def _share(tokens: Sequence[str], haystack: set[str]) -> float:
    if not tokens:
        return 0.0
    return sum(1 for token in tokens if token in haystack) / len(tokens)


def longest_shared_ngram(first: Sequence[str], second: Sequence[str]) -> int:
    """Length of the longest token sequence the two texts share.

    A near-duplicate is not a matter of vocabulary overlap -- two paragraphs of
    the same paper always overlap -- but of repeated phrasing, which is what a
    long shared n-gram detects and a bag-of-words score cannot.
    """
    if not first or not second:
        return 0
    previous = [0] * (len(second) + 1)
    best = 0
    for left in first:
        current = [0] * (len(second) + 1)
        for index, right in enumerate(second, start=1):
            if left == right:
                current[index] = previous[index - 1] + 1
                best = max(best, current[index])
        previous = current
    return best


def elsewhere_in_corpus(
    answer_tokens: Sequence[str],
    source_pmcid: str,
    token_sets: dict[str, set[str]],
    coverage: float,
) -> int:
    """How many *other* papers already contain this answer's content.

    The answer is scored as a conjunction, not as a bag of rarities: a paper
    counts only if it holds at least ``coverage`` of the answer's content terms.
    That is what makes this a test of the answer rather than of its vocabulary --
    an answer made entirely of ordinary words passes if their *combination* is
    not already sitting in the rest of the literature, and an answer containing
    one exotic catalogue number gets no credit for it.
    """
    if not answer_tokens:
        return 0
    needed = max(1, int(round(coverage * len(answer_tokens))))
    return sum(
        1
        for pmcid, tokens in token_sets.items()
        if pmcid != source_pmcid
        and sum(1 for token in answer_tokens if token in tokens) >= needed
    )


def provenance_markers(text: str, markers: dict[str, Sequence[str]]) -> list[str]:
    """Marks of an answer that identifies apparatus rather than a result.

    Vendors, artefact nouns ("kit", "microscope", "package"), equipment units and
    version strings. Deliberately tight: "database", "samples" and bare "ml" are
    not here, because they occur in answers that are findings.
    """
    lowered = f" {text.lower()} "
    found = [
        f"{kind}:{needle}"
        for kind, needles in markers.items()
        for needle in needles
        if needle.lower() in lowered
    ]
    if VERSION.search(text):
        found.append("version-string")
    return sorted(set(found))


def result_language(text: str, markers: Sequence[str]) -> list[str]:
    """Marks of an answer that states a result: comparison, relationship, effect."""
    lowered = text.lower()
    return sorted({marker for marker in markers if marker.lower() in lowered})


def check(
    question: str,
    answer: str,
    span: str,
    abstract: str,
    source_pmcid: str,
    token_sets: dict[str, set[str]],
    section_kind: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Run every check. Returns the flags, the numbers behind them, and a verdict."""
    answer_tokens = content_tokens(answer)
    span_tokens = content_tokens(span)
    abstract_tokens = content_tokens(abstract)
    question_tokens = set(content_tokens(question))
    span_set = set(span_tokens)

    grounding = _share(answer_tokens, span_set)
    leakage = _share(answer_tokens, question_tokens)
    elsewhere = elsewhere_in_corpus(
        answer_tokens, source_pmcid, token_sets, float(params["corpus_coverage"])
    )
    abstract_overlap = _share(answer_tokens, set(abstract_tokens))
    shared_ngram = longest_shared_ngram(span_tokens, abstract_tokens)
    markers = provenance_markers(answer, dict(params.get("provenance_markers", {})))
    results = result_language(answer, list(params.get("result_markers", [])))

    # 1. Three ways an answer needs no span: the question already states it; the
    #    rest of the corpus already states it; or the span never stated it, in
    #    which case the label is wrong and the answer came from somewhere else.
    answerable_without_span = (
        leakage >= float(params["max_question_leakage"])
        or elsewhere > int(params["max_other_papers_with_answer"])
        or grounding < float(params["min_answer_grounding"])
    )

    # 2. The answer identifies apparatus. A reagent catalogue number is retrieved
    #    by near-verbatim match in every configuration, so it discriminates
    #    between nothing.
    methods_provenance = bool(markers)

    # 3. The span is placeholder-free by construction, so this catches the
    #    drafted text pointing at an artefact that is not in the corpus.
    needs_placeholder = bool(
        PLACEHOLDER.search(span)
        or ARTEFACT_REFERENCE.search(question)
        or ARTEFACT_REFERENCE.search(answer)
    )

    # 4. Either the answer itself is restated in the abstract, or the span is.
    in_abstract = abstract_overlap >= float(params["max_abstract_overlap"]) or shared_ngram >= int(
        params["max_shared_ngram"]
    )

    flags = {
        "answerable_without_span": answerable_without_span,
        "methods_provenance": methods_provenance,
        "needs_placeholder": needs_placeholder,
        "in_abstract": in_abstract,
    }
    # Not a flag, and deliberately not auto-rejecting. A Methods passage earns a
    # question when its answer is a design choice that changes how a result reads
    # -- a positivity threshold, a set of covariates -- and not when it names an
    # instrument. Telling those apart is the judgement these checks cannot make,
    # so it is surfaced for the person doing the pass instead of guessed at.
    warnings: list[str] = []
    if section_kind in set(params.get("methods_section_kinds", [])) and not results:
        warnings.append(
            "methods section and no result language: is this a design choice that "
            "affects interpretation, or apparatus?"
        )

    return {
        "flags": flags,
        "signals": {
            "answer_grounding": round(grounding, 4),
            "question_leakage": round(leakage, 4),
            "other_papers_with_answer": elsewhere,
            "abstract_overlap": round(abstract_overlap, 4),
            "span_abstract_shared_ngram": shared_ngram,
            "provenance_markers": markers,
            "result_language": results,
        },
        "warnings": warnings,
        "auto_rejected": any(flags.values()),
        "reasons": sorted(name for name, fired in flags.items() if fired),
    }
