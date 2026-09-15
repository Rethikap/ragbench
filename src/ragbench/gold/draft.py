"""Where a candidate question comes from.

**The generator does not draft its own evaluation questions.** Qwen2.5-7B-Instruct
is the system under test at answer time; a model asked to write questions writes
them in its own idiom -- its phrasing, its way of framing a fact, its vocabulary
for hedging -- and then scores well at answer time partly because the questions
sound like it. That is a measurement artefact wearing the costume of a result,
and no amount of hand-verification removes it, because the questions a verifier
sees are already drawn from the generator's distribution.

So there is no Qwen drafter here, and there is deliberately no TODO for one. Two
implementations, both behind one interface:

``authored``
    The real path. Questions are written by a different author than the system
    under test -- recorded per record in ``drafted_by`` -- and read from the
    authored file, which also carries the evidence anchors and the selection and
    verification decisions. One committed file, one place a human decided
    anything.
``stand-in``
    No model, no download. Masks the rarest token of the passage's longest
    sentence and asks for it back. Enough to smoke-test the whole path offline;
    it is not a question-writing system, and ``gold freeze`` refuses its output.

The drafting prompt is kept and pinned by ``gold.draft_prompt_id`` because it is
the brief the author wrote to, and changing it changes what the questions are.
"""

from __future__ import annotations

import re
from typing import Any, Protocol

from .passages import Passage

#: Marks the model-free drafter. `gold freeze` refuses a set containing it.
STAND_IN = "stand-in"

DRAFT_PROMPT_V1 = """\
You are helping build an evaluation set for scientific-literature retrieval.

Below is one passage from the body of an open-access Alzheimer's biomarker paper.
Write ONE question that the passage answers, and the answer.

Requirements:
- The question must be answerable ONLY from this passage. A reader who knows the
  field but has not seen the passage must not be able to answer it.
- The answer must be a specific fact stated in the passage: a value, a cohort, a
  method, a named measure. Not a summary, not a generalisation.
- Do not refer to tables, figures, equations or supplementary material.
- Do not mention "the passage", "the study" or "the authors" in the question.
- Answer in one or two sentences.
- Mark the sentence or two that actually answer the question: these become the
  gold span, and they must be narrower than the passage.

Passage ({section}, {pmcid}):
\"\"\"
{passage}
\"\"\"

Reply with exactly two lines:
QUESTION: <your question>
ANSWER: <your answer>
"""

DRAFT_PROMPT_V2 = """\
You are helping build an evaluation set for scientific-literature retrieval.

Below is one passage from the body of an open-access Alzheimer's biomarker paper.
Write ONE question that the passage answers, and the answer.

THE ANSWER MUST BE A FINDING. A result, a measured relationship, an effect, a
claim the authors make, or a design choice that changes how a result is read
(which covariates a model adjusted for, what threshold defined a positive case).

THE ANSWER MUST NOT BE THE PROVENANCE OF A METHOD. Not an instrument or its
settings, not a reagent or its supplier, not a catalogue number, not a software
package or version, not animal housing, not a bare count of samples or animals.
Those are answerable by near-verbatim string match, so every retrieval
configuration finds them equally and the question measures nothing.

Also:
- The question must be answerable ONLY from this passage. A reader who knows the
  field but has not seen it must not be able to answer.
- The question must not contain its own answer.
- Do not refer to tables, figures, equations or supplementary material.
- Do not mention "the passage", "the study" or "the authors" in the question.
- Answer in one or two sentences.
- Mark the sentence or two that actually answer the question: these become the
  gold span, and they must be narrower than the passage.

Passage ({section}, {pmcid}):
\"\"\"
{passage}
\"\"\"

Reply with exactly two lines:
QUESTION: <your question>
ANSWER: <your answer>
"""

#: v1 is kept, not deleted. It is what the first round of candidates was written
#: to, and those candidates are still in the authored record with their
#: rejections; a prompt that produced rejected work is part of the evidence.
PROMPTS = {"v1": DRAFT_PROMPT_V1, "v2": DRAFT_PROMPT_V2}
_REPLY = re.compile(r"QUESTION:\s*(?P<question>.+?)\s*ANSWER:\s*(?P<answer>.+)", re.S)


