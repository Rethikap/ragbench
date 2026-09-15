"""The three rejection checks, made mechanical wherever they can be.

A hand-verified gold set is only as trustworthy as the reasons it was filtered
by. "I read it and it seemed fine" is not a reason another person can audit, so
each of the three grounds for rejection gets a computed signal, a configured
threshold, and its evidence recorded on the candidate:

1. **Answerable without the passage.** A question about general knowledge
   measures what the generator already knows, not what retrieval fetched.
2. **Answer needs a placeholder.** ``[TABLE: Table 3]`` and ``[EQUATION]`` stand
   in for content the parse policy dropped; a question answered by one is
   unanswerable from the corpus as it exists.
3. **Answer is also in the abstract.** Abstracts are not chunked, but an answer
   restated there means the body passage is a near-duplicate of text elsewhere
   in the paper, which is the labelling ambiguity abstracts were excluded to
   avoid in the first place.

These auto-reject. Everything that survives still gets read by a person: the
checks are a floor, not the verification.
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


def content_tokens(text: str) -> list[str]:
    """Lowercased word and number tokens, stopwords removed, order preserved."""
    return [token for token in (m.group(0).lower() for m in WORD.finditer(text))
            if token not in STOPWORDS]


def document_frequency(bodies: Iterable[str]) -> dict[str, int]:
    """How many papers each content token appears in.

    The corpus is the reference for "general knowledge" rather than an external
    frequency list: a token every Alzheimer's paper uses ("amyloid", "cognitive")
    identifies nothing within this corpus, whatever its frequency in English.
    """
    frequency: dict[str, int] = {}
    for body in bodies:
        for token in set(content_tokens(body)):
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


def check(
    question: str,
    answer: str,
    passage: str,
    abstract: str,
    frequency: dict[str, int],
    params: dict[str, Any],
) -> dict[str, Any]:
    """Run all three checks. Returns the flags, the evidence, and the verdict."""
    answer_tokens = content_tokens(answer)
    passage_tokens = content_tokens(passage)
    abstract_tokens = content_tokens(abstract)
    passage_set = set(passage_tokens)

    grounding = _share(answer_tokens, passage_set)
    anchors = sorted(
        {
            token
            for token in answer_tokens
            if token in passage_set and frequency.get(token, 0) <= int(params["max_anchor_df"])
        }
    )
    abstract_overlap = _share(answer_tokens, set(abstract_tokens))
    shared_ngram = longest_shared_ngram(passage_tokens, abstract_tokens)

    # 1. Without a rare token shared by answer and passage, nothing in the answer
    #    distinguishes this paper from the other 99 -- the question is about the
    #    field, not about the passage. Low grounding says the same thing more
    #    bluntly: the answer was not drawn from the passage at all.
    general_knowledge = not anchors or grounding < float(params["min_answer_grounding"])

    # 2. The passage is placeholder-free by construction, so this catches the
    #    drafted text pointing at an artefact that is not in the corpus.
    needs_placeholder = bool(
        PLACEHOLDER.search(passage)
        or ARTEFACT_REFERENCE.search(question)
        or ARTEFACT_REFERENCE.search(answer)
    )

    # 3. Either the answer itself is restated in the abstract, or the passage is.
    in_abstract = abstract_overlap >= float(params["max_abstract_overlap"]) or shared_ngram >= int(
        params["max_shared_ngram"]
    )

    flags = {
        "general_knowledge": general_knowledge,
        "needs_placeholder": needs_placeholder,
        "in_abstract": in_abstract,
    }
    return {
        "flags": flags,
        # Named "signals" rather than "evidence": a candidate record already has
        # an `evidence` field, and it is the gold span's text. Two meanings of
        # the same word in one record is how a span quietly becomes a diagnostic
        # dict -- which it did, once.
        "signals": {
            "answer_grounding": round(grounding, 4),
            "rare_anchors": anchors[:8],
            "n_rare_anchors": len(anchors),
            "abstract_overlap": round(abstract_overlap, 4),
            "passage_abstract_shared_ngram": shared_ngram,
        },
        "auto_rejected": any(flags.values()),
        "reasons": sorted(name for name, fired in flags.items() if fired),
    }
