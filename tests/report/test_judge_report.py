"""The judge report: what the means exclude, and whether the sheet is blind.

Two properties do the work. An abstention must never reach a mean -- scoring it
5 for faithfulness would reward a configuration for retrieving badly. And the
calibration sheet must not let the configuration be read back, by label or by
ordering, or the hand scores it collects are not blind.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pytest

from ragbench.gold.freeze import gold_set_sha, write_gold_set
from ragbench.jsonl import write_jsonl
from ragbench.judging.pipeline import judgements_path
from ragbench.report.calibration import item_id, read_scores, sample_items, write_sheet
from ragbench.report.judge import build_report
from ragbench.report.judge_render import render
from ragbench.types import GeneratedAnswer, GoldSpan, Judgement, Query

SCALES = ("faithfulness", "relevance", "completeness")
VERDICTS = ("correct", "partially_correct", "incorrect", "abstained")
JUDGE: dict[str, Any] = {
    "model_id": "meta-llama/llama-3.3-70b-instruct",
    "temperature": 0.0,
    "rubric_id": "v1",
    "system_prompt": "Grade it.",
    "prompt_template": "{question}{reference_answer}{context}{answer}{judge_note}",
    "judge_note_template": "{judge_note}",
    "scales": list(SCALES),
    "verdicts": list(VERDICTS),
    "passes": 2,
    "calibration_sample": 8,
    "calibration_seed": 3,
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


def _judgement(
    query_id: str, verdict: str, scores: dict[str, float] | None, pass_index: int = 0
) -> dict[str, Any]:
    return Judgement(
        query_id=query_id,
        scores=scores or {},
        rationale="because",
        judge_model="test",
        rubric_id="v1",
        verdict=verdict,
        pass_index=pass_index,
        answer_sha256="a" * 64,
    ).to_dict()


def _answer(query_id: str, text: str, tokens: int) -> dict[str, Any]:
    return GeneratedAnswer(
        query_id=query_id, answer=text, prompt_sha256="0" * 64, n_prompt_tokens=1000,
        n_completion_tokens=tokens, latency_ms=1.0, context_chunk_ids=("PMC1-0000",),
        n_context_chunks=1,
    ).to_dict()


def _world(
    tmp_path: Path, judgements: list[dict[str, Any]], answers: list[dict[str, Any]]
) -> tuple[dict[str, Any], Path, Path]:
    configs, run = tmp_path / "configs", tmp_path / "run"
    configs.mkdir(parents=True, exist_ok=True)
    queries = [_query("q001"), _query("q002"), _query("q003"), _query("q004")]
    write_gold_set(configs / "gold_set.jsonl", queries)
    resolved = {
        "base": {"judge": dict(JUDGE), "generation": {"context_separator": "\n\n"}},
        "gold": {"gold_set_sha": gold_set_sha(queries)},
        "corpus": {"manifest_sha": "deadbeef"},
        "factors": {
            "chunking": {"fixed": {}}, "embedding": {"bge": {}}, "rerank": {"off": {}},
        },
    }
    write_jsonl(judgements_path(run, "fixed", "bge", "off"), judgements)
    write_jsonl(run / "generate" / "fixed-bge-rerank_off.jsonl", answers)
    return resolved, configs, run


# ------------------------------------------------- abstentions are not scores


def test_an_abstention_is_excluded_from_the_means_not_scored_as_five(
    tmp_path: Path,
) -> None:
    """The whole reason the verdict exists beside the scales. Folding the
    abstention in as high faithfulness would reward the configuration that
    retrieved worst."""
    good = {"faithfulness": 4.0, "relevance": 4.0, "completeness": 4.0}
    judgements = []
    for index in (0, 1):
        judgements += [
            _judgement("q001", "correct", good, index),
            _judgement("q002", "correct", good, index),
            _judgement("q003", "abstained", None, index),
            _judgement("q004", "abstained", None, index),
        ]
    answers = [_answer(q, "x", 10) for q in ("q001", "q002", "q003", "q004")]
    report = build_report(*_world(tmp_path, judgements, answers))
    (config,) = report["configs"]

    assert config["scores"]["faithfulness"] == 4.0
    assert config["scores"]["faithfulness_n"] == 2
    assert config["n_scored"] == 2
    assert config["abstained"] == 2
    assert config["abstention_rate"] == 0.5


def test_the_denominator_is_visible_beside_every_mean(tmp_path: Path) -> None:
    """Two configurations with different abstention counts have means over
    different numbers of answers, and a table that hid that would invite
    comparing them as though they did not."""
    judgements = []
    for index in (0, 1):
        judgements += [
            _judgement("q001", "correct", {s: 5.0 for s in SCALES}, index),
            _judgement("q002", "abstained", None, index),
        ]
    report = build_report(
        *_world(tmp_path, judgements, [_answer("q001", "x", 5), _answer("q002", "y", 5)])
    )
    rendered = render(report)
    assert "means over JUDGED answers only" in rendered
    assert "abstentions carry no scores" in rendered


def test_answer_length_sits_in_the_same_table_as_the_scores(tmp_path: Path) -> None:
    """The judge literature reports a length bias; a separate section invites
    reading the scores without it."""
    judgements = [
        _judgement("q001", "correct", {s: 5.0 for s in SCALES}, i) for i in (0, 1)
    ]
    report = build_report(*_world(tmp_path, judgements, [_answer("q001", "x", 42)]))
    assert report["configs"][0]["completion_tokens"]["mean"] == 42.0
    header = [line for line in render(report).splitlines() if "faithfuln" in line][0]
    assert "tokens" in header


# ---------------------------------------------------------- self-consistency


def test_the_two_passes_are_compared_and_disagreement_shows(tmp_path: Path) -> None:
    judgements = [
        _judgement("q001", "correct", {s: 5.0 for s in SCALES}, 0),
        _judgement("q001", "partially_correct", {s: 2.0 for s in SCALES}, 1),
        _judgement("q002", "correct", {s: 4.0 for s in SCALES}, 0),
        _judgement("q002", "correct", {s: 4.0 for s in SCALES}, 1),
    ]
    report = build_report(
        *_world(tmp_path, judgements, [_answer("q001", "x", 5), _answer("q002", "y", 5)])
    )
    consistency = report["configs"][0]["self_consistency"]
    assert consistency["measured"] is True
    assert consistency["n_items"] == 2
    assert consistency["verdict"]["exact_agreement"] == 0.5
    assert consistency["faithfulness"]["exact_agreement"] == 0.5


def test_a_single_pass_reports_that_it_could_not_be_measured(tmp_path: Path) -> None:
    """Silence would read as perfect consistency, which is the opposite."""
    judgements = [_judgement("q001", "correct", {s: 5.0 for s in SCALES}, 0)]
    report = build_report(*_world(tmp_path, judgements, [_answer("q001", "x", 5)]))
    assert report["configs"][0]["self_consistency"]["measured"] is False


def test_the_report_says_self_consistency_bounds_everything_above_it(
    tmp_path: Path,
) -> None:
    judgements = [_judgement("q001", "correct", {s: 5.0 for s in SCALES}, i) for i in (0, 1)]
    report = build_report(*_world(tmp_path, judgements, [_answer("q001", "x", 5)]))
    assert "not evidence of anything" in render(report)


# -------------------------------------------------------- the sheet is blind


def _items(n_configs: int = 4, n_queries: int = 5) -> dict[str, dict[str, Any]]:
    return {
        f"config{c}": {f"q{q:03d}": object() for q in range(n_queries)}
        for c in range(n_configs)
    }


def test_the_sample_is_stratified_across_configurations() -> None:
    chosen = sample_items(_items(), size=8, seed=1)
    per_config: dict[str, int] = {}
    for config, _ in chosen:
        per_config[config] = per_config.get(config, 0) + 1
    assert len(chosen) == 8
    assert set(per_config.values()) == {2}


def test_the_sample_is_shuffled_so_the_order_does_not_reveal_the_configuration() -> None:
    """Five consecutive items from one configuration would reconstruct the label
    from the ordering alone. A sheet grouped by config is not blind, however
    carefully the header is omitted."""
    chosen = sample_items(_items(n_configs=4, n_queries=5), size=20, seed=1)
    configs = [config for config, _ in chosen]
    assert configs != sorted(configs)


def test_the_sample_is_deterministic_given_the_seed() -> None:
    """A re-run must not invalidate scoring already in progress."""
    assert sample_items(_items(), 8, 5) == sample_items(_items(), 8, 5)


def test_item_ids_carry_no_ordering() -> None:
    """A serial number that happens to run in config order is a label."""
    first = item_id("fixed-bge-rerank_off", "q001")
    second = item_id("fixed-bge-rerank_on", "q001")
    assert first != second
    assert first == item_id("fixed-bge-rerank_off", "q001")
    assert not first.isdigit()


def test_the_sheet_names_no_configuration_anywhere(tmp_path: Path) -> None:
    items = [
        {
            "item_id": item_id("recursive-specter2-rerank_on", "q001"),
            "config": "recursive-specter2-rerank_on",
            "query_id": "q001",
            "question": "where?",
            "reference_answer": "the hippocampus",
            "judge_note": "",
            "answer": "the hippocampus",
            "context": "plaques accumulate in the hippocampus",
        }
    ]
    written = write_sheet(tmp_path, items, SCALES, VERDICTS)
    sheet = written["sheet"].read_text(encoding="utf-8")
    for token in ("recursive", "specter2", "rerank_on", "fixed", "bge"):
        assert token not in sheet
    # The mapping exists, but in a file scoring does not need.
    assert "recursive-specter2-rerank_on" in written["key"].read_text(encoding="utf-8")


def test_the_sheet_carries_the_passages_because_faithfulness_needs_them(
    tmp_path: Path,
) -> None:
    items = [{
        "item_id": "abc", "config": "c", "query_id": "q001", "question": "where?",
        "reference_answer": "ref", "judge_note": "", "answer": "a",
        "context": "a very distinctive passage",
    }]
    written = write_sheet(tmp_path, items, SCALES, VERDICTS)
    assert "a very distinctive passage" in written["sheet"].read_text(encoding="utf-8")


def test_a_gold_note_reaches_the_sheet(tmp_path: Path) -> None:
    items = [{
        "item_id": "abc", "config": "c", "query_id": "q045", "question": "q",
        "reference_answer": "r", "judge_note": "the source sentence is malformed",
        "answer": "a", "context": "c",
    }]
    written = write_sheet(tmp_path, items, SCALES, VERDICTS)
    assert "the source sentence is malformed" in written["sheet"].read_text(encoding="utf-8")


# ------------------------------------------------------------- reading it back


def _fill(path: Path, rows: list[list[Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["item_id", *SCALES, "verdict", "notes"])
        writer.writerows(rows)


def test_blank_rows_are_skipped_rather_than_counted_as_disagreement(
    tmp_path: Path,
) -> None:
    path = tmp_path / "scores.csv"
    _fill(path, [["a", 5, 4, 3, "correct", ""], ["b", "", "", "", "", ""]])
    scored = read_scores(path, SCALES)
    assert set(scored) == {"a"}


def test_an_abstention_may_carry_a_verdict_with_no_scales(tmp_path: Path) -> None:
    path = tmp_path / "scores.csv"
    _fill(path, [["a", "", "", "", "abstained", ""]])
    scored = read_scores(path, SCALES)
    assert scored["a"]["verdict"] == "abstained"
    assert scored["a"]["faithfulness"] is None


def test_a_score_off_the_scale_is_an_error_with_the_line_number(tmp_path: Path) -> None:
    path = tmp_path / "scores.csv"
    _fill(path, [["a", 9, 4, 3, "correct", ""]])
    with pytest.raises(ValueError, match="outside the 1-5 scale"):
        read_scores(path, SCALES)


def test_a_non_numeric_score_is_an_error(tmp_path: Path) -> None:
    path = tmp_path / "scores.csv"
    _fill(path, [["a", "five", 4, 3, "correct", ""]])
    with pytest.raises(ValueError, match="not a number"):
        read_scores(path, SCALES)


def test_the_calibration_comparison_pairs_hand_scores_with_the_judge(
    tmp_path: Path,
) -> None:
    from ragbench.report.calibration_agreement import compare

    judgements = [
        _judgement("q001", "correct", {s: 5.0 for s in SCALES}, i) for i in (0, 1)
    ] + [_judgement("q002", "incorrect", {s: 2.0 for s in SCALES}, i) for i in (0, 1)]
    resolved, configs, run = _world(
        tmp_path, judgements, [_answer("q001", "x", 5), _answer("q002", "y", 5)]
    )
    key = {
        item_id("fixed-bge-rerank_off", "q001"): {
            "config": "fixed-bge-rerank_off", "query_id": "q001"},
        item_id("fixed-bge-rerank_off", "q002"): {
            "config": "fixed-bge-rerank_off", "query_id": "q002"},
    }
    (run / "calibration_key.json").write_text(json.dumps(key), encoding="utf-8")
    path = tmp_path / "scores.csv"
    _fill(path, [
        [item_id("fixed-bge-rerank_off", "q001"), 4, 4, 4, "correct", ""],
        [item_id("fixed-bge-rerank_off", "q002"), 2, 2, 2, "incorrect", ""],
    ])
    result = compare(resolved, run, path, SCALES, VERDICTS)
    assert result["n_paired"] == 2
    assert result["verdict"]["exact_agreement"] == 1.0
    # The judge scored q001 a point higher than the hand score did.
    assert result["scales"]["faithfulness"]["mean_difference"] == 0.5


def test_comparing_before_the_sheet_exists_says_so(tmp_path: Path) -> None:
    from ragbench.report.calibration_agreement import compare

    resolved, configs, run = _world(tmp_path, [], [])
    with pytest.raises(ValueError, match="no calibration key"):
        compare(resolved, run, tmp_path / "scores.csv", SCALES, VERDICTS)
