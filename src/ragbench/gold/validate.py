"""The five rejection checks, made mechanical wherever they can be.

A hand-verified gold set is only as trustworthy as the reasons it was filtered
by. "I read it and it seemed fine" is not a reason another person can audit, so
each ground for rejection gets a computed signal, a configured threshold, and its
numbers recorded on the candidate:

1. **Answerable without the span.** A question the generator can answer from what
   it already knows measures the generator's memory, not retrieval.
2. **Methods provenance, not a finding.** The answer identifies a reagent, an
   instrument, a software version, a housing condition -- or a count of what
   went into the study. That is a string lookup dressed as scientific QA, and it
   is answerable by near-verbatim matching, so every configuration scores alike
   and the set stops discriminating between arms.

   The count case needs its own rule, because the surface form does not separate
   it: **counts of findings are findings; counts of inputs are provenance.**
   "A core group of 48 proteins consistently enriched in plaques" is a
   discovered quantity and is the paper's result. "648 individuals", "49 samples
   after filtering" and "112 nerves from 56 rats" describe what went in, and are
   retrieved by exactly the same near-verbatim match as a catalogue number. Both
   are numbers next to nouns; only one was found by doing the science.
3. **Answer needs a placeholder.** ``[TABLE: Table 3]`` and ``[EQUATION]`` stand
   in for content the parse policy dropped; a question answered by one is
   unanswerable from the corpus as it exists.
4. **Answer is also in the abstract.** Abstracts are not chunked, but an answer
   restated there means the span is a near-duplicate of text elsewhere in the
   paper, which is the labelling ambiguity abstracts were excluded to avoid.
5. **The span withdraws its own claim.** The answer has to be a positive claim
   the paper asserts, not a described non-effect. A null result is a legitimate
   finding in science and an unusable gold answer here: a model that answers
   "NfL was not significantly affected" is scientifically right and will not
   match a reference answer phrased the other way round, so the question ends up
   scoring the judge's tolerance for hedging rather than retrieval quality.

   Narrow on purpose. It fires only on a **significance retraction** -- "did not
   reach statistical significance", "without reaching statistical difference" --
   and only when no sentence of the span asserts an unretracted result. Plain
   negation is not enough and must not be: "no correlation was shown in CpG1"
   contrasts with a significant correlation in the same sentence, "yet it has no
   significant gene overlap" is half of the finding itself, and "they were not
   affected by HS in the case of WT neurons" is the control arm of a result.
   Each of those is a paper asserting something.

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
#: A cardinal number, including "95.2" and "1,730".
NUMBER = r"\d[\d,]*(?:\.\d+)?"
#: Prepositions that put a count after the thing counted: "a cohort of 648".
OF = r"(?:of|from|in|comprising|totalling|totaling)"


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


def input_counts(text: str, units: Sequence[str]) -> list[str]:
    """Counts of study inputs found in the answer. See rule 2 in the module doc.

    Matched two ways, both requiring the number and the unit to be close enough
    to be in the same phrase: "112 nerves" and "56 Sprague-Dawley rats" (a number
    then at most two intervening words, which covers a strain or an adjective),
    and "a cohort of 648" (the unit, a preposition, then the number).

    Proximity is doing real work. "no differences in microglial numbers between
    transgenic and control rats; by 18-20 months" contains both a number and the
    unit "rats" and is a finding; they are twelve words apart and in different
    clauses, and neither pattern spans that.

    The unit list is configured and deliberately excludes "cells", "lesions" and
    "proteins", which are as often counted as *results* as they are as inputs.
    """
    if not units:
        return []
    alternation = "|".join(
        re.escape(unit) for unit in sorted(units, key=len, reverse=True)
    )
    before = re.compile(
        rf"\b{NUMBER}\b(?:\s+[A-Za-z][\w'-]*){{0,2}}\s+\b(?:{alternation})\b",
        re.IGNORECASE,
    )
    after = re.compile(rf"\b(?:{alternation})\b\s+{OF}\s+\b{NUMBER}\b", re.IGNORECASE)
    found = {match.group(0).strip() for match in before.finditer(text)}
    found |= {match.group(0).strip() for match in after.finditer(text)}
    return sorted(found)


def non_effect(span: str, retractions: Sequence[str], results: Sequence[str]) -> list[str]:
    """Significance retractions in a span that asserts nothing else.

    Sentence by sentence: a sentence carrying a retraction is withdrawn, and any
    other sentence carrying result language is an assertion that survives it. If
    one survives, the paper is still claiming something and the span is usable.
    If none does, every effect the span describes has been taken back.

    That sentence-level split is what separates the two shapes that look alike
    in the answer text. "We found significantly reduced N1 differences in the
    parietal cortex. Additionally, although not statistically significant, ..."
    asserts a finding and then qualifies a secondary one. "We observed a slight
    reduction ... although the differences did not reach statistical
    significance" is a single sentence that ends by withdrawing itself.
    """
    sentences = [part for part in re.split(r"(?<=[.!?])\s+", span) if part.strip()]
    withdrawn: list[str] = []
    for sentence in sentences:
        lowered = sentence.lower()
        hits = [phrase for phrase in retractions if phrase.lower() in lowered]
        if hits:
            withdrawn.extend(hits)
        elif result_language(sentence, results):
            return []
    return sorted(set(withdrawn))


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
    counts = input_counts(answer, list(params.get("input_count_units", [])))
    result_markers = list(params.get("result_markers", []))
    results = result_language(answer, result_markers)
    withdrawn = non_effect(
        span, list(params.get("significance_retractions", [])), result_markers
    )

    # 1. Three ways an answer needs no span: the question already states it; the
    #    rest of the corpus already states it; or the span never stated it, in
    #    which case the label is wrong and the answer came from somewhere else.
    answerable_without_span = (
        leakage >= float(params["max_question_leakage"])
        or elsewhere > int(params["max_other_papers_with_answer"])
        or grounding < float(params["min_answer_grounding"])
    )

    # 2. The answer identifies apparatus, or counts what went into the study.
    #    Either is retrieved by near-verbatim match in every configuration, so it
    #    discriminates between nothing. A count of what came *out* -- 48 proteins
    #    found enriched -- is a result and is left alone.
    methods_provenance = bool(markers) or bool(counts)

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

    # 5. Every effect the span describes is taken back before the span ends, so
    #    there is no positive claim for a reference answer to be.
    non_effect_answer = bool(withdrawn)

    flags = {
        "answerable_without_span": answerable_without_span,
        "methods_provenance": methods_provenance,
        "needs_placeholder": needs_placeholder,
        "in_abstract": in_abstract,
        "non_effect_answer": non_effect_answer,
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
            "input_counts": counts,
            "result_language": results,
            "significance_retractions": withdrawn,
        },
        "warnings": warnings,
        "auto_rejected": any(flags.values()),
        "reasons": sorted(name for name, fired in flags.items() if fired),
    }
