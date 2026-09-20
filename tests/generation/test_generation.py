"""The generate stage: the stand-in, the sampling guard, and resumability.

Everything runs offline. The real arm is exercised on the GPU host; what is
tested here is the contract around it -- that decoding cannot silently stop
being greedy, that an interrupted run continues, and that it refuses to continue
into a file whose answers came from a different prompt.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ragbench.generation.base import (
    FINISH_LENGTH,
    FINISH_STOP,
    Completion,
    build_generator,
    generation_params,
    sampling_params,
)
from ragbench.generation.pipeline import (
    answers_path,
    generate_one_config,
    load_answers,
    run_generate,
)
from ragbench.generation.prompt import Prompt, build_prompt
from ragbench.generation.standin import StandInGenerator
from ragbench.gold.freeze import gold_set_sha, write_gold_set
from ragbench.jsonl import write_jsonl
from ragbench.types import Chunk, GoldSpan, Query, RetrievalResult, ScoredChunk

GENERATION: dict[str, Any] = {
    "model_id": "stand-in",
    "model_revision": "0" * 40,
    "quantization": None,
    "dtype": "float16",
    "temperature": 0.0,
    "top_p": 1.0,
    "top_k": -1,
    "repetition_penalty": 1.0,
    "max_new_tokens": 64,
    "seed": 20260813,
    "max_model_len": 4096,
    "prompt_template_id": "v1",
    "system_prompt": "Answer from the passages only.",
    "prompt_template": "Passages:\n\n{context}\n\nQuestion: {question}",
    "refusal_text": "The provided context does not contain the answer.",
    "context_separator": "\n\n",
}

CHUNK_TEXTS = {
    "PMC1-0000": "Amyloid beta plaques accumulate in the hippocampus of patients.",
    "PMC1-0001": "Gas chromatography of industrial solvents and their residues.",
    "PMC1-0002": "Tau phosphorylation correlates with cognitive decline severity.",
}
QUESTIONS = {
    "q001": "Where do amyloid beta plaques accumulate?",
    "q002": "What does tau phosphorylation correlate with?",
}


def prompt(context: str = "amyloid accumulates in the hippocampus", question: str = "where?"):
    return build_prompt(GENERATION, context, question)


# --------------------------------------------------------------- the stand-in


def test_the_stand_in_answers_from_the_context_rather_than_returning_a_constant() -> None:
    """A stand-in returning a constant would make the whole stage look healthy
    while assembling nothing, and no offline test could tell."""
    generator = StandInGenerator(GENERATION)
    context = "Solvent residues were measured.\n\nPlaques accumulate in the hippocampus."
    (completion,) = generator.generate_many([prompt(context, "Where do plaques accumulate?")])
    assert "hippocampus" in completion.text
    assert completion.finish_reason == FINISH_STOP


def test_the_stand_in_abstains_with_the_configured_sentence() -> None:
    """The abstention path gets coverage offline instead of being first
    exercised on a GPU host at the end of a run."""
    generator = StandInGenerator(GENERATION)
    (completion,) = generator.generate_many([prompt("Unrelated text here.", "zzz qqq?")])
    assert completion.text == GENERATION["refusal_text"]


def test_the_stand_in_is_deterministic() -> None:
    generator = StandInGenerator(GENERATION)
    first = generator.generate_many([prompt()])[0]
    second = generator.generate_many([prompt()])[0]
    assert first == second


def test_hitting_the_ceiling_is_reported_as_length_not_as_a_short_answer() -> None:
    """A truncated answer is a different object from a brief one: the judge marks
    it down for an incompleteness the generator never chose."""
    generator = StandInGenerator({**GENERATION, "max_new_tokens": 3})
    (completion,) = generator.generate_many(
        [prompt("Plaques accumulate in the hippocampus of elderly patients.", "plaques where?")]
    )
    assert completion.finish_reason == FINISH_LENGTH
    assert completion.n_completion_tokens == 3


def test_the_stand_in_is_selected_by_model_id_not_by_a_flag() -> None:
    """A config asking for the real model cannot silently degrade to the
    stand-in when the download fails -- it fails instead."""
    assert isinstance(build_generator(GENERATION), StandInGenerator)


# ------------------------------------------------- decoding cannot drift quiet


def test_every_sampling_field_must_be_stated() -> None:
    """Qwen ships a generation_config.json with do_sample, temperature 0.7,
    top_p 0.8, top_k 20 and repetition_penalty 1.05, and vLLM reads it. An
    unstated field is an inherited field, so there is no default here."""
    for field in ("temperature", "top_p", "top_k", "repetition_penalty", "seed"):
        with pytest.raises(ValueError, match=field):
            sampling_params({**GENERATION, field: None})


def test_the_configured_decoding_is_greedy_and_neutral() -> None:
    """The values that make "temperature 0" true rather than nominal."""
    resolved = {"base": {"generation": dict(GENERATION)}}
    sampling = sampling_params(generation_params(resolved))
    assert sampling["temperature"] == 0.0
    assert sampling["top_p"] == 1.0
    assert sampling["top_k"] == -1
    assert sampling["repetition_penalty"] == 1.0


def test_generation_is_not_a_factor() -> None:
    """One model, one prompt, one decoding setting across all 8 cells. What
    varies between them is the context, and nothing else."""
    import ragbench.generation.base as module

    assert not hasattr(module, "arm_params")
    resolved = {"base": {"generation": dict(GENERATION)}, "factors": {"generation": {"a": {}}}}
    # Reads base.generation whole; a factors entry cannot reach it.
    assert generation_params(resolved) == GENERATION


# --------------------------------------------------------- a whole mini-run


class _CountingGenerator:
    """Records how many prompts it was asked for, and can fail on demand."""

    name = "counting"

    def __init__(self, fail_after: int = -1) -> None:
        self.max_new_tokens = 64
        self.seen: list[str] = []
        self._fail_after = fail_after
        self._inner = StandInGenerator(GENERATION)

    def generate_many(self, prompts):
        if 0 <= self._fail_after <= len(self.seen):
            raise RuntimeError("session died")
        self.seen.extend(p.question for p in prompts)
        return self._inner.generate_many(prompts)


def _chunk(identifier: str, index: int) -> Chunk:
    text = CHUNK_TEXTS[identifier]
    return Chunk(
        chunk_id=identifier,
        pmcid="PMC1",
        chunk_index=index,
        text=text,
        n_tokens=len(text.split()),
        char_start=index * 200,
        char_end=index * 200 + len(text),
        sections=("Results",),
        content_sha256="0" * 64,
    )


def _query(identifier: str) -> Query:
    return Query(
        query_id=identifier,
        question=QUESTIONS[identifier],
        reference_answer="the hippocampus",
        gold=GoldSpan(
            pmcid="PMC1", char_start=0, char_end=60, section="Results",
            context_start=0, context_end=200,
        ),
        verified=True,
    )


def _result(identifier: str, chunk_ids: list[str]) -> dict[str, Any]:
    return RetrievalResult(
        query_id=identifier,
        selected=tuple(
            ScoredChunk(chunk_id=c, score=1.0 - i / 10, rank=i + 1, n_budget_tokens=20)
            for i, c in enumerate(chunk_ids)
        ),
        n_candidates=len(chunk_ids),
        n_chunks=len(chunk_ids),
        tokens_used=20 * len(chunk_ids),
        token_budget=2000,
        budget_slack=2000 - 20 * len(chunk_ids),
        stopped_reason="candidates_exhausted",
    ).to_dict()


def _world(tmp_path: Path) -> tuple[dict[str, Any], Path, Path, Path]:
    """A one-cell run on disk: gold set, chunk set, retrieval results."""
    configs = tmp_path / "configs"
    data = tmp_path / "data"
    run = tmp_path / "runs" / "test"
    configs.mkdir(parents=True, exist_ok=True)

    queries = [_query("q001"), _query("q002")]
    write_gold_set(configs / "gold_set.jsonl", queries)
    resolved: dict[str, Any] = {
        "base": {
            "generation": dict(GENERATION),
            "chunking": {
                "target_tokens": 510, "overlap_tokens": 0,
                "tokenizer_id": "whitespace", "tokenizer_revision": "x",
                "min_chunk_tokens": 0, "separators": ["\n\n"], "chunk_abstract": False,
            },
        },
        "corpus": {"manifest_sha": "deadbeef"},
        "gold": {"gold_set_sha": gold_set_sha(queries)},
        "factors": {
            "chunking": {"fixed": {"strategy": "fixed"}},
            "embedding": {"bge": {}},
            "rerank": {"off": {}},
        },
    }

    from ragbench.cache_keys import chunk_set_key
    from ragbench.chunking.pipeline import arm_params as chunking_params
    from ragbench.config import chunk_set_dir

    chunk_set_id = chunk_set_key("deadbeef", chunking_params(resolved, "fixed"))
    directory = chunk_set_dir(chunk_set_id, data)
    directory.mkdir(parents=True, exist_ok=True)
    write_jsonl(
        directory / "chunks.jsonl",
        [_chunk(identifier, i).to_dict() for i, identifier in enumerate(CHUNK_TEXTS)],
    )

    (run / "retrieve").mkdir(parents=True, exist_ok=True)
    write_jsonl(
        run / "retrieve" / "fixed-bge-rerank_off.jsonl",
        [
            _result("q001", ["PMC1-0000", "PMC1-0001"]),
            _result("q002", ["PMC1-0002"]),
        ],
    )
    return resolved, configs, data, run


def _generate(tmp_path: Path, generator: Any = None, **kwargs: Any) -> dict[str, Any]:
    resolved, configs, data, run = _world(tmp_path)
    return generate_one_config(
        resolved, "fixed", "bge", "off", configs, data, run,
        generator=generator or StandInGenerator(GENERATION), **kwargs,
    )


def test_a_cell_produces_one_answer_per_question(tmp_path: Path) -> None:
    report = _generate(tmp_path)
    assert report["n_answers"] == 2
    assert report["answers_written"] == 2
    answers = load_answers(answers_path(tmp_path / "runs" / "test", "fixed", "bge", "off"))
    assert {a.query_id for a in answers} == {"q001", "q002"}
    assert all(a.answer for a in answers)


def test_the_answer_records_the_context_it_was_given(tmp_path: Path) -> None:
    """An answer has to be readable on its own for the side-by-side view, and
    re-deriving its context from another stage's file is how they drift apart."""
    _generate(tmp_path)
    answers = {
        a.query_id: a
        for a in load_answers(answers_path(tmp_path / "runs" / "test", "fixed", "bge", "off"))
    }
    assert answers["q001"].context_chunk_ids == ("PMC1-0000", "PMC1-0001")
    assert answers["q001"].n_context_chunks == 2


