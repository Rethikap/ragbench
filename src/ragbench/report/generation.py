"""What the generator produced, per configuration, and what it cost.

Answer length is the reason this report exists rather than a line in the run
summary. The LLM-as-judge literature reports a length bias -- longer answers
score higher for reasons unrelated to being right -- so if the 8 configurations
differ in how long their answers are, any difference the judge finds is
confounded until length is controlled for. Measuring it before judging is the
only ordering that lets the control be honest rather than a post-hoc excuse.

Two length measures, because they can disagree: completion tokens as the model
counted them, and characters. A truncated answer inflates the first while the
second stays ordinary, so ``hit_max_new_tokens`` sits beside both.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..generation.base import FINISH_LENGTH, generation_params
from ..generation.pipeline import answers_path, load_answers
from ..generation.prompt import template_digest
from ..gold.freeze import GOLD_SET_FILENAME, verify_frozen
from ..retrieval.pipeline import cells, config_name
from ..types import GeneratedAnswer, Query
from .chunks import distribution


def _is_refusal(answer: GeneratedAnswer, refusal_text: str) -> bool:
    """Abstention, judged by the exact configured sentence.

    Exact rather than fuzzy on purpose. The system prompt asks for one specific
    string, so anything else is the model answering in its own words -- which may
    still be a refusal in spirit, but counting it here would turn a countable
    fact into a paraphrase judgement this report is not entitled to make.
    """
    return bool(refusal_text) and answer.answer.strip().rstrip(".") == refusal_text.rstrip(".")


def _summarise(answers: list[GeneratedAnswer], refusal_text: str) -> dict[str, Any]:
    if not answers:
        return {"n_answers": 0}
    return {
        "n_answers": len(answers),
        "completion_tokens": distribution([a.n_completion_tokens for a in answers]),
        "answer_chars": distribution([len(a.answer) for a in answers]),
        "prompt_tokens": distribution([a.n_prompt_tokens for a in answers]),
        "context_chunks": distribution([a.n_context_chunks for a in answers]),
        "latency_ms": distribution([int(round(a.latency_ms)) for a in answers]),
        "hit_max_new_tokens": sum(1 for a in answers if a.finish_reason == FINISH_LENGTH),
        "refusals": sum(1 for a in answers if _is_refusal(a, refusal_text)),
        "truncated_ids": [a.query_id for a in answers if a.finish_reason == FINISH_LENGTH],
    }


def build_report(
    resolved: dict[str, Any],
    configs_dir: Path,
    run_directory: Path,
    query_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Per-configuration length and timing, plus answers laid out per question."""
    params = generation_params(resolved)
    refusal_text = str(params.get("refusal_text") or "")
    queries: list[Query] = verify_frozen(
        Path(configs_dir) / GOLD_SET_FILENAME, str(resolved["gold"].get("gold_set_sha", ""))
    )
    questions = {query.query_id: query for query in queries}

    configs: list[dict[str, Any]] = []
    by_query: dict[str, dict[str, GeneratedAnswer]] = {}
    for chunking, embedding, rerank in cells(resolved):
        name = config_name(chunking, embedding, rerank)
        answers = load_answers(answers_path(run_directory, chunking, embedding, rerank))
        for answer in answers:
            by_query.setdefault(answer.query_id, {})[name] = answer
        configs.append(
            {
                "config": name,
                "chunking_level": chunking,
                "embedding_level": embedding,
                "rerank_level": rerank,
                **_summarise(answers, refusal_text),
            }
        )

    wanted = query_ids or [query.query_id for query in queries]
    side_by_side = [
        {
            "query_id": identifier,
            "question": questions[identifier].question if identifier in questions else "",
            "reference_answer": (
                questions[identifier].reference_answer if identifier in questions else ""
            ),
            "answers": {
                name: {
                    "answer": answer.answer,
                    "n_completion_tokens": answer.n_completion_tokens,
                    "n_context_chunks": answer.n_context_chunks,
                    "finish_reason": answer.finish_reason,
                }
                for name, answer in sorted(by_query.get(identifier, {}).items())
            },
        }
        for identifier in wanted
        if identifier in by_query
    ]

    generated = [config for config in configs if config["n_answers"]]
    return {
        "gold_set_sha": str(resolved["gold"].get("gold_set_sha", "")),
        "model_id": str(params.get("model_id", "")),
        "model_revision": str(params.get("model_revision") or ""),
        "quantization": params.get("quantization"),
        "prompt_template_id": str(params.get("prompt_template_id") or ""),
        "prompt_digest": template_digest(params),
        "max_new_tokens": int(params["max_new_tokens"]),
        "refusal_text": refusal_text,
        "n_questions": len(queries),
        "n_configs": len(configs),
        "n_configs_generated": len(generated),
        "n_answers": sum(config["n_answers"] for config in configs),
        "n_answers_expected": len(configs) * len(queries),
        "configs": configs,
        "side_by_side": side_by_side,
    }
