"""Drafting a candidate question from a sampled passage.

Three implementations behind one interface, because the real drafter is the 7B
generator and this laptop has no GPU:

``qwen``
    The real one. Lazily imports transformers, greedy-decodes from the pinned
    generator, and is the drafter the frozen gold set should be produced with.
``replay:<path>``
    Replays questions drafted earlier -- on Kaggle, or by hand -- keyed by
    passage id, carrying each record's own ``drafted_by`` through to the
    candidate. This is what makes a GPU-drafted set reproducible from a laptop
    without re-running the model, and what lets a human-authored draft enter the
    pipeline through the same validation as a model-authored one.
``stand-in``
    No model, no download. Masks the rarest token of the passage's longest
    sentence and asks for it back. Enough to smoke-test the whole path offline;
    it is not a question-writing system and its output is labelled as such.

The prompt is pinned by ``gold.draft_prompt_id`` so a change to it is a change to
the gold set's provenance rather than an invisible edit.
"""

from __future__ import annotations

import re
from typing import Any, Protocol

from ..jsonl import read_jsonl
from .passages import Passage

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

Passage ({section}, {pmcid}):
\"\"\"
{passage}
\"\"\"

Reply with exactly two lines:
QUESTION: <your question>
ANSWER: <your answer>
"""

PROMPTS = {"v1": DRAFT_PROMPT_V1}
_REPLY = re.compile(r"QUESTION:\s*(?P<question>.+?)\s*ANSWER:\s*(?P<answer>.+)", re.S)


class Drafter(Protocol):
    name: str

    def draft(self, passage: Passage) -> tuple[str, str]:
        """Return ``(question, answer)`` for one passage."""


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
    """Pull the two fields out of a completion, or say why it was unusable."""
    match = _REPLY.search(reply)
    if not match:
        raise ValueError(f"drafter reply has no QUESTION/ANSWER pair: {reply[:160]!r}")
    return match.group("question").strip(), match.group("answer").strip()


class QwenDrafter:
    """The real drafter: the pinned generator, decoded greedily.

    Greedy because ``generation.temperature`` is 0.0 everywhere else in this
    project and a sampled draft would make the candidate set unreproducible for
    no gain -- the human verification step is where quality comes from.
    """

    def __init__(self, generation: dict[str, Any], prompt_id: str) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model_id = generation["model_id"]
        revision = generation.get("model_revision") or ""
        if not revision:
            raise ValueError(
                "generation.model_revision is required: a Hub id is a mutable pointer "
                "and the drafter's identity is part of the gold set's provenance."
            )
        self.name = f"qwen:{model_id}@{revision[:12]}"
        self.prompt_id = prompt_id
        self._max_new_tokens = int(generation.get("max_new_tokens", 512))
        self._tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
        self._model = AutoModelForCausalLM.from_pretrained(
            model_id, revision=revision, torch_dtype="auto", device_map="auto"
        )
        torch.manual_seed(int(generation["seed"]))

    def draft(self, passage: Passage) -> tuple[str, str]:
        messages = [{"role": "user", "content": build_prompt(passage, self.prompt_id)}]
        text = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self._tokenizer([text], return_tensors="pt").to(self._model.device)
        generated = self._model.generate(
            **inputs, max_new_tokens=self._max_new_tokens, do_sample=False
        )
        completion = self._tokenizer.decode(
            generated[0][inputs["input_ids"].shape[-1] :], skip_special_tokens=True
        )
        return parse_reply(completion)


class ReplayDrafter:
    """Replays drafts recorded earlier, keyed by passage id.

    Refuses a passage it has no record for rather than inventing one: a silent
    miss would drop a sampled passage from the candidate set and change what the
    rejection counts are measured against.
    """

    def __init__(self, path: str) -> None:
        self.name = f"replay:{path}"
        self._records: dict[str, dict[str, Any]] = {}
        for record in read_jsonl(path):
            self._records[record["passage_id"]] = record
        if not self._records:
            raise ValueError(f"no drafted questions in {path}")

    def drafted_by(self, passage: Passage) -> str:
        return str(self._records[passage.passage_id].get("drafted_by") or self.name)

    def draft(self, passage: Passage) -> tuple[str, str]:
        try:
            record = self._records[passage.passage_id]
        except KeyError:
            raise ValueError(
                f"no recorded draft for passage {passage.passage_id}. The sample changed "
                "since the drafts were recorded -- re-draft, or restore the seed and "
                "sampling parameters that produced them."
            ) from None
        return str(record["question"]).strip(), str(record["answer"]).strip()


class StandInDrafter:
    """Offline stand-in: a cloze question built from the passage itself.

    Deterministic and model-free, so the pipeline is smoke-testable end to end on
    a laptop. It writes a fill-in-the-blank, which is grounded and specific
    enough to exercise the validation checks honestly -- but it is a string
    operation, not question generation, and the gold set must not be frozen from
    it. ``ragbench gold freeze`` refuses to.
    """

    name = "stand-in"

    def __init__(self, frequency: dict[str, int] | None = None) -> None:
        self._frequency = frequency or {}

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
    specification: str, generation: dict[str, Any], prompt_id: str, frequency: dict[str, int]
) -> Drafter:
    if specification == "stand-in":
        return StandInDrafter(frequency)
    if specification == "qwen":
        return QwenDrafter(generation, prompt_id)
    if specification.startswith("replay:"):
        return ReplayDrafter(specification.removeprefix("replay:"))
    raise ValueError(
        f"unknown gold.drafter {specification!r}; expected 'qwen', 'stand-in' or 'replay:<path>'"
    )
