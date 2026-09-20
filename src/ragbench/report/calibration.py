"""The blind calibration sample, and the agreement it is scored against.

An LLM judge's scores are worth what its agreement with a human is worth, and
that number has to be produced before the results are read, not after they are
argued about. So this emits a sample to hand-score and then computes agreement
against the judge on exactly those items.

**Blind, and blind in two ways.** The configuration label is not in the sheet,
so an item cannot be scored more generously for coming from the arm the reader
expects to win. And the items are *shuffled* after stratified sampling, because
five consecutive items from one configuration would reconstruct the label from
the ordering alone -- a sheet grouped by config is not blind, however carefully
the header is omitted.

Item ids are content-addressed via :mod:`ragbench.hashing`, not sequential, for
the same reason: a serial number that happens to run in config order is a label.
The mapping back lives in a separate key file, which is not needed to score and
should not be opened while scoring.
"""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path
from typing import Any

from ..hashing import stable_hash

SHEET_FILENAME = "calibration_sheet.md"
SCORES_FILENAME = "calibration_scores.csv"
KEY_FILENAME = "calibration_key.json"
COLUMNS = ("item_id", "faithfulness", "relevance", "completeness", "verdict", "notes")


def item_id(config: str, query_id: str) -> str:
    """Opaque, stable, and carrying no ordering. See the module docstring."""
    return stable_hash({"kind": "calibration_item", "config": config, "query_id": query_id}, 8)


