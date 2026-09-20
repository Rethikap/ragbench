"""The CPU stand-in: extractive, deterministic, and not a language model.

It exists so the generate stage is smoke-testable end to end on a laptop with no
GPU and no download, the same reason `WhitespaceTokenizer` and `HashingEmbedder`
exist. It picks the sentence in the context with the most words in common with
the question, and says the configured refusal when nothing overlaps.

Two things about that are deliberate. It genuinely reads the context, so a test
can tell a prompt that carries the passages from one that does not -- a stand-in
returning a constant would make the whole stage look healthy while assembling
nothing. And it can refuse, so the abstention path has coverage offline rather
than being first exercised on a GPU host at the end of a run.

It is not a language model, produces no fluent prose, and its answers must never
be reported as results.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from .base import FINISH_LENGTH, FINISH_STOP, Completion
from .prompt import Prompt

WORD = re.compile(r"[A-Za-z0-9]+")
#: Sentence-ish. Scientific prose is full of "0.05." and "et al.", so this
#: over-splits -- which costs nothing here, because the unit only has to be
#: small enough to be a plausible answer and stable enough to be deterministic.
SENTENCE = re.compile(r"[^.!?\n]+[.!?]?")
#: Words carried by every question, which would otherwise decide the match.
STOPWORDS = frozenset(
    "a an and are as at be by for from how in is it of on or that the to was were what "
    "which who why with does did do".split()
)


class StandInGenerator:
    """Longest lexical overlap with the question wins. No model, no weights."""

    def __init__(self, params: Mapping[str, Any]) -> None:
        self.max_new_tokens = int(params["max_new_tokens"])
        self.refusal_text = str(params.get("refusal_text") or "")
        self.name = "stand-in"

    def _terms(self, question: str) -> set[str]:
        return {word for word in WORD.findall(question.lower()) if word not in STOPWORDS}

    def _best_sentence(self, context: str, terms: set[str]) -> str:
        best, best_score = "", 0
        for match in SENTENCE.finditer(context):
            sentence = match.group().strip()
            if not sentence:
                continue
            words = set(WORD.findall(sentence.lower()))
            score = len(words & terms)
            # Strictly greater: the first sentence wins a tie, so the answer is a
            # function of the context's order and not of iteration order.
            if score > best_score:
                best, best_score = sentence, score
        return best

    def generate_many(self, prompts: Sequence[Prompt]) -> list[Completion]:
        return [self._generate(prompt) for prompt in prompts]

    def _generate(self, prompt: Prompt) -> Completion:
        terms = self._terms(prompt.question)
        sentence = self._best_sentence(prompt.context, terms) if terms else ""
        finish = FINISH_STOP
        if not sentence:
            answer = self.refusal_text
        else:
            words = sentence.split()
            if len(words) > self.max_new_tokens:
                # Truncated exactly the way the real generator's ceiling truncates:
                # mid-sentence, and reported as such rather than as a short answer.
                words = words[: self.max_new_tokens]
                finish = FINISH_LENGTH
            answer = " ".join(words)
        return Completion(
            text=answer,
            n_prompt_tokens=len(WORD.findall(prompt.system)) + len(WORD.findall(prompt.user)),
            n_completion_tokens=len(WORD.findall(answer)),
            finish_reason=finish,
        )
