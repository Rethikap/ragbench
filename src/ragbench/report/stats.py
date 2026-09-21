"""The analysis: main effects, interactions, and what could not be computed yet.

Assembles the comparisons and applies the pre-specified correction. Nothing here
decides which metric is primary -- that is read from `configs/stats.yaml`, which
was committed before the judge results existed, because a correction applied to
a family chosen after seeing the results corrects nothing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..hashing import canonical_json, sha256_text
from ..stats.design import factor_levels, interaction, main_effect
from ..stats.pipeline import BY_NAME, METRICS, build_table, prespecification, primary_metrics
from ..stats.tests import (
    TestResult,
    bootstrap_ci,
    holm,
    sign_test,
    wilcoxon_signed_rank,
)


def run_test(differences: Any, metric_name: str, plan: dict[str, Any]) -> TestResult:
    """Match the test to the data type, then report everything about it."""
    metric = BY_NAME[metric_name]
    values = differences.values
    mean, low, high = bootstrap_ci(
        values,
        resamples=int(plan.get("bootstrap_resamples", 10000)),
        seed=int(plan.get("bootstrap_seed", 0)),
        confidence=float(plan.get("confidence", 0.95)),
    )
    if metric.kind == "binary":
        p_value, effect, ties = sign_test(values)
        test = "exact sign test (McNemar's exact test, generalised over the averaged cells)"
    else:
        p_value, effect = wilcoxon_signed_rank(values)
        ties = sum(1 for value in values if value == 0.0)
        test = "exact Wilcoxon signed-rank"
    return TestResult(
        name=f"{differences.factor}:{metric_name}",
        n=len(values),
        mean_difference=mean,
        ci_low=low,
        ci_high=high,
        p_value=p_value,
        effect_size=effect,
        test=test,
        n_ties=ties,
        note="" if differences.complete else "incomplete: some cells have no data yet",
    )


def _comparison(
    resolved: dict[str, Any],
    table: Any,
    query_ids: list[str],
    factor: str,
    metric_name: str,
    plan: dict[str, Any],
) -> dict[str, Any]:
    differences = main_effect(resolved, table, factor, metric_name, query_ids)
    return {
        **differences.to_dict(),
        **run_test(differences, metric_name, plan).to_dict(),
        "metric_label": BY_NAME[metric_name].label,
        "higher_is_better": BY_NAME[metric_name].higher_is_better,
        "differences": differences.pairs,
    }


def build_report(
    resolved: dict[str, Any],
    configs_dir: Path,
    data_root: Path,
    run_directory: Path,
    calibration: Path | None = None,
) -> dict[str, Any]:
    """Every comparison the run can currently support, and the ones it cannot."""
    plan = prespecification(configs_dir)
    table, query_ids, availability = build_table(
        resolved, configs_dir, data_root, run_directory
    )
    primary = primary_metrics(plan)
    questions = dict(plan.get("research_questions") or {})

    primaries: list[dict[str, Any]] = []
    for research_question, factor in sorted(questions.items()):
        for family, metric_name in sorted(primary.items()):
            row = _comparison(resolved, table, query_ids, factor, metric_name, plan)
            row["research_question"] = research_question
            row["family"] = family
            row["primary"] = True
            primaries.append(row)

    corrected = holm(
        {row["name"]: row["p_value"] for row in primaries},
        alpha=float(plan.get("alpha", 0.05)),
    )
    for row in primaries:
        row.update(corrected.get(row["name"], {}))

    exploratory: list[dict[str, Any]] = []
    for metric_name in plan.get("exploratory") or []:
        if metric_name not in BY_NAME:
            continue
        for _, factor in sorted(questions.items()):
            row = _comparison(resolved, table, query_ids, factor, str(metric_name), plan)
            row["primary"] = False
            exploratory.append(row)

    interactions: list[dict[str, Any]] = []
    for pair in plan.get("interactions") or []:
        first, second = str(pair[0]), str(pair[1])
        for family, metric_name in sorted(primary.items()):
            differences = interaction(
                resolved, table, first, second, metric_name, query_ids
            )
            interactions.append(
                {
                    **differences.to_dict(),
                    **run_test(differences, metric_name, plan).to_dict(),
                    "metric_label": BY_NAME[metric_name].label,
                    "family": family,
                    "exploratory": True,
                }
            )

    return {
        "gold_set_sha": str(resolved["gold"].get("gold_set_sha", "")),
        "prespecification": plan,
        "prespecification_digest": sha256_text(canonical_json(plan))[:12],
        "factor_levels": {
            factor: list(factor_levels(resolved, factor)) for factor in sorted(questions.values())
        },
        "availability": availability,
        "primaries": primaries,
        "exploratory": exploratory,
        "interactions": interactions,
        "metrics": [
            {"name": m.name, "label": m.label, "kind": m.kind, "family": m.family}
            for m in METRICS
        ],
        "calibration": _calibration(resolved, run_directory, calibration, plan),
    }


def _calibration(
    resolved: dict[str, Any],
    run_directory: Path,
    scores_path: Path | None,
    plan: dict[str, Any],
) -> dict[str, Any] | None:
    """RQ4: the judge against the human, on the blind sample.

    Returns ``None`` rather than zeros when the sheet has not been filled in --
    an agreement of nothing is not an agreement of zero.
    """
    if scores_path is None:
        return None
    from ..judging.base import judge_params, scales, verdicts
    from .calibration_agreement import compare

    params = judge_params(resolved)
    del plan
    return compare(resolved, run_directory, scores_path, scales(params), verdicts(params))