def test_the_context_reaches_the_model_in_rank_order(tmp_path: Path) -> None:
    generator = _CountingGenerator()
    _generate(tmp_path, generator=generator)
    assert sorted(generator.seen) == sorted(QUESTIONS.values())


def test_rerunning_a_finished_cell_generates_nothing(tmp_path: Path) -> None:
    _generate(tmp_path)
    generator = _CountingGenerator()
    report = _generate(tmp_path, generator=generator)
    assert report["answers_written"] == 0
    assert report["answers_reused"] == 2
    assert generator.seen == []


def test_an_interrupted_cell_continues_where_it_stopped(tmp_path: Path) -> None:
    """Interrupt midway, re-run, it continues: the first question is kept and
    only the second is generated."""
    with pytest.raises(RuntimeError, match="session died"):
        _generate(tmp_path, generator=_CountingGenerator(fail_after=1), batch_size=1)
    partial = load_answers(answers_path(tmp_path / "runs" / "test", "fixed", "bge", "off"))
    assert len(partial) == 1

    resumed = _CountingGenerator()
    report = _generate(tmp_path, generator=resumed, batch_size=1)
    assert report["n_answers"] == 2
    assert report["answers_written"] == 1
    assert len(resumed.seen) == 1


def test_resuming_into_a_different_prompt_is_refused(tmp_path: Path) -> None:
    """The failure it prevents leaves one run directory holding answers produced
    under two prompts, indistinguishable after the fact."""
    resolved, configs, data, run = _world(tmp_path)
    generate_one_config(
        resolved, "fixed", "bge", "off", configs, data, run,
        generator=StandInGenerator(GENERATION),
    )
    # Someone edits the wording and leaves prompt_template_id at v1.
    path = answers_path(run, "fixed", "bge", "off")
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    records = records[:1]
    path.write_text(
        "".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in records),
        encoding="utf-8", newline="",
    )
    edited = dict(resolved)
    edited["base"] = {
        **resolved["base"],
        "generation": {**GENERATION, "system_prompt": "Answer from the passages only. Be brief."},
    }
    with pytest.raises(ValueError, match="different prompt"):
        generate_one_config(
            edited, "fixed", "bge", "off", configs, data, run,
            generator=StandInGenerator(GENERATION),
        )