class Drafter(Protocol):
    name: str

    def draft(self, passage: Passage) -> tuple[str, str]:
        """Return ``(question, answer)`` for one passage."""

    def drafted_by(self, passage: Passage) -> str:
        """Who wrote it. Recorded per candidate, not per run."""


def build_prompt(passage: Passage, prompt_id: str) -> str:
    try:
        template = PROMPTS[prompt_id]
    except KeyError:
        raise ValueError(
            f"unknown gold.draft_prompt_id {prompt_id!r}; known: {', '.join(sorted(PROMPTS))}"
        ) from None
    return template.format(
        section=passage.section or "body", pmcid=passage.pmcid, passage=passage.text
    )


def parse_reply(reply: str) -> tuple[str, str]:
    """Pull the two fields out of a drafted reply, or say why it was unusable."""
    match = _REPLY.search(reply)
    if not match:
        raise ValueError(f"drafted reply has no QUESTION/ANSWER pair: {reply[:160]!r}")
    return match.group("question").strip(), match.group("answer").strip()


class AuthoredDrafter:
    """Reads the authored questions, keyed by passage id.

    Refuses a passage it has no record for rather than inventing one: a silent
    miss would drop a sampled passage from the candidate set and change what the
    rejection counts are measured against.
    """

    name = "authored"

    def __init__(self, records: dict[str, dict[str, Any]]) -> None:
        if not records:
            raise ValueError("no authored questions; nothing to draft from")
        self._records = records

    def _record(self, passage: Passage) -> dict[str, Any]:
        try:
            return self._records[passage.passage_id]
        except KeyError:
            raise ValueError(
                f"no authored question for passage {passage.passage_id}. The sample "
                "changed since the questions were written -- re-author, or restore the "
                "seed and sampling parameters that produced them."
            ) from None

    def drafted_by(self, passage: Passage) -> str:
        return str(self._record(passage).get("drafted_by") or self.name)

    def draft(self, passage: Passage) -> tuple[str, str]:
        record = self._record(passage)
        return str(record["question"]).strip(), str(record["answer"]).strip()


class StandInDrafter:
    """Offline stand-in: a cloze question built from the passage itself.

    Deterministic and model-free, so the pipeline is smoke-testable end to end on
    a laptop. It writes a fill-in-the-blank, which is grounded and specific
    enough to exercise the validation checks honestly -- but it is a string
    operation, not question generation, and the gold set must not be frozen from
    it. ``ragbench gold freeze`` refuses to.
    """

    name = STAND_IN

    def __init__(self, frequency: dict[str, int] | None = None) -> None:
        self._frequency = frequency or {}

    def drafted_by(self, passage: Passage) -> str:
        return self.name

    def draft(self, passage: Passage) -> tuple[str, str]:
        from .validate import content_tokens

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", passage.text) if s.strip()]
        sentence = max(sentences, key=len) if sentences else passage.text
        tokens = content_tokens(sentence)
        if not tokens:
            raise ValueError(f"passage {passage.passage_id} has no content tokens")
        rarest = min(tokens, key=lambda token: (self._frequency.get(token, 0), token))
        blanked = re.sub(rf"\b{re.escape(rarest)}\b", "____", sentence, count=1, flags=re.I)
        return f"Complete the reported finding: {blanked}", rarest


def build_drafter(
    specification: str, authored: dict[str, dict[str, Any]], frequency: dict[str, int]
) -> Drafter:
    if specification == STAND_IN:
        return StandInDrafter(frequency)
    if specification == "authored":
        return AuthoredDrafter(authored)
    raise ValueError(
        f"unknown gold.drafter {specification!r}; expected 'authored' or 'stand-in'. "
        "There is no generator-drafted option: the system under test does not write "
        "the questions it will be scored on."
    )
