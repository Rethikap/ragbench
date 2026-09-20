"""The CPU stand-in judge: lexical overlap, and nothing that resembles judgement.

It exists so the judge stage is testable end to end with no API key, no network
and no spend -- the same reason `HashingEmbedder` and the extractive generator
exist. It scores completeness by overlap with the reference, faithfulness by
overlap with the retrieved context, and relevance by overlap with the question.

That is a caricature of the rubric, deliberately: it separates the *cases* the
rubric separates, so the pipeline, the aggregation and the agreement statistics
can all be exercised, and it does so without pretending to be a judge. It cannot
see that a value has been attached to the wrong entity, which is precisely the
failure the real rubric spends a paragraph on.

Its scores must never be reported as results. `report judge` prints a banner.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .base import ABSTAINED, Verdict, scales
from .prompt import JudgePrompt

WORD = re.compile(r"[A-Za-z0-9.]+")
STOPWORDS = frozenset(
    "a an and are as at be by for from in is it of on or that the to was were with what "
    "which who why how does did do this these those there their its not no".split()
)


def _terms(text: str) -> set[str]:
    return {w for w in WORD.findall(text.lower()) if w not in STOPWORDS and len(w) > 1}


def _band(share: float) -> float:
    """Overlap share to a 1-5 band. Fixed cut points, so it is reproducible."""
    for threshold, score in ((0.8, 5.0), (0.6, 4.0), (0.4, 3.0), (0.2, 2.0)):
        if share >= threshold:
            return score
    return 1.0


class StandInJudge:
    """Deterministic, offline, and not a judge."""

    name = "stand-in"

    def __init__(self, params: Mapping[str, Any]) -> None:
        self._params = dict(params)
        self._scales = scales(params)
        self._refusal = str(params.get("refusal_text") or "").strip()

    def _overlap(self, answer: set[str], other: set[str]) -> float:
        if not other:
            return 0.0
        return len(answer & other) / len(other)

    def score(self, prompt: JudgePrompt) -> Verdict:
        answer = prompt.answer.strip()
        if self._refusal and answer.rstrip(".") == self._refusal.rstrip("."):
            return Verdict(verdict=ABSTAINED, rationale="declined to answer")

        words = _terms(answer)
        reference = self._overlap(words, _terms(prompt.reference_answer))
        grounded = self._overlap(_terms(prompt.context), words) if words else 0.0
        asked = self._overlap(words, _terms(prompt.question))

        available = {
            "faithfulness": _band(grounded),
            "relevance": _band(asked),
            "completeness": _band(reference),
        }
        # Only the configured scales, so a rubric that renames one does not
        # silently keep scoring the old name.
        scored = {name: available.get(name, 3.0) for name in self._scales}

        if reference >= 0.7:
            verdict = "correct"
        elif reference >= 0.35:
            verdict = "partially_correct"
        else:
            verdict = "incorrect"
        return Verdict(
            verdict=verdict,
            scores=scored,
            rationale=(
                f"stand-in: {reference:.0%} of the reference's terms present, "
                f"{grounded:.0%} of the answer's terms grounded in the context"
            ),
        )
