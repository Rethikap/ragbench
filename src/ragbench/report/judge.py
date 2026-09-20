"""Aggregating the judgements: scores, verdicts, abstention, and self-consistency.

Three decisions here are worth stating because they change what the numbers mean.

**Means are taken over judged answers only.** An abstention carries no scores, so
a configuration that abstained four times has its means over sixteen. The
denominator is reported beside every mean, and the abstention rate is its own
column -- folding abstentions in as high faithfulness would reward a
configuration for retrieving badly, and folding them in as low completeness
would punish the generator for the retriever's failure.

**The scale scores are the mean of the two passes; the verdict is the first
pass.** Averaging repeated measures is standard and halves the judge's own
noise. A verdict is categorical and has no mean, so the first pass stands and
the disagreement between passes is reported next to it.

**Answer length sits in the same table as the scores.** The judge literature
reports a length bias; putting length in a separate section invites reading the
scores without it. Here they cannot be read apart.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..eval.agreement import agreement_summary
from ..generation.pipeline import answers_path, load_answers
from ..gold.freeze import GOLD_SET_FILENAME, verify_frozen
from ..judging.base import ABSTAINED, UNPARSED, judge_params, scales, verdicts
from ..judging.pipeline import judgements_path, load_judgements
from ..judging.prompt import rubric_digest
from ..retrieval.pipeline import cells, config_name
from ..types import GeneratedAnswer, Judgement
from .chunks import distribution


def _by_pass(records: list[Judgement]) -> dict[int, dict[str, Judgement]]:
    out: dict[int, dict[str, Judgement]] = {}
    for record in records:
        out.setdefault(record.pass_index, {})[record.query_id] = record
    return out


def _mean_over_passes(
    passes: dict[int, dict[str, Judgement]], query_id: str, scale: str
) -> float | None:
    values = [
        float(byq[query_id].scores[scale])
        for byq in passes.values()
        if query_id in byq and scale in byq[query_id].scores
    ]
    return sum(values) / len(values) if values else None


def _summarise(
    records: list[Judgement],
    answers: dict[str, GeneratedAnswer],
    names: tuple[str, ...],
    permitted: tuple[str, ...],
) -> dict[str, Any]:
    if not records:
        return {"n_judgements": 0, "n_answers": len(answers)}
    passes = _by_pass(records)
    first = passes.get(min(passes), {})
    query_ids = sorted({record.query_id for record in records})

    means: dict[str, Any] = {}
    for scale in names:
        values = [
            value
            for query_id in query_ids
            if (value := _mean_over_passes(passes, query_id, scale)) is not None
        ]
        means[scale] = round(sum(values) / len(values), 3) if values else None
        means[f"{scale}_n"] = len(values)

    counts = {name: 0 for name in permitted}
    counts[UNPARSED] = 0
    for query_id in query_ids:
        record = first.get(query_id)
        if record is not None:
            counts[record.verdict] = counts.get(record.verdict, 0) + 1

    n_answers = len(query_ids)
    abstained = counts.get(ABSTAINED, 0)
    lengths = [answers[q].n_completion_tokens for q in query_ids if q in answers]
    return {
        "n_judgements": len(records),
        "n_answers": n_answers,
        "n_passes": len(passes),
        "scores": means,
        "verdicts": counts,
        "n_scored": n_answers - abstained - counts.get(UNPARSED, 0),
        "abstained": abstained,
        "abstention_rate": round(abstained / n_answers, 4) if n_answers else 0.0,
        "correct_rate": round(counts.get("correct", 0) / n_answers, 4) if n_answers else 0.0,
        "unparsed": counts.get(UNPARSED, 0),
        "completion_tokens": distribution(lengths) if lengths else {"n": 0},
        "self_consistency": _self_consistency(passes, names, permitted),
        "abstained_by_match": sum(1 for r in records if r.from_refusal_match),
    }


def _self_consistency(
    passes: dict[int, dict[str, Judgement]],
    names: tuple[str, ...],
    permitted: tuple[str, ...],
) -> dict[str, Any]:
    """The judge against itself, at temperature 0.

    Whatever this number is, it bounds how much any difference *between*
    configurations can be trusted: a gap smaller than the judge's disagreement
    with itself is not evidence of anything.
    """
    if len(passes) < 2:
        return {"n_passes": len(passes), "measured": False}
    indices = sorted(passes)
    left, right = passes[indices[0]], passes[indices[1]]
    shared = sorted(set(left) & set(right))
    out: dict[str, Any] = {"n_passes": len(passes), "measured": True, "n_items": len(shared)}
    for scale in names:
        out[scale] = agreement_summary(
            [left[q].scores.get(scale) for q in shared],
            [right[q].scores.get(scale) for q in shared],
            categories=[1.0, 2.0, 3.0, 4.0, 5.0],
        )
    order = {name: float(position) for position, name in enumerate(permitted)}
    out["verdict"] = agreement_summary(
        [order.get(left[q].verdict) for q in shared],
        [order.get(right[q].verdict) for q in shared],
        categories=[float(i) for i in range(len(permitted))],
        ordinal=False,
    )
    return out


def build_report(
    resolved: dict[str, Any], configs_dir: Path, run_directory: Path
) -> dict[str, Any]:
    """Per-configuration scores, verdicts, abstention and self-consistency."""
    params = judge_params(resolved)
    names = scales(params)
    permitted = verdicts(params)
    queries = verify_frozen(
        Path(configs_dir) / GOLD_SET_FILENAME, str(resolved["gold"].get("gold_set_sha", ""))
    )

    configs: list[dict[str, Any]] = []
    for chunking, embedding, rerank in cells(resolved):
        name = config_name(chunking, embedding, rerank)
        answers = {
            record.query_id: record
            for record in load_answers(answers_path(run_directory, chunking, embedding, rerank))
        }
        records = load_judgements(
            judgements_path(run_directory, chunking, embedding, rerank)
        )
        configs.append(
            {
                "config": name,
                "chunking_level": chunking,
                "embedding_level": embedding,
                "rerank_level": rerank,
                **_summarise(records, answers, names, permitted),
            }
        )

    judged = [config for config in configs if config["n_judgements"]]
    return {
        "gold_set_sha": str(resolved["gold"].get("gold_set_sha", "")),
        "judge_model": str(params.get("model_id", "")),
        "judge_temperature": params.get("temperature"),
        "rubric_id": str(params.get("rubric_id") or ""),
        "rubric_digest": rubric_digest(params),
        "scales": list(names),
        "verdicts": list(permitted),
        "passes": int(params.get("passes", 1)),
        "n_questions": len(queries),
        "n_configs": len(configs),
        "n_configs_judged": len(judged),
        "n_judgements": sum(config["n_judgements"] for config in configs),
        "n_expected": len(configs) * len(queries) * int(params.get("passes", 1)),
        "configs": configs,
    }
