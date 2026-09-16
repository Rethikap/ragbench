"""Gold-set orchestration: sample, draft, narrow, check, then freeze.

Two entry points, matching the two things that actually happen:

``build_candidates``
    Mechanical and repeatable. Samples passages, takes the authored question for
    each, narrows the label to its minimal evidence span, runs the three checks,
    and writes every candidate with its evidence. Safe to re-run: same seed,
    same passages, same spans.
``freeze_gold_set``
    Writes the gold set and returns its digest. This is the step that cannot be
    regenerated, and it refuses to run unless every selected record has been
    verified by hand.

Three separate booleans, deliberately not one:

``auto_rejected``
    A mechanical check fired. Only the checks set it.
``selected``
    The author proposes this candidate for the gold set.
``verified``
    The author has read the question, the answer and the span, and attests they
    are right.

Collapsing `selected` and `verified` into one flag is what let a gold set be
frozen claiming a verification that had not happened. Selection is editorial and
cheap; verification is a claim about correctness. They are not the same act and
they no longer share a field.
"""

from __future__ import annotations

import collections
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
from .draft import STAND_IN, build_drafter
from .evidence import contiguity_note, resolve, sentence_count
from .freeze import CANDIDATES_FILENAME, GOLD_SET_FILENAME, gold_set_sha, write_gold_set
from .passages import Passage, sample
from .relevance import corpus_drift
from .validate import check, corpus_tokens, document_frequency

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


def load_authored(path: Path) -> dict[str, dict[str, Any]]:
    """The one committed file carrying everything a human decided."""
    records = {record["passage_id"]: record for record in read_jsonl(path)}
    if not records:
        raise ValueError(f"no authored questions in {path}")
    return records


def build_candidates(
    resolved: dict[str, Any],
    manifest_path: Path,
    data_root: Path,
    out_dir: Path,
    configs_dir: Path,
    drafter_spec: str | None = None,
    on_progress: Progress = None,
) -> dict[str, Any]:
    gold = resolved["gold"]
    papers = load_papers(resolved, manifest_path, data_root)
    chunking = resolved["base"]["chunking"]
    tokenizer = load_tokenizer(chunking["tokenizer_id"], chunking["tokenizer_revision"])

    token_sets = corpus_tokens((paper.pmcid, paper.body) for paper in papers)
    frequency = document_frequency(token_sets)
    n_candidates = int(gold["n_questions"]) * int(gold["candidate_multiplier"])

    specification = drafter_spec or str(gold["drafter"])
    authored_path = Path(configs_dir) / str(gold["authored_filename"])
    authored = load_authored(authored_path) if specification == "authored" else {}
    # Passages already written about are pinned, in the order they were first
    # drawn, so a change to the sampling rules cannot discard a completed review.
    pinned = list(authored) if gold.get("pin_authored_passages") and authored else []

    passages = sample(
        papers, tokenizer, gold, int(resolved["base"]["seed"]), n_candidates, pinned
    )
    shortfall = n_candidates - len(passages)
    drafter = build_drafter(specification, authored, frequency)
    by_pmcid = {paper.pmcid: paper for paper in papers}

    records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for position, passage in enumerate(passages, start=1):
        paper = by_pmcid[passage.pmcid]
        query_id = f"q{position:03d}"
        decisions = authored.get(passage.passage_id, {})
        try:
            question, answer = drafter.draft(passage)
            start, end = _evidence_span(paper, passage, decisions, query_id)
        except ValueError as exc:
            failures.append({"passage_id": passage.passage_id, "error": str(exc)})
            continue

        evidence_text = paper.body[start:end]
        # The checks judge the label, so they read the evidence span rather than
        # the paragraph: an answer grounded only in text outside its own span is
        # precisely what narrowing is meant to surface.
        verdict = check(
            question,
            answer,
            evidence_text,
            paper.abstract,
            paper.pmcid,
            token_sets,
            passage.section_kind,
            {**gold["validation"], "methods_section_kinds": gold["methods_section_kinds"]},
        )
        records.append(
            {
                "query_id": query_id,
                "passage_id": passage.passage_id,
                "pmcid": passage.pmcid,
                "section": passage.section,
                "section_kind": passage.section_kind,
                "topic_score": passage.topic_score,
                "char_start": start,
                "char_end": end,
                "context_start": passage.char_start,
                "context_end": passage.char_end,
                "question": question,
                "answer": answer,
                "evidence": evidence_text,
                "context": passage.text,
                "evidence_chars": end - start,
                "context_chars": passage.char_end - passage.char_start,
                "evidence_sentences": sentence_count(evidence_text),
                "contiguity_note": contiguity_note(evidence_text),
                "drafted_by": drafter.drafted_by(passage),
                "draft_prompt_id": gold["draft_prompt_id"],
                "pinned": passage.pinned,
                "on_topic": passage.topic_score >= int(gold["min_topic_terms"]),
                # An off-topic paper cannot be sampled, but a pinned one can
                # already be in the record. Selecting it takes a deliberate,
                # written override -- see freeze_gold_set.
                "off_topic_override": bool(decisions.get("off_topic_override", False)),
                "selected": bool(decisions.get("selected", False)),
                "rejection_reason": str(decisions.get("rejection_reason", "")),
                "note": str(decisions.get("note", "")),
                # Why a warning was overruled, and anything wrong with the source
                # sentence itself. Both are the author's judgement about a record
                # and both have to survive into the artefact to be auditable --
                # the second so the judge stage does not penalise a generated
                # answer for reproducing an error the paper made.
                "warning_resolution": str(decisions.get("warning_resolution", "")),
                "source_note": str(decisions.get("source_note", "")),
                # Never inferred, never defaulted true. The author sets it in the
                # authored file after reading question, answer and span.
                "verified": bool(decisions.get("verified", False)),
                **verdict,
            }
        )
        if on_progress:
            on_progress(f"{position}/{len(passages)} candidates built")

    out_dir = Path(out_dir)
    write_jsonl(out_dir / CANDIDATES_FILENAME, records)
    summary = _summarise(records, specification, len(passages), failures)
    summary["corpus_drift"] = corpus_drift(papers, gold)
    # Reported, never quietly made up by reaching past the gate.
    summary["n_requested"] = n_candidates
    summary["shortfall"] = max(0, shortfall)
    (out_dir / "candidates_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8", newline=""
    )
    return {**summary, "directory": out_dir, "records": records}