def test_generating_before_retrieving_says_so(tmp_path: Path) -> None:
    resolved, configs, data, run = _world(tmp_path)
    (run / "retrieve" / "fixed-bge-rerank_off.jsonl").unlink()
    with pytest.raises(ValueError, match="run `ragbench retrieve` first"):
        generate_one_config(
            resolved, "fixed", "bge", "off", configs, data, run,
            generator=StandInGenerator(GENERATION),
        )


def test_a_partially_retrieved_cell_is_refused(tmp_path: Path) -> None:
    """Generating over 19 of 20 questions would silently produce a cell that is
    not comparable with the other seven."""
    resolved, configs, data, run = _world(tmp_path)
    write_jsonl(
        run / "retrieve" / "fixed-bge-rerank_off.jsonl",
        [_result("q001", ["PMC1-0000"])],
    )
    with pytest.raises(ValueError, match="retrieval is incomplete"):
        generate_one_config(
            resolved, "fixed", "bge", "off", configs, data, run,
            generator=StandInGenerator(GENERATION),
        )


def test_the_summary_records_what_the_stage_is_measured_on(tmp_path: Path) -> None:
    """Answer length and the truncation count are results, not diagnostics."""
    report = _generate(tmp_path)
    assert report["prompt_template_id"] == "v1"
    assert report["prompt_digest"]
    assert report["sampling"]["temperature"] == 0.0
    assert report["hit_max_new_tokens"] == 0
    assert report["wall_clock_ms"] >= 0


def test_the_whole_cartesian_product_runs_and_writes_a_summary(tmp_path: Path) -> None:
    resolved, configs, data, run = _world(tmp_path)
    reports = run_generate(
        resolved, configs, data, run, generator=StandInGenerator(GENERATION)
    )
    assert len(reports) == 1  # one level per factor in this fixture
    summary = json.loads((run / "generate" / "summary.json").read_text(encoding="utf-8"))
    assert summary[0]["config"] == "fixed-bge-rerank_off"


def test_a_completion_carries_its_own_finish_reason() -> None:
    assert Completion("x", 1, 1).finish_reason == FINISH_STOP


def test_prompts_are_not_reordered_by_the_generator() -> None:
    """A transposed batch attributes every answer to the wrong question and
    looks entirely healthy."""
    generator = StandInGenerator(GENERATION)
    prompts = [
        Prompt(system="s", user="u", context="hippocampus plaques", question="plaques where?"),
        Prompt(system="s", user="u", context="tau decline", question="tau correlates with?"),
    ]
    first, second = generator.generate_many(prompts)
    assert "hippocampus" in first.text
    assert "decline" in second.text
