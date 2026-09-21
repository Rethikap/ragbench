"""The factorial construction: 20 paired differences, not 80 observations.

The arithmetic here is checkable by hand, so the tests construct data whose
effect is known by design and assert the construction recovers exactly that.
"""

from __future__ import annotations

import numpy as np
import pytest

from ragbench.stats.design import cell_name, factor_levels, interaction, main_effect
from ragbench.stats.tests import bootstrap_ci

RESOLVED = {
    "factors": {
        "chunking": {"fixed": {}, "recursive": {}},
        "embedding": {"bge": {}, "specter2": {}},
        "rerank": {"off": {}, "on": {}},
    }
}
QUESTIONS = [f"q{index:03d}" for index in range(20)]


def _table(effect: float = 0.0, noise: float = 0.0, seed: int = 0, metric: str = "m"):
    """Every cell, with a known effect of `effect` for recursive over fixed."""
    rng = np.random.default_rng(seed)
    table: dict[tuple[str, str], dict[str, float | None]] = {}
    for query_id in QUESTIONS:
        # A per-question level, which is exactly the dependence that makes the
        # 8 configurations 8 measurements of one thing rather than 8 samples.
        base = float(rng.normal(0.5, 0.3))
        for chunking in ("fixed", "recursive"):
            for embedding in ("bge", "specter2"):
                for rerank in ("off", "on"):
                    name = cell_name(
                        {"chunking": chunking, "embedding": embedding, "rerank": rerank}
                    )
                    value = base + (effect if chunking == "recursive" else 0.0)
                    if noise:
                        value += float(rng.normal(0.0, noise))
                    table[(name, query_id)] = {metric: value}
    return table


# ------------------------------------------------------------ known effects


def test_a_constructed_effect_is_recovered_exactly() -> None:
    """No noise, so every one of the 20 differences must be the effect itself."""
    differences = main_effect(RESOLVED, _table(effect=0.25), "chunking", "m", QUESTIONS)
    assert len(differences.pairs) == 20
    assert differences.label == "recursive - fixed"
    assert all(value == pytest.approx(0.25) for value in differences.values)


def test_the_sign_follows_the_order_in_factors_yaml() -> None:
    """The label says which way round the subtraction went, and the label is
    generated from the same order the arithmetic used."""
    assert factor_levels(RESOLVED, "chunking") == ("fixed", "recursive")
    differences = main_effect(RESOLVED, _table(effect=-0.1), "chunking", "m", QUESTIONS)
    assert differences.label == "recursive - fixed"
    assert all(value == pytest.approx(-0.1) for value in differences.values)


def test_one_difference_per_question_averaged_over_the_other_two_factors() -> None:
    differences = main_effect(RESOLVED, _table(effect=0.25), "chunking", "m", QUESTIONS)
    assert differences.n_cells == 4
    assert len(differences.values) == len(QUESTIONS)
    assert sorted(differences.query_ids) == sorted(QUESTIONS)


# ----------------------------------------- why the 4 pairs are not 80 rows


def _heterogeneous(seed: int = 5):
    """Cells whose effect VARIES BY QUESTION -- the realistic case.

    An effect that helped every question identically would make pooling
    harmless; what makes it misleading is the per-question component, which is
    the same in all four of a question's pairs and so gets counted four times.
    """
    rng = np.random.default_rng(seed)
    table: dict[tuple[str, str], dict[str, float | None]] = {}
    for query_id in QUESTIONS:
        base = float(rng.normal(0.5, 0.3))
        # This question's own effect: shared by all four of its pairs.
        effect_here = 0.25 + float(rng.normal(0.0, 0.20))
        for chunking in ("fixed", "recursive"):
            for embedding in ("bge", "specter2"):
                for rerank in ("off", "on"):
                    value = base + float(rng.normal(0.0, 0.02))
                    if chunking == "recursive":
                        value += effect_here
                    table[
                        (cell_name({"chunking": chunking, "embedding": embedding,
                                    "rerank": rerank}), query_id)
                    ] = {"m": value}
    return table


