"""Reading a run's artefacts into one (configuration, question) -> metrics table.

Everything the analysis needs is already on disk; this only puts it in one
shape. Two rules govern what a missing value means, and they are not the same
rule:

* **A metric that was never produced is ``None``**, and the question drops out
  of that comparison with `n` reported. A judge run that is a quarter finished
  must not be silently averaged over whichever cells happen to exist.
* **An abstention is not a missing score for `correct`** -- it is a `correct`
  of 0, because declining to answer is not answering correctly. It *is* missing
  for faithfulness, relevance and completeness, which an abstention genuinely
  does not have (I8). The two are different facts and the table keeps them
  apart.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..gold.freeze import GOLD_SET_FILENAME, verify_frozen
from ..judging.base import ABSTAINED, judge_params, scales
from ..judging.pipeline import judgements_path, load_judgements
from ..report.retrieval import build_report as retrieval_report
from ..retrieval.pipeline import cells, config_name


@dataclass(frozen=True, slots=True)
class Metric:
    """What a metric is, so a test can be matched to its data type."""

    name: str
    label: str
    #: ``binary`` picks the exact sign test, ``continuous`` the signed-rank test.
    kind: str
    #: ``retrieval`` or ``generation`` -- which pre-specified primary it sits under.
    family: str
    #: Higher is better? Only affects how a direction is described, never a p-value.
    higher_is_better: bool = True


METRICS: tuple[Metric, ...] = (
    Metric("span_coverage", "span coverage", "continuous", "retrieval"),
    Metric("gold_found", "gold chunk retrieved", "binary", "retrieval"),
    Metric("ndcg_at_10", "nDCG@10", "continuous", "retrieval"),
    Metric("recall_at_10", "Recall@10", "continuous", "retrieval"),
    Metric("evidence_density", "evidence density", "continuous", "retrieval"),
    Metric("distractor_count", "distractors in window", "continuous", "retrieval", False),
    Metric("correct", "verdict == correct", "binary", "generation"),
    Metric("abstained", "abstention", "binary", "generation", False),
    Metric("faithfulness", "faithfulness (1-5)", "continuous", "generation"),
    Metric("relevance", "relevance (1-5)", "continuous", "generation"),
    Metric("completeness", "completeness (1-5)", "continuous", "generation"),
    Metric("answer_tokens", "answer length (tokens)", "continuous", "generation"),
)

BY_NAME: dict[str, Metric] = {metric.name: metric for metric in METRICS}

#: Copied out of the retrieval report's per-query rows unchanged.
RETRIEVAL_FIELDS: tuple[str, ...] = (
    "span_coverage",
    "ndcg_at_10",
    "recall_at_10",
    "evidence_density",
    "distractor_count",
)


def _judge_rows(
    run_directory: Path, chunking: str, embedding: str, rerank: str, names: Sequence[str]
) -> dict[str, dict[str, float | None]]:
    """One row per question: first-pass verdict, scales averaged over passes."""
    records = load_judgements(judgements_path(run_directory, chunking, embedding, rerank))
    by_query: dict[str, list[Any]] = {}
    for record in records:
        by_query.setdefault(record.query_id, []).append(record)

    rows: dict[str, dict[str, float | None]] = {}
    for query_id, found in by_query.items():
        first = min(found, key=lambda record: record.pass_index)
        row: dict[str, float | None] = {
            "correct": 1.0 if first.verdict == "correct" else 0.0,
            "abstained": 1.0 if first.verdict == ABSTAINED else 0.0,
        }
        for name in names:
            values = [
                float(record.scores[name]) for record in found if name in record.scores
            ]
            # Averaged over passes: repeated measures of the same judgement, so
            # the mean halves the judge's own noise. Absent for an abstention,
            # which carries no scores at all.
            row[name] = sum(values) / len(values) if values else None
        rows[query_id] = row
    return rows


def build_table(
    resolved: dict[str, Any],
    configs_dir: Path,
    data_root: Path,
    run_directory: Path,
) -> tuple[dict[tuple[str, str], dict[str, float | None]], list[str], dict[str, Any]]:
    """The table, the question ids, and what is missing from it."""
    queries = verify_frozen(
        Path(configs_dir) / GOLD_SET_FILENAME, str(resolved["gold"].get("gold_set_sha", ""))
    )
    query_ids = [query.query_id for query in queries]
    names = scales(judge_params(resolved))

    retrieval = retrieval_report(resolved, configs_dir, data_root, run_directory)
    per_config = {config["config"]: config for config in retrieval["configs"]}

    table: dict[tuple[str, str], dict[str, float | None]] = {}
    availability: list[dict[str, Any]] = []
    from ..generation.pipeline import answers_path, load_answers

    for chunking, embedding, rerank in cells(resolved):
        name = config_name(chunking, embedding, rerank)
        rows = {
            row["query_id"]: row
            for row in per_config.get(name, {}).get("per_query", [])
        }
        judged = _judge_rows(run_directory, chunking, embedding, rerank, names)
        lengths = {
            record.query_id: float(record.n_completion_tokens)
            for record in load_answers(answers_path(run_directory, chunking, embedding, rerank))
        }

        for query_id in query_ids:
            entry: dict[str, float | None] = {}
            row = rows.get(query_id)
            if row is not None:
                for field in RETRIEVAL_FIELDS:
                    entry[field] = None if row.get(field) is None else float(row[field])
                entry["gold_found"] = 0.0 if row.get("gold_rank") is None else 1.0
            entry["answer_tokens"] = lengths.get(query_id)
            entry.update(judged.get(query_id, {}))
            table[(name, query_id)] = entry

        availability.append(
            {
                "config": name,
                "n_retrieved": len(rows),
                "n_judged": len(judged),
                "n_answers": len(lengths),
                "n_questions": len(query_ids),
            }
        )

    summary = {
        "n_questions": len(query_ids),
        "n_configs": len(availability),
        "per_config": availability,
        "judged_configs": [row["config"] for row in availability if row["n_judged"]],
        "unjudged_configs": [row["config"] for row in availability if not row["n_judged"]],
        "n_judgements": sum(row["n_judged"] for row in availability),
        "n_judgements_expected": len(availability) * len(query_ids),
    }
    return table, query_ids, summary


def prespecification(configs_dir: Path) -> dict[str, Any]:
    """The analysis plan, loaded from its own file. See `configs/stats.yaml`."""
    import yaml

    path = Path(configs_dir) / "stats.yaml"
    if not path.is_file():
        raise ValueError(f"no analysis pre-specification at {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "stats" not in data:
        raise ValueError(f"{path}: expected a top-level 'stats:' mapping")
    return dict(data["stats"])


def primary_metrics(plan: Mapping[str, Any]) -> dict[str, str]:
    """``{family: metric}`` -- exactly one per family, pre-specified."""
    primary = dict(plan.get("primary") or {})
    for family, metric in primary.items():
        if metric not in BY_NAME:
            raise ValueError(f"primary metric {metric!r} for {family!r} is not a known metric")
    return {str(family): str(metric) for family, metric in primary.items()}
