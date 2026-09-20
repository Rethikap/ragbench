"""The generation report: length, truncation, abstention, and the answers.

Answer length is the reason the report exists. The judge literature reports a
length bias, so if the 8 configurations differ in how long their answers are,
any difference the judge later finds is confounded until length is controlled
for -- and it can only be controlled for if it was measured first.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ragbench.generation.pipeline import answers_path
from ragbench.gold.freeze import gold_set_sha, write_gold_set
from ragbench.jsonl import write_jsonl
from ragbench.report.generation import build_report
from ragbench.report.generation_render import render
from ragbench.types import GeneratedAnswer, GoldSpan, Query

GENERATION: dict[str, Any] = {
    "model_id": "Qwen/Qwen2.5-7B-Instruct-AWQ",
    "model_revision": "b" * 40,
    "quantization": "awq",
    "max_new_tokens": 512,
    "prompt_template_id": "v1",
    "system_prompt": "Answer from the passages only.",
    "prompt_template": "{context}\n\nQuestion: {question}",
    "refusal_text": "The provided context does not contain the answer.",
    "context_separator": "\n\n",
}


def _query(identifier: str) -> Query:
    return Query(
        query_id=identifier,
        question=f"question {identifier}?",
        reference_answer="the hippocampus",
        gold=GoldSpan(
            pmcid="PMC1", char_start=0, char_end=60, section="Results",
            context_start=0, context_end=200,
        ),
        verified=True,
    )


def _answer(identifier: str, text: str, tokens: int, finish: str = "stop") -> dict[str, Any]:
    return GeneratedAnswer(
        query_id=identifier,
        answer=text,
        prompt_sha256="0" * 64,
        n_prompt_tokens=1500,
        n_completion_tokens=tokens,
        latency_ms=120.0,
        finish_reason=finish,
        context_chunk_ids=("PMC1-0000",),
        n_context_chunks=1,
    ).to_dict()


def _world(tmp_path: Path, answers: list[dict[str, Any]]) -> tuple[dict[str, Any], Path, Path]:
    configs = tmp_path / "configs"
    run = tmp_path / "run"
    configs.mkdir(parents=True, exist_ok=True)
    queries = [_query("q001"), _query("q002")]
    write_gold_set(configs / "gold_set.jsonl", queries)
    resolved = {
        "base": {"generation": dict(GENERATION)},
        "gold": {"gold_set_sha": gold_set_sha(queries)},
        "factors": {
            "chunking": {"fixed": {}},
            "embedding": {"bge": {}},
            "rerank": {"off": {}},
        },
    }
    write_jsonl(answers_path(run, "fixed", "bge", "off"), answers)
    return resolved, configs, run


def test_answer_length_is_reported_per_configuration(tmp_path: Path) -> None:
    resolved, configs, run = _world(
        tmp_path, [_answer("q001", "a short one.", 4), _answer("q002", "a much longer one.", 40)]
    )
    report = build_report(resolved, configs, run)
    (config,) = report["configs"]
    assert config["completion_tokens"]["mean"] == 22.0
    assert config["completion_tokens"]["max"] == 40
    assert config["answer_chars"]["n"] == 2


def test_truncated_answers_are_counted_and_named(tmp_path: Path) -> None:
    """A cut-off answer is a different object from a brief one: the judge marks
    it down for an incompleteness the generator never chose, so it has to be
    separable from the results rather than averaged into them."""
    resolved, configs, run = _world(
        tmp_path,
        [_answer("q001", "cut off mid-", 512, finish="length"), _answer("q002", "fine.", 7)],
    )
    report = build_report(resolved, configs, run)
    (config,) = report["configs"]
    assert config["hit_max_new_tokens"] == 1
    assert config["truncated_ids"] == ["q001"]
    assert "[TRUNCATED at the ceiling]" in render(report)


def test_abstentions_are_counted_by_the_exact_configured_sentence(tmp_path: Path) -> None:
    """Exact, not fuzzy. Counting paraphrases would turn a countable fact into a
    judgement this report is not entitled to make."""
    resolved, configs, run = _world(
        tmp_path,
        [
            _answer("q001", GENERATION["refusal_text"], 9),
            _answer("q002", "I am not sure the passages say.", 8),
        ],
    )
    (config,) = build_report(resolved, configs, run)["configs"]
    assert config["refusals"] == 1


def test_the_prompt_digest_is_derived_from_the_text_not_the_label(tmp_path: Path) -> None:
    resolved, configs, run = _world(tmp_path, [_answer("q001", "x", 1)])
    first = build_report(resolved, configs, run)["prompt_digest"]
    resolved["base"]["generation"]["system_prompt"] += " Be brief."
    assert build_report(resolved, configs, run)["prompt_digest"] != first


def test_the_answers_are_laid_out_per_question_for_reading(tmp_path: Path) -> None:
    resolved, configs, run = _world(
        tmp_path, [_answer("q001", "the hippocampus.", 3), _answer("q002", "tau.", 2)]
    )
    report = build_report(resolved, configs, run)
    assert [item["query_id"] for item in report["side_by_side"]] == ["q001", "q002"]
    assert report["side_by_side"][0]["answers"]["fixed-bge-rerank_off"]["answer"] == (
        "the hippocampus."
    )
    assert report["side_by_side"][0]["reference_answer"] == "the hippocampus"


def test_one_question_can_be_singled_out(tmp_path: Path) -> None:
    resolved, configs, run = _world(
        tmp_path, [_answer("q001", "a", 1), _answer("q002", "b", 1)]
    )
    report = build_report(resolved, configs, run, query_ids=["q002"])
    assert [item["query_id"] for item in report["side_by_side"]] == ["q002"]


def test_an_ungenerated_run_says_so_rather_than_rendering_zeros(tmp_path: Path) -> None:
    resolved, configs, run = _world(tmp_path, [])
    report = build_report(resolved, configs, run)
    assert report["n_answers"] == 0
    assert report["n_answers_expected"] == 2
    assert "Nothing generated yet" in render(report)


def test_a_stand_in_run_cannot_be_mistaken_for_results(tmp_path: Path) -> None:
    """Its answers are extracted sentences. Nothing stops someone pasting a
    table into a thesis except the table saying what produced it."""
    resolved, configs, run = _world(tmp_path, [_answer("q001", "x", 1)])
    resolved["base"]["generation"]["model_id"] = "stand-in"
    assert "CPU STAND-IN" in render(build_report(resolved, configs, run))


def test_the_report_is_ascii_so_a_legacy_console_can_print_it(tmp_path: Path) -> None:
    """Reports quote the corpus, and the corpus is biomedical. A Windows console
    at cp1252 raises on a beta, and the crash lands after the work is done."""
    resolved, configs, run = _world(
        tmp_path, [_answer("q001", "Aβ42 rose 2× (p ≤ 0.05).", 12)]
    )
    rendered = render(build_report(resolved, configs, run))
    # The answer's own characters pass through; the report's furniture adds none.
    furniture = "\n".join(
        line for line in rendered.splitlines() if "Aβ42" not in line
    )
    assert furniture.isascii()