def test_pooling_the_four_pairs_would_halve_the_interval() -> None:
    """The mistake this module exists to prevent, measured.

    Pooling gives 80 rows that are four measurements of each of 20 questions.
    The per-question part of the effect is identical across a question's four
    pairs, so counting them separately counts it four times and the interval
    comes out about half the width it has earned.
    """
    table = _heterogeneous()
    correct = main_effect(RESOLVED, table, "chunking", "m", QUESTIONS)

    pooled: list[float] = []
    for query_id in QUESTIONS:
        for embedding in ("bge", "specter2"):
            for rerank in ("off", "on"):
                low = table[
                    (cell_name({"chunking": "fixed", "embedding": embedding,
                                "rerank": rerank}), query_id)
                ]["m"]
                high = table[
                    (cell_name({"chunking": "recursive", "embedding": embedding,
                                "rerank": rerank}), query_id)
                ]["m"]
                pooled.append(high - low)

    assert len(correct.values) == 20
    assert len(pooled) == 80
    _, low_correct, high_correct = bootstrap_ci(correct.values, resamples=4000, seed=1)
    _, low_pooled, high_pooled = bootstrap_ci(pooled, resamples=4000, seed=1)
    width_correct = high_correct - low_correct
    width_pooled = high_pooled - low_pooled
    # Both centre on the same effect; only the claimed precision differs.
    assert np.mean(correct.values) == pytest.approx(float(np.mean(pooled)), abs=1e-9)
    assert width_pooled < width_correct * 0.65


# ------------------------------------------------------- partial data


def test_a_question_missing_any_cell_is_dropped_and_the_cell_is_named() -> None:
    """Averaging over four cells for one question and one cell for another
    would be two estimators wearing one name."""
    table = _table(effect=0.25)
    missing = cell_name({"chunking": "recursive", "embedding": "specter2", "rerank": "on"})
    for query_id in QUESTIONS[:5]:
        table[(missing, query_id)] = {"m": None}

    differences = main_effect(RESOLVED, table, "chunking", "m", QUESTIONS)
    assert len(differences.pairs) == 15
    assert not differences.complete
    assert missing in differences.missing
    assert differences.to_dict()["n_questions_dropped"] == 5


def test_a_wholly_unjudged_configuration_yields_no_comparison_at_all() -> None:
    """What `report stats` shows today: the retrieval comparisons run, and the
    generation ones report n=0 rather than an average over two of eight cells."""
    table = _table(effect=0.25)
    for (name, query_id) in list(table):
        if name.startswith("recursive"):
            table[(name, query_id)] = {"m": None}
    differences = main_effect(RESOLVED, table, "chunking", "m", QUESTIONS)
    assert differences.pairs == []
    assert len(differences.missing) == 4


def test_a_metric_absent_for_one_cell_does_not_hide_a_different_metric() -> None:
    """An abstention has no faithfulness but does have a `correct` of 0."""
    table = _table(effect=0.2, metric="correct")
    for (_name, query_id), row in table.items():
        row["faithfulness"] = None if query_id == QUESTIONS[0] else 4.0
    correct = main_effect(RESOLVED, table, "chunking", "correct", QUESTIONS)
    faithfulness = main_effect(RESOLVED, table, "chunking", "faithfulness", QUESTIONS)
    assert len(correct.pairs) == 20
    assert len(faithfulness.pairs) == 19


# -------------------------------------------------------------- interactions


def test_no_interaction_when_the_effect_is_additive() -> None:
    """Built additive, so the contrast must be exactly zero."""
    contrast = interaction(RESOLVED, _table(effect=0.25), "chunking", "rerank", "m", QUESTIONS)
    assert all(value == pytest.approx(0.0) for value in contrast.values)


def test_a_constructed_interaction_is_recovered() -> None:
    """recursive gains 0.4 when rerank is on and 0.1 when it is off, so the
    contrast is 0.3 on every question."""
    table: dict[tuple[str, str], dict[str, float | None]] = {}
    rng = np.random.default_rng(2)
    for query_id in QUESTIONS:
        base = float(rng.normal(0.5, 0.3))
        for chunking in ("fixed", "recursive"):
            for embedding in ("bge", "specter2"):
                for rerank in ("off", "on"):
                    bonus = 0.0
                    if chunking == "recursive":
                        bonus = 0.4 if rerank == "on" else 0.1
                    table[
                        (cell_name({"chunking": chunking, "embedding": embedding,
                                    "rerank": rerank}), query_id)
                    ] = {"m": base + bonus}
    contrast = interaction(RESOLVED, table, "chunking", "rerank", "m", QUESTIONS)
    assert all(value == pytest.approx(0.3) for value in contrast.values)
    assert "chunking" in contrast.factor and "rerank" in contrast.factor


def test_an_unknown_factor_is_an_error_not_an_empty_result() -> None:
    with pytest.raises(ValueError, match="unknown factor"):
        main_effect(RESOLVED, {}, "temperature", "m", QUESTIONS)
