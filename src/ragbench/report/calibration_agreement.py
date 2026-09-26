"""Judge against human, on the blind sample only.

Separated from :mod:`ragbench.report.calibration`, which makes the sheet: one
module produces the items to score, one compares the scores that come back. The
split matters more than usual here, because the comparison is the only thing
that may read the key file, and keeping it in its own module makes that visible.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..eval.agreement import agreement_summary
from .calibration import KEY_FILENAME, read_scores


def _judge_view(
    resolved: dict[str, Any], run_directory: Path, scales: tuple[str, ...]
) -> dict[tuple[str, str], dict[str, Any]]:
    """The judge's own scores, keyed by (config, query): means over passes, first-pass verdict."""
    from ..judging.pipeline import judgements_path, load_judgements
    from ..retrieval.pipeline import cells, config_name

    out: dict[tuple[str, str], dict[str, Any]] = {}
    for chunking, embedding, rerank in cells(resolved):
        config = config_name(chunking, embedding, rerank)
        by_pass: dict[str, list[Any]] = {}
        first: dict[str, Any] = {}
        for record in load_judgements(judgements_path(run_directory, chunking, embedding, rerank)):
            by_pass.setdefault(record.query_id, []).append(record)
            if record.pass_index == 0:
                first[record.query_id] = record
        for query_id, records in by_pass.items():
            entry: dict[str, Any] = {
                "verdict": first.get(query_id, records[0]).verdict,
            }
            for name in scales:
                values = [float(r.scores[name]) for r in records if name in r.scores]
                entry[name] = sum(values) / len(values) if values else None
            out[(config, query_id)] = entry
    return out


def compare(
    resolved: dict[str, Any],
    run_directory: Path,
    scores_path: Path,
    scales: tuple[str, ...],
    verdicts: tuple[str, ...],
) -> dict[str, Any]:
    """Weighted kappa and Spearman between the hand scores and the judge.

    Percentage agreement is reported too, but never alone: on a five-point scale
    where most answers are good, two raters who never read anything would agree
    a third of the time. Kappa subtracts what the marginals predict.

    The mean difference is reported beside both, because it separates the two
    ways a judge can disagree. A judge a full point harsher than the human ranks
    the answers identically -- high Spearman, poor kappa -- and that is a
    calibration offset with a different remedy from genuine disagreement.
    """
    key_path = Path(run_directory) / KEY_FILENAME
    if not key_path.is_file():
        raise ValueError(
            f"no calibration key at {key_path}; run `ragbench report judge` once to emit "
            "the sheet before scoring against it"
        )
    key = json.loads(key_path.read_text(encoding="utf-8"))
    human = read_scores(Path(scores_path), scales, verdicts)
    judge = _judge_view(resolved, Path(run_directory), scales)

    paired: list[dict[str, Any]] = []
    missing: list[str] = []
    for identifier, scored in sorted(human.items()):
        entry = key.get(identifier)
        if entry is None:
            missing.append(identifier)
            continue
        found = judge.get((entry["config"], entry["query_id"]))
        if found is None:
            missing.append(identifier)
            continue
        paired.append({"item_id": identifier, "human": scored, "judge": found, **entry})

    order = {name: float(position) for position, name in enumerate(verdicts)}
    result: dict[str, Any] = {
        "n_sheet_items": len(key),
        "n_scored_by_hand": len(human),
        "n_paired": len(paired),
        "unmatched_item_ids": missing,
        "scales": {},
    }
    for name in scales:
        left = [row["human"].get(name) for row in paired]
        right = [row["judge"].get(name) for row in paired]
        summary = agreement_summary(left, right, categories=[1.0, 2.0, 3.0, 4.0, 5.0])
        both = [(a, b) for a, b in zip(left, right, strict=True) if a is not None and b is not None]
        summary["mean_human"] = round(sum(a for a, _ in both) / len(both), 3) if both else None
        summary["mean_judge"] = round(sum(b for _, b in both) / len(both), 3) if both else None
        summary["mean_difference"] = (
            round(summary["mean_judge"] - summary["mean_human"], 3) if both else None
        )
        # A judge score is the mean of its two passes, so a scale the passes
        # disagreed on lands on a half-point -- 4.5 against a human's 4 or 5.
        # Weighted kappa and Spearman handle that correctly, treating it as the
        # near miss it is. EXACT agreement cannot: those rows can never match,
        # so the count travels with the figure it depresses.
        summary["judge_pass_means"] = sum(
            1 for _, value in both if value is not None and value != int(value)
        )
        result["scales"][name] = summary

    result["verdict"] = agreement_summary(
        [order.get(row["human"].get("verdict", "")) for row in paired],
        [order.get(row["judge"].get("verdict", "")) for row in paired],
        categories=[float(i) for i in range(len(verdicts))],
        ordinal=False,
    )
    # Only now is the hidden label used, and only in aggregate: a per-item
    # listing here would let a second pass of hand-scoring see the answer.
    per_config: dict[str, int] = {}
    for row in paired:
        per_config[row["config"]] = per_config.get(row["config"], 0) + 1
    result["items_per_config"] = dict(sorted(per_config.items()))
    return result
