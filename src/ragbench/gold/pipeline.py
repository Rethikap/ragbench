"""Gold-set orchestration: sample, draft, check, then freeze what a human kept.

Two entry points, matching the two things that actually happen:

``build_candidates``
    Mechanical and repeatable. Samples passages, drafts a question from each,
    runs the three checks, and writes every candidate with its evidence. Safe to
    re-run: same seed, same passages.
``freeze_gold_set``
    Takes the candidates a person marked ``verified``, writes the gold set, and
    pins its digest. This is the step that cannot be regenerated, which is why
    it is separate and why it refuses to run on unverified or stand-in drafts.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..config import parsed_papers_dir, raw_xml_dir
from ..ingest.manifest import verify_frozen as verify_manifest
from ..ingest.store import ArticleStore
from ..jsonl import read_jsonl, write_jsonl
from ..tokenizers import load_tokenizer
from ..types import GoldSpan, ParsedPaper, Query
from .draft import StandInDrafter, build_drafter
from .freeze import CANDIDATES_FILENAME, GOLD_SET_FILENAME, gold_set_sha, write_gold_set
from .passages import sample
from .validate import check, document_frequency

Progress = Callable[[str], None] | None


def load_papers(
    resolved: dict[str, Any], manifest_path: Path, data_root: Path
) -> list[ParsedPaper]:
    digest = str(resolved["corpus"].get("manifest_sha", ""))
    entries = verify_manifest(manifest_path, digest)
    store = ArticleStore(raw_xml_dir(data_root), parsed_papers_dir(digest, data_root))
    missing = [entry.pmcid for entry in entries if not store.has_parsed(entry.pmcid)]
    if missing:
        raise ValueError(
            f"{len(missing)} manifest papers have no parsed output (first: {missing[0]}); "
            "run `ragbench ingest` first"
        )
    return [store.read_parsed(entry.pmcid) for entry in entries]


def build_candidates(
    resolved: dict[str, Any],
    manifest_path: Path,
    data_root: Path,
    out_dir: Path,
    drafter_spec: str | None = None,
    on_progress: Progress = None,
) -> dict[str, Any]:
    gold = resolved["gold"]
    papers = load_papers(resolved, manifest_path, data_root)
    chunking = resolved["base"]["chunking"]
    tokenizer = load_tokenizer(chunking["tokenizer_id"], chunking["tokenizer_revision"])

    frequency = document_frequency(paper.body for paper in papers)
    n_candidates = int(gold["n_questions"]) * int(gold["candidate_multiplier"])
    passages = sample(
        papers, tokenizer, gold, int(resolved["base"]["seed"]), n_candidates
    )

    specification = drafter_spec or str(gold["drafter"])
    drafter = build_drafter(
        specification, resolved["base"]["generation"], str(gold["draft_prompt_id"]), frequency
    )
    by_pmcid = {paper.pmcid: paper for paper in papers}

    records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for position, passage in enumerate(passages, start=1):
        paper = by_pmcid[passage.pmcid]
        try:
            question, answer = drafter.draft(passage)
        except ValueError as exc:
            failures.append({"passage_id": passage.passage_id, "error": str(exc)})
            continue
        verdict = check(
            question, answer, passage.text, paper.abstract, frequency, gold["validation"]
        )
        records.append(
            {
                "query_id": f"q{position:03d}",
                "passage_id": passage.passage_id,
                "pmcid": passage.pmcid,
                "char_start": passage.char_start,
                "char_end": passage.char_end,
                "section": passage.section,
                "question": question,
                "answer": answer,
                "passage": passage.text,
                "drafted_by": getattr(drafter, "drafted_by", lambda _: drafter.name)(passage),
                "draft_prompt_id": gold["draft_prompt_id"],
                # Set by hand. The checks below can only reject; nothing here can
                # promote a candidate into the gold set.
                "verified": False,
                **verdict,
            }
        )
        if on_progress:
            on_progress(f"{position}/{len(passages)} candidates drafted")

    out_dir = Path(out_dir)
    write_jsonl(out_dir / CANDIDATES_FILENAME, records)
    summary = _summarise(records, specification, len(passages), failures)
    (out_dir / "candidates_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8", newline=""
    )
    return {**summary, "directory": out_dir, "records": records}


def _summarise(
    records: list[dict[str, Any]],
    drafter: str,
    n_passages: int,
    failures: list[dict[str, str]],
) -> dict[str, Any]:
    reasons: dict[str, int] = {}
    for record in records:
        for reason in record["reasons"]:
            reasons[reason] = reasons.get(reason, 0) + 1
    rejected = [record for record in records if record["auto_rejected"]]
    return {
        "drafter": drafter,
        "n_passages_sampled": n_passages,
        "n_drafted": len(records),
        "n_draft_failures": len(failures),
        "draft_failures": failures,
        "n_auto_rejected": len(rejected),
        "n_surviving_checks": len(records) - len(rejected),
        # Reasons are not mutually exclusive, so these sum to more than
        # n_auto_rejected whenever a candidate fires more than one check.
        "rejected_by_reason": dict(sorted(reasons.items())),
        "reasons_per_rejected_candidate": {
            str(count): sum(1 for r in rejected if len(r["reasons"]) == count)
            for count in sorted({len(r["reasons"]) for r in rejected})
        },
    }


def load_candidates(directory: Path) -> list[dict[str, Any]]:
    return list(read_jsonl(Path(directory) / CANDIDATES_FILENAME))


def freeze_gold_set(
    resolved: dict[str, Any], candidates: list[dict[str, Any]], configs_dir: Path
) -> dict[str, Any]:
    """Write the verified candidates as the gold set and return its digest.

    Refuses three things, all of which would produce a gold set that looks frozen
    and is not: a stand-in draft, an unverified candidate, and the wrong number
    of questions.
    """
    gold = resolved["gold"]
    wanted = int(gold["n_questions"])

    kept = [record for record in candidates if record.get("verified")]
    if any(record["drafted_by"] == StandInDrafter.name for record in kept):
        raise ValueError(
            "refusing to freeze a gold set containing stand-in drafts. The stand-in "
            "builds cloze questions by string substitution; it exists to smoke-test "
            "the pipeline, not to write an evaluation set."
        )
    if any(record["auto_rejected"] for record in kept):
        raise ValueError(
            "a candidate is marked verified but failed a check. Clear the flag or fix "
            "the candidate -- verification may override taste, not the three checks."
        )
    if len(kept) != wanted:
        raise ValueError(
            f"gold.n_questions is {wanted} but {len(kept)} candidates are marked verified. "
            "Freezing a different number would make the frozen set disagree with the "
            "config that describes it."
        )

    queries = [
        Query(
            query_id=record["query_id"],
            question=record["question"],
            reference_answer=record["answer"],
            gold=GoldSpan(
                pmcid=record["pmcid"],
                char_start=int(record["char_start"]),
                char_end=int(record["char_end"]),
                section=record["section"],
            ),
            verified=True,
        )
        for record in kept
    ]

    configs_dir = Path(configs_dir)
    write_gold_set(configs_dir / GOLD_SET_FILENAME, queries)
    write_jsonl(configs_dir / CANDIDATES_FILENAME, candidates)
    digest = gold_set_sha(queries)
    return {
        "gold_set_sha": digest,
        "n_questions": len(queries),
        "path": configs_dir / GOLD_SET_FILENAME,
        "candidates_path": configs_dir / CANDIDATES_FILENAME,
    }
