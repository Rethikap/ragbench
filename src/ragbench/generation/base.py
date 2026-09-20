"""The generator, behind an interface: one real arm, one CPU stand-in.

Generation is **not a factor**. One model, one decoding setting, one prompt,
held fixed across all 8 runs -- so this module reads ``base.generation`` and
there is no ``arm_params`` here to read a factor level with. What varies between
the 8 cells is the context the generator is handed, and nothing else. A
generation parameter that moved with a factor would be an uncontrolled variable
wearing that factor's name.

The real arm is Qwen2.5-7B-Instruct at AWQ under vLLM and imports vllm inside
its constructor, so ``import ragbench.generation`` stays cheap and the CPU smoke
path never drags a CUDA runtime in. ``model_id: stand-in`` selects the offline
implementation *by id*, which means a config asking for the real model cannot
silently degrade to the stand-in when the download fails -- it fails instead.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from .prompt import Prompt

#: The decode ended on an end-of-turn token: the model chose to stop.
FINISH_STOP = "stop"
#: The decode hit ``max_new_tokens``: the model was cut off mid-answer. A
#: different object from a short answer, and counted separately for that reason.
FINISH_LENGTH = "length"

#: Sampling fields that must be sent on every request. Qwen's own
#: generation_config.json sets do_sample/temperature/top_p/top_k/
#: repetition_penalty, and vLLM reads it -- so any field left unstated here is
#: inherited from the checkpoint and decoding stops being greedy without saying
#: so. Stating the neutral value of each is what makes "temperature 0" true.
SAMPLING_FIELDS: tuple[str, ...] = (
    "temperature",
    "top_p",
    "top_k",
    "repetition_penalty",
    "max_new_tokens",
    "seed",
)


@dataclass(frozen=True, slots=True)
class Completion:
    """What one decode produced. ``finish_reason`` is the decode's own account."""

    text: str
    n_prompt_tokens: int
    n_completion_tokens: int
    finish_reason: str = FINISH_STOP


class Generator(Protocol):
    name: str
    max_new_tokens: int

    def generate_many(self, prompts: Sequence[Prompt]) -> list[Completion]:
        """Answer each prompt. One call, because batching is where the GPU time is."""


def generation_params(resolved: Mapping[str, Any]) -> dict[str, Any]:
    """Generation settings: ``base.generation``, whole, and nothing else.

    No factor level is merged in, deliberately -- see the module docstring.
    """
    return dict(resolved["base"]["generation"])


def sampling_params(params: Mapping[str, Any]) -> dict[str, Any]:
    """The decoding settings, as configured, with every field required present.

    Missing one is an error rather than a default: a default here would be
    indistinguishable from the checkpoint's own, which is the failure this
    function exists to make impossible.
    """
    missing = [field for field in SAMPLING_FIELDS if params.get(field) is None]
    if missing:
        raise ValueError(
            f"generation is missing {', '.join(missing)}. Every sampling field must be "
            "stated: Qwen ships a generation_config.json with do_sample, temperature "
            "0.7, top_p 0.8, top_k 20 and repetition_penalty 1.05, and an unstated "
            "field is inherited from it."
        )
    return {field: params[field] for field in SAMPLING_FIELDS}


def build_generator(params: Mapping[str, Any], **runtime: Any) -> Generator:
    """Construct the generator named by ``model_id``, or the offline stand-in.

    ``runtime`` carries host settings that cannot change an answer -- GPU memory
    fraction, batch size. They are keyword arguments rather than config because
    config reaches the run id, and a run re-done on a smaller GPU is the same
    run. Anything that *can* change an answer (``max_model_len``, every sampling
    field) is config and is not accepted here.
    """
    model_id = str(params["model_id"])
    if model_id == "stand-in":
        from .standin import StandInGenerator

        return StandInGenerator(params)
    from .vllm_backend import VllmGenerator

    return VllmGenerator(params, **runtime)
