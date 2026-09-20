"""Rendering the rubric prompt. Its text comes from config, like the generator's.

Same reason: ``run_key`` hashes the whole resolved config, so editing a word of
the rubric moves the run id and scores produced under two rubrics can never
share a directory. A rubric in a module would let two incomparable runs wear one
name.

The judge sees four things -- question, reference answer, retrieved passages, and
the answer -- plus, for the two gold records that carry one, the note the author
attached to that item. It needs the passages because faithfulness is a question
about what the system was *shown*, which is not the same question as whether the
answer matches the reference.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ..hashing import canonical_json, sha256_text

PLACEHOLDER = re.compile(r"\{(question|reference_answer|context|answer|judge_note)\}")
REQUIRED_FIELDS: tuple[str, ...] = ("question", "reference_answer", "context", "answer")


@dataclass(frozen=True, slots=True)
class JudgePrompt:
    """The rendered rubric, plus the parts it was rendered from.

    ``system`` and ``user`` are what the judge is sent and the only things the
    digest covers. The four fields below are kept alongside for the CPU
    stand-in, which has to produce a defensible verdict without a language
    model and cannot be asked to parse them back out of the prose.
    """

    system: str
    user: str
    question: str = ""
    reference_answer: str = ""
    context: str = ""
    answer: str = ""

    @property
    def sha256(self) -> str:
        return sha256_text(canonical_json({"system": self.system, "user": self.user}))


def _validate(template: str) -> None:
    found = set(PLACEHOLDER.findall(template))
    missing = [name for name in REQUIRED_FIELDS if name not in found]
    if missing:
        raise ValueError(
            "judge.prompt_template must contain "
            + " and ".join(f"{{{name}}}" for name in missing)
            + f"; it has {sorted(found) or 'no placeholders'}. Without {{context}} the "
            "judge cannot assess faithfulness at all -- it would be comparing the answer "
            "to the reference and calling the result grounding."
        )


def render_note(params: Mapping[str, Any], note: str) -> str:
    """The per-item instruction, or nothing at all.

    Two of the twenty gold records carry one: a paper whose own sentence is
    malformed, and a span that is one clause of a longer sentence. Both would
    otherwise be marked down for reproducing the source correctly. An empty note
    renders to an empty string rather than an empty heading, so 18 items are not
    prompted with a blank instruction block that invites the judge to invent one.
    """
    if not note.strip():
        return ""
    template = str(params.get("judge_note_template") or "")
    if "{judge_note}" not in template:
        raise ValueError("judge.judge_note_template must contain {judge_note}")
    return template.replace("{judge_note}", note.strip())


def build_prompt(
    params: Mapping[str, Any],
    question: str,
    reference_answer: str,
    context: str,
    answer: str,
    judge_note: str = "",
) -> JudgePrompt:
    """Render the configured rubric for one answer."""
    template = str(params.get("prompt_template") or "")
    system = str(params.get("system_prompt") or "")
    if not template.strip() or not system.strip():
        raise ValueError("judge.system_prompt and judge.prompt_template must both be set")
    _validate(template)

    values = {
        "question": question,
        "reference_answer": reference_answer,
        "context": context,
        "answer": answer,
        "judge_note": render_note(params, judge_note),
    }
    # One pass, so a passage containing the literal text "{answer}" cannot be
    # rewritten by a later substitution.
    user = PLACEHOLDER.sub(lambda match: values[match.group(1)], template)
    return JudgePrompt(
        system=system.strip(),
        user=user.strip(),
        question=question,
        reference_answer=reference_answer,
        context=context,
        answer=answer,
    )


def rubric_digest(params: Mapping[str, Any]) -> str:
    """Digest of the rubric as configured, independent of any one answer.

    ``rubric_id`` is a label a human writes and can forget to change; this is
    derived from the text, so a report can print both and an edited "v1" is
    visible as one whose digest no longer matches.
    """
    return sha256_text(
        canonical_json(
            {
                "rubric_id": str(params.get("rubric_id") or ""),
                "system_prompt": str(params.get("system_prompt") or ""),
                "prompt_template": str(params.get("prompt_template") or ""),
                "judge_note_template": str(params.get("judge_note_template") or ""),
                "scales": list(params.get("scales") or ()),
                "verdicts": list(params.get("verdicts") or ()),
            }
        )
    )[:12]