def sample_items(
    per_config: dict[str, dict[str, Any]], size: int, seed: int
) -> list[tuple[str, str]]:
    """Stratify across configurations, then shuffle. Deterministic given the seed."""
    configs = sorted(per_config)
    if not configs:
        return []
    chosen: list[tuple[str, str]] = []
    rng = random.Random(seed)
    # Ceiling division, so a sample that does not divide by 8 over-draws rather
    # than silently dropping a configuration entirely.
    each = max(1, -(-size // len(configs)))
    for config in configs:
        query_ids = sorted(per_config[config])
        chosen.extend((config, q) for q in rng.sample(query_ids, min(each, len(query_ids))))
    rng.shuffle(chosen)
    return chosen[:size]


def write_sheet(
    directory: Path,
    items: list[dict[str, Any]],
    scales: tuple[str, ...],
    verdicts: tuple[str, ...],
) -> dict[str, Path]:
    """Three files: the sheet to read, the CSV to fill, and the key not to open."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [
        "# Blind calibration sheet",
        "",
        f"{len(items)} answers sampled across all configurations. The configuration is not",
        "shown, and the items are shuffled so the order does not reveal it.",
        "",
        f"Score each item in `{SCORES_FILENAME}` on three 1-5 scales and one verdict:",
        "",
        "- **faithfulness** -- is every claim supported by the RETRIEVED PASSAGES? A value",
        "  that appears in the passages but is attached to the wrong entity is not faithful.",
        "- **relevance** -- does it answer the question that was asked?",
        "- **completeness** -- does it cover what the reference answer covers?",
        f"- **verdict** -- one of: {', '.join(verdicts)}.",
        "",
        "Leave all four blank for an item you would rather not score; blank rows are",
        "skipped rather than counted as disagreement. For an abstention, set the verdict",
        "and leave the three scales blank.",
        "",
        "---",
        "",
    ]
    for position, item in enumerate(items, start=1):
        lines.append(f"## {position}. `{item['item_id']}`")
        lines.append("")
        lines.append(f"**Question.** {item['question']}")
        lines.append("")
        lines.append(f"**Reference answer.** {item['reference_answer']}")
        lines.append("")
        if item.get("judge_note"):
            lines.append(f"**Note from the gold set.** {item['judge_note']}")
            lines.append("")
        lines.append("**Answer under review.**")
        lines.append("")
        lines.append("> " + "\n> ".join(item["answer"].splitlines() or [""]))
        lines.append("")
        lines.append("<details><summary>Retrieved passages (what the system was shown)</summary>")
        lines.append("")
        lines.append("```")
        lines.append(item["context"])
        lines.append("```")
        lines.append("")
        lines.append("</details>")
        lines.append("")
    sheet = directory / SHEET_FILENAME
    sheet.write_text("\n".join(lines), encoding="utf-8", newline="")

    scores = directory / SCORES_FILENAME
    with scores.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        for item in items:
            writer.writerow([item["item_id"], "", "", "", "", ""])

    key = directory / KEY_FILENAME
    key.write_text(
        json.dumps(
            {item["item_id"]: {"config": item["config"], "query_id": item["query_id"]}
             for item in items},
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
        newline="",
    )
    return {"sheet": sheet, "scores": scores, "key": key}


def read_scores(path: Path, scales: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    """Load the filled CSV. Blank rows are skipped; bad values are an error."""
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"no calibration scores at {path}")
    out: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for number, row in enumerate(csv.DictReader(handle), start=2):
            identifier = (row.get("item_id") or "").strip()
            if not identifier:
                continue
            record: dict[str, Any] = {"verdict": (row.get("verdict") or "").strip().lower()}
            for name in scales:
                raw = (row.get(name) or "").strip()
                if not raw:
                    record[name] = None
                    continue
                try:
                    value = float(raw)
                except ValueError:
                    raise ValueError(f"{path}:{number}: {name} is {raw!r}, not a number") from None
                if not 1 <= value <= 5:
                    raise ValueError(f"{path}:{number}: {name} is {value}, outside the 1-5 scale")
                record[name] = value
            if record["verdict"] or any(record[name] is not None for name in scales):
                out[identifier] = record
    return out


def build_items(
    resolved: dict[str, Any],
    configs_dir: Path,
    data_root: Path,
    run_directory: Path,
    size: int,
    seed: int,
) -> list[dict[str, Any]]:
    """Assemble the sheet's items: the answer, and everything needed to score it.

    The retrieved passages are included in full. Faithfulness is a question
    about what the system was shown, so a sheet without them would be asking for
    a judgement the reader has no way to make -- and the judge is being given
    them, so a human scoring without them is not scoring the same thing.
    """
    from ..cache_keys import chunk_set_key
    from ..chunking.pipeline import arm_params as chunking_params
    from ..chunking.pipeline import load_chunks
    from ..config import chunk_set_dir
    from ..generation.base import generation_params
    from ..generation.pipeline import answers_path, load_answers
    from ..generation.prompt import render_context
    from ..gold.freeze import GOLD_SET_FILENAME, verify_frozen
    from ..retrieval.pipeline import cells, config_name

    generation = generation_params(resolved)
    separator = str(generation.get("context_separator") or "\n\n")
    queries = {
        query.query_id: query
        for query in verify_frozen(
            Path(configs_dir) / GOLD_SET_FILENAME, str(resolved["gold"].get("gold_set_sha", ""))
        )
    }
    answers: dict[str, dict[str, Any]] = {}
    texts: dict[str, dict[str, str]] = {}
    for chunking, embedding, rerank in cells(resolved):
        config = config_name(chunking, embedding, rerank)
        records = load_answers(answers_path(run_directory, chunking, embedding, rerank))
        if not records:
            continue
        answers[config] = {record.query_id: record for record in records}
        if chunking not in texts:
            chunk_set_id = chunk_set_key(
                str(resolved["corpus"].get("manifest_sha", "")),
                chunking_params(resolved, chunking),
            )
            texts[chunking] = {
                chunk.chunk_id: chunk.text
                for chunk in load_chunks(chunk_set_dir(chunk_set_id, data_root))
            }

    chosen = sample_items(answers, size, seed)
    items: list[dict[str, Any]] = []
    for config, query_id in chosen:
        record = answers[config][query_id]
        chunking = config.split("-", 1)[0]
        context = render_context(
            [texts[chunking][cid] for cid in record.context_chunk_ids], separator
        )
        query = queries[query_id]
        items.append(
            {
                "item_id": item_id(config, query_id),
                "config": config,
                "query_id": query_id,
                "question": query.question,
                "reference_answer": query.reference_answer,
                "judge_note": query.judge_note,
                "answer": record.answer,
                "context": context,
            }
        )
    return items