def _evidence_span(
    paper: ParsedPaper, passage: Passage, decisions: dict[str, Any], query_id: str
) -> tuple[int, int]:
    """Narrow the label, or refuse to pretend a paragraph is one.

    An unselected candidate keeps the paragraph: it never becomes a label, so
    there is nothing to narrow. A *selected* one without anchors is an error,
    because the alternative is a gold set whose spans are silently the recursive
    chunker's own splitting unit.
    """
    prefix = str(decisions.get("evidence_prefix", ""))
    suffix = str(decisions.get("evidence_suffix", ""))
    if not decisions.get("selected"):
        return passage.char_start, passage.char_end
    if not prefix or not suffix:
        raise ValueError(
            f"{query_id} ({passage.passage_id}) is selected but has no evidence anchors. "
            "A selected candidate must narrow its label to the sentence(s) that answer "
            "the question; keeping the paragraph would make the gold set an artefact of "
            "one chunker's boundaries."
        )
    return resolve(paper, passage.char_start, passage.char_end, prefix, suffix, query_id)


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
    selected = [record for record in records if record["selected"]]
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
        "n_selected": len(selected),
        "n_verified": sum(1 for record in selected if record["verified"]),
        "unverified": sorted(r["query_id"] for r in selected if not r["verified"]),
        "section_kinds": {
            kind: sum(1 for r in records if r["section_kind"] == kind)
            for kind in sorted({r["section_kind"] for r in records})
        },
        "selected_section_kinds": {
            kind: sum(1 for r in selected if r["section_kind"] == kind)
            for kind in sorted({r["section_kind"] for r in selected})
        },
        "n_with_warnings": sum(1 for r in records if r["warnings"]),
        "n_off_topic_selected": sum(1 for r in selected if not r["on_topic"]),
        "off_topic_overrides": sorted(
            r["query_id"] for r in selected if r["off_topic_override"]
        ),
        "n_pinned": sum(1 for r in records if r["pinned"]),
    }


