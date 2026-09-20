"""Qwen2.5-7B-Instruct at AWQ, under vLLM. The only GPU code in this stage.

vllm is imported inside the constructor, so `import ragbench.generation` stays
stdlib-cheap and the CPU smoke path never touches a CUDA runtime. It is an
optional extra (`.[generate]`) rather than a base dependency because it carries
its own transformers range: it must not share an environment with `.[specter]`,
which pins transformers to 4.57.x for the `adapters` library. Indexing and
generation are separate sessions anyway -- see docs/kaggle.md.

The one trap this file exists to avoid is documented at length below: Qwen's
checkpoint ships sampling defaults, vLLM reads them, and a request that sets
only `temperature=0` inherits the rest.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any

from .base import FINISH_LENGTH, FINISH_STOP, Completion, sampling_params
from .prompt import Prompt

logger = logging.getLogger(__name__)


class VllmGenerator:
    """One pinned checkpoint, greedy decoding, every sampling field stated."""

    def __init__(
        self,
        params: Mapping[str, Any],
        gpu_memory_utilization: float = 0.90,
        enforce_eager: bool = False,
    ) -> None:
        from transformers import AutoTokenizer
        from vllm import LLM, SamplingParams

        model_id = str(params["model_id"])
        revision = str(params.get("model_revision") or "")
        if not revision:
            raise ValueError(
                f"{model_id}: generation.model_revision is required. A Hub id is a "
                "mutable pointer, and the answers are a function of the checkpoint "
                "behind it."
            )
        decoding = sampling_params(params)
        self.max_new_tokens = int(decoding["max_new_tokens"])
        self.name = f"{model_id}@{revision[:12]}"

        # `generation_config="vllm"` tells vLLM to use its own neutral defaults
        # instead of reading the checkpoint's generation_config.json. Both Qwen
        # repos ship one with do_sample: true, temperature 0.7, top_p 0.8,
        # top_k 20, repetition_penalty 1.05 -- so without this, and without the
        # explicit fields below, "greedy at temperature 0" would be false while
        # every log line still said temperature 0. The argument is recent, hence
        # the fallback; the explicit SamplingParams below is the load-bearing
        # half and works on every version.
        common: dict[str, Any] = {
            "model": model_id,
            "revision": revision,
            "tokenizer_revision": revision,
            "quantization": str(params.get("quantization") or "") or None,
            "dtype": str(params.get("dtype") or "auto"),
            "max_model_len": int(params["max_model_len"]),
            "seed": int(decoding["seed"]),
            "gpu_memory_utilization": float(gpu_memory_utilization),
            "enforce_eager": bool(enforce_eager),
        }
        try:
            self._llm = LLM(generation_config="vllm", **common)
        except TypeError:
            logger.warning(
                "this vLLM does not accept generation_config=; relying on explicit "
                "SamplingParams to override the checkpoint's own defaults"
            )
            self._llm = LLM(**common)

        self._sampling = SamplingParams(
            temperature=float(decoding["temperature"]),
            top_p=float(decoding["top_p"]),
            top_k=int(decoding["top_k"]),
            repetition_penalty=float(decoding["repetition_penalty"]),
            # Not configured, because there is only one defensible value and it
            # is the neutral one. Stated rather than defaulted, for the reason
            # above: an omitted field is an inherited field.
            presence_penalty=0.0,
            frequency_penalty=0.0,
            max_tokens=self.max_new_tokens,
            seed=int(decoding["seed"]),
        )
        self._tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)

    def _chat_text(self, prompt: Prompt) -> str:
        """Lay the two turns into the model's own chat format.

        Qwen2.5-Instruct is trained with a chat template; feeding it raw text
        would put the instruction outside the turn structure it was tuned on and
        measure a different model from the one the config names.
        """
        return str(
            self._tokenizer.apply_chat_template(
                [
                    {"role": "system", "content": prompt.system},
                    {"role": "user", "content": prompt.user},
                ],
                tokenize=False,
                add_generation_prompt=True,
            )
        )

    def generate_many(self, prompts: Sequence[Prompt]) -> list[Completion]:
        if not prompts:
            return []
        outputs = self._llm.generate(
            [self._chat_text(prompt) for prompt in prompts], self._sampling
        )
        if len(outputs) != len(prompts):
            raise ValueError(
                f"vLLM returned {len(outputs)} outputs for {len(prompts)} prompts"
            )
        # vLLM returns outputs in input order, but the scheduler reorders
        # internally and the guarantee has moved between versions. Re-index by
        # request id where they are the integers vLLM assigns; a silently
        # transposed batch would attribute every answer to the wrong question
        # and look entirely healthy.
        ordered = list(outputs)
        identifiers = [str(getattr(out, "request_id", "")) for out in outputs]
        if all(identifier.isdigit() for identifier in identifiers):
            ordered = [
                out
                for _, out in sorted(
                    zip(identifiers, outputs, strict=True), key=lambda pair: int(pair[0])
                )
            ]
        return [self._completion(out) for out in ordered]

    def _completion(self, output: Any) -> Completion:
        first = output.outputs[0]
        reason = str(getattr(first, "finish_reason", "") or "")
        return Completion(
            text=str(first.text).strip(),
            n_prompt_tokens=len(output.prompt_token_ids or ()),
            n_completion_tokens=len(first.token_ids or ()),
            finish_reason=FINISH_LENGTH if reason == "length" else FINISH_STOP,
        )
