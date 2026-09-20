"""Assembling the prompt. Its text comes from config, never from this file.

That is the point of the module, not an implementation detail. If the wording
lived here, two runs with different prompts would be two runs with the same
resolved config and therefore the same run id, and their answers would land in
one directory. Because it lives in ``base.generation``, editing a word changes
the config digest and the run moves -- which is the behaviour that makes an
answer traceable to the instruction that produced it.

What this module does own is the *assembly*: how retrieved chunks become one
context string, and how the two rendered turns are digested so a resumed run can
prove it is continuing the same work rather than mixing two prompts.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ..hashing import canonical_json, sha256_text

#: The only substitutions a template may make. Applied in ONE pass: replacing
#: them one after another would let a passage containing the literal text
#: "{question}" be rewritten by the second replacement.
PLACEHOLDER = re.compile(r"\{(context|question)\}")
REQUIRED_FIELDS: tuple[str, ...] = ("context", "question")


@dataclass(frozen=True, slots=True)
class Prompt:
    """One rendered prompt: the two turns, plus the parts they were built from.

    ``system`` and ``user`` are what the model sees and the only things the
    digest covers. ``context`` and ``question`` are kept alongside for the CPU
    stand-in, which has to answer from the passages without a language model,
    and for the side-by-side view in ``report generation``.
    """

    system: str
    user: str
    context: str
    question: str

    @property
    def sha256(self) -> str:
        """Digest of what the model is shown -- not of the template.

        Two configurations retrieve different chunks for the same question, so
        this differs across the 8 cells by design. What it pins is that a given
        cell's answer was produced from a given context: if the assembly, the
        template or the retrieved chunks change, the digest moves and the
        generate stage refuses to top up a file written under the old one.
        """
        return sha256_text(canonical_json({"system": self.system, "user": self.user}))


def render_context(texts: Sequence[str], separator: str) -> str:
    """Join retrieved chunk texts in rank order.

    Rank order, not document order: the ranking is what retrieval produced, and
    re-sorting here would quietly undo the rerank factor for the one arm it is
    supposed to distinguish.

    Chunks arrive stripped of trailing whitespace so the separator is the only
    thing between them -- otherwise a chunk ending in a newline would be spaced
    differently from one that does not, and the context would carry a formatting
    difference that tracks the chunker rather than the text.
    """
    return separator.join(text.strip() for text in texts)


def _validate(template: str) -> None:
    found = set(PLACEHOLDER.findall(template))
    missing = [field for field in REQUIRED_FIELDS if field not in found]
    if missing:
        raise ValueError(
            "generation.prompt_template must contain "
            + " and ".join(f"{{{field}}}" for field in missing)
            + f"; it has {sorted(found) or 'no placeholders'}. The template is the only "
            "thing that puts the retrieved context in front of the model, so a missing "
            "{context} would generate 160 answers from the question alone."
        )


def build_prompt(params: Mapping[str, Any], context: str, question: str) -> Prompt:
    """Render the configured template. Fails loudly on a template that cannot work."""
    template = str(params.get("prompt_template") or "")
    system = str(params.get("system_prompt") or "")
    if not template.strip():
        raise ValueError("generation.prompt_template is empty; the prompt lives in config")
    if not system.strip():
        raise ValueError("generation.system_prompt is empty; the prompt lives in config")
    _validate(template)

    values = {"context": context, "question": question}
    user = PLACEHOLDER.sub(lambda match: values[match.group(1)], template)
    return Prompt(system=system.strip(), user=user.strip(), context=context, question=question)


def template_digest(params: Mapping[str, Any]) -> str:
    """Digest of the prompt as configured, independent of any one question.

    ``prompt_template_id`` is a label a human writes and a human can forget to
    change. This is derived from the text, so a report can print both and an
    edited "v1" is visible as one whose digest no longer matches the last run's.
    """
    return sha256_text(
        canonical_json(
            {
                "prompt_template_id": str(params.get("prompt_template_id") or ""),
                "system_prompt": str(params.get("system_prompt") or ""),
                "prompt_template": str(params.get("prompt_template") or ""),
                "context_separator": str(params.get("context_separator") or ""),
            }
        )
    )[:12]