def load_candidates(directory: Path) -> list[dict[str, Any]]:
    return list(read_jsonl(Path(directory) / CANDIDATES_FILENAME))


def selected_queries(candidates: list[dict[str, Any]]) -> list[Query]:
    """The selected candidates as Query records, verified or not.

    The report and the verification sheet both need this: an unfrozen,
    unverified draft is exactly the state the author reads it in.
    """
    return [
        Query(
            query_id=record["query_id"],
            question=record["question"],
            reference_answer=record["answer"],
            gold=GoldSpan(
                pmcid=record["pmcid"],
                char_start=int(record["char_start"]),
                char_end=int(record["char_end"]),
                section=record["section"],
                context_start=int(record["context_start"]),
                context_end=int(record["context_end"]),
            ),
            verified=bool(record["verified"]),
        )
        for record in candidates
        if record.get("selected")
    ]


def freeze_gold_set(
    resolved: dict[str, Any], candidates: list[dict[str, Any]], configs_dir: Path
) -> dict[str, Any]:
    """Write the selected candidates as the gold set and return its digest.

    Refuses four things, each of which would produce a gold set that looks
    frozen and is not: an unverified record, a stand-in draft, a record that
    failed a mechanical check, and the wrong number of questions.
    """
    gold = resolved["gold"]
    wanted = int(gold["n_questions"])
    kept = [record for record in candidates if record.get("selected")]

    unverified = sorted(record["query_id"] for record in kept if not record.get("verified"))
    if unverified:
        shown = ", ".join(unverified[:8]) + ("..." if len(unverified) > 8 else "")
        raise ValueError(
            f"{len(unverified)} of {len(kept)} selected questions are not verified "
            f"({shown}). Freezing would stamp a digest over content claiming a human "
            'read it. Set "verified": true in the authored file, per question, after '
            "reading the question, the answer and the evidence span; "
            "`ragbench gold sheet` prints them."
        )
    if any(record["drafted_by"] == STAND_IN for record in kept):
        raise ValueError(
            "refusing to freeze a gold set containing stand-in drafts. The stand-in "
            "builds cloze questions by string substitution; it exists to smoke-test "
            "the pipeline, not to write an evaluation set."
        )
    if any(record["auto_rejected"] for record in kept):
        raise ValueError(
            "a selected candidate failed a mechanical check. Deselect it or fix it -- "
            "verification may override taste, not the three checks."
        )
    if len(kept) != wanted:
        raise ValueError(
            f"gold.n_questions is {wanted} but {len(kept)} candidates are selected. "
            "Freezing a different number would make the frozen set disagree with the "
            "config that describes it."
        )
    # Two questions from one paper share its abstract, its vocabulary and its
    # distractors, so they are not independent measurements of retrieval. The
    # sampler enforces this while it draws; enforce it again on what is actually
    # frozen, because a candidate can be selected by hand.
    ungated = sorted(
        record["query_id"]
        for record in kept
        if not record.get("on_topic") and not record.get("off_topic_override")
    )
    if ungated:
        raise ValueError(
            f"{len(ungated)} selected questions come from papers below "
            f"gold.min_topic_terms ({', '.join(ungated)}). The topic gate keeps them out "
            'of the sample; selecting one anyway needs "off_topic_override": true and a '
            "note saying why the score is wrong, recorded on the authored record."
        )
    overridden = [record for record in kept if record.get("off_topic_override")]
    if any(not record.get("note") for record in overridden):
        raise ValueError(
            "an off_topic_override carries no note. An override without a stated "
            "reason is indistinguishable from an oversight, which is the failure it "
            "exists to prevent."
        )

    per_paper = collections.Counter(record["pmcid"] for record in kept)
    doubled = sorted(pmcid for pmcid, count in per_paper.items() if count > 1)
    if doubled:
        raise ValueError(
            f"{len(doubled)} papers contribute more than one selected question "
            f"({', '.join(doubled[:5])}). Two questions from one paper are not two "
            "independent measurements of retrieval."
        )

    queries = selected_queries(candidates)
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
