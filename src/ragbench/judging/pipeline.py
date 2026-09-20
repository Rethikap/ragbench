"""Judging orchestration: every answer scored, twice, resumably.

Three things make this stage different from the ones before it.

**It costs money and is throttled.** So the unit of resumption is one
(configuration, question, pass): a record on disk is never re-judged, and a
session killed after 200 of 320 calls resumes at 201. Nothing here retries work
that succeeded.

**Abstentions are recognised, not asked about.** An answer that is exactly the
configured refusal sentence is classified without an API call. That is 40 of the
320 calls saved on this run, and it removes a class of judge error from a
question with one right answer. A *paraphrased* refusal still goes to the judge,
which is why ``abstained`` remains in the rubric's vocabulary -- and the report
counts the two paths separately, so a generator that started improvising its
refusals would be visible rather than silently reclassified.

**A judgement is tied to the answer it judged.** The rubric lives in config and
so moves the run id when edited; what that cannot catch is `generate` re-run
underneath a directory that already holds judgements. Each record carries the
answer's digest and resumption refuses on a mismatch.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from ..cache_keys import chunk_set_key
from ..chunking.pipeline import arm_params as chunking_params
from ..chunking.pipeline import load_chunks
from ..config import chunk_set_dir
from ..generation.base import generation_params
from ..generation.pipeline import answers_path, load_answers
from ..generation.prompt import render_context
from ..gold.freeze import GOLD_SET_FILENAME, verify_frozen
from ..hashing import sha256_text
from ..jsonl import append_jsonl, read_jsonl, write_jsonl
from ..retrieval.pipeline import cells, config_name, load_results, results_path
from ..types import Judgement
from .base import (
    ABSTAINED,
    UNPARSED,
    JudgeQuotaExhausted,
    LazyJudge,
    Verdict,
    judge_params,
)
from .prompt import build_prompt, rubric_digest

Progress = Callable[[str], None] | None


def judgements_path(run_directory: Path, chunking: str, embedding: str, rerank: str) -> Path:
    return Path(run_directory) / "judge" / f"{config_name(chunking, embedding, rerank)}.jsonl"


def load_judgements(path: Path) -> list[Judgement]:
    return [Judgement.from_dict(record) for record in read_jsonl(path)]


def clear_unparsed(path: Path) -> int:
    """Drop the unparsed records from one configuration's file.

    An unparsed record is persisted deliberately: it stops a re-run spending the
    calls again, and it keeps the configuration's denominator honest. But that
    makes it permanent, and a judgement that failed because the *settings* were
    wrong must not survive a change to those settings -- the configuration would
    then be scored under two regimes with nothing to say which item came from
    which.

    Rewriting the file rather than hand-editing JSONL is the point: the records
    that stay are re-serialised through the same canonical writer that appended
    them, so the file is byte-identical to one that had never held the failures.
    """
    records = load_judgements(path)
    keep = [record for record in records if record.verdict != UNPARSED]
    removed = len(records) - len(keep)
    if removed:
        write_jsonl(path, [record.to_dict() for record in keep])
    return removed


def is_refusal(answer: str, refusal_text: str) -> bool:
    """Exact match on the configured sentence, modulo a trailing full stop."""
    return bool(refusal_text) and answer.strip().rstrip(".") == refusal_text.strip().rstrip(".")


def _context_for(chunk_ids: Sequence[str], texts: dict[str, str], separator: str) -> str:
    """Rebuild what the generator was shown, from the chunk ids it recorded."""
    return render_context([texts[identifier] for identifier in chunk_ids], separator)


def judge_one_config(
    resolved: dict[str, Any],
    chunking_level: str,
    embedding_level: str,
    rerank_level: str,
    configs_dir: Path,
    data_root: Path,
    run_directory: Path,
    judge: Any = None,
    retry_unparsed: bool = False,
    on_progress: Progress = None,
) -> dict[str, Any]:
    """One of the 8 cells, every answer, every pass."""
    params = judge_params(resolved)
    generation = generation_params(resolved)
    refusal_text = str(generation.get("refusal_text") or "")
    separator = str(generation.get("context_separator") or "\n\n")
    config = config_name(chunking_level, embedding_level, rerank_level)
    passes = max(1, int(params.get("passes", 1)))

    queries = {
        query.query_id: query
        for query in verify_frozen(
            Path(configs_dir) / GOLD_SET_FILENAME, str(resolved["gold"].get("gold_set_sha", ""))
        )
    }
    source = answers_path(run_directory, chunking_level, embedding_level, rerank_level)
    if not source.is_file():
        raise ValueError(f"no answers at {source}; run `ragbench generate` first")
    answers = {record.query_id: record for record in load_answers(source)}

    chunk_set_id = chunk_set_key(
        str(resolved["corpus"].get("manifest_sha", "")),
        chunking_params(resolved, chunking_level),
    )
    texts = {
        chunk.chunk_id: chunk.text
        for chunk in load_chunks(chunk_set_dir(chunk_set_id, data_root))
    }
    # The answer records the chunk ids it was given, but an older file may not
    # have; fall back to the retrieval results, which are the same list.
    fallback = {
        result.query_id: [scored.chunk_id for scored in result.selected]
        for result in load_results(
            results_path(run_directory, chunking_level, embedding_level, rerank_level)
        )
    }

    path = judgements_path(run_directory, chunking_level, embedding_level, rerank_level)
    cleared = clear_unparsed(path) if retry_unparsed else 0
    existing = load_judgements(path)
    done: set[tuple[str, int]] = set()
    for record in existing:
        answer = answers.get(record.query_id)
        if answer is None:
            raise ValueError(
                f"{config}: a judgement exists for {record.query_id} but no answer does. "
                "The generated answers changed under this run directory."
            )
        digest = sha256_text(answer.answer)
        if record.answer_sha256 and record.answer_sha256 != digest:
            raise ValueError(
                f"{config}: {record.query_id} was judged against a different answer "
                f"({record.answer_sha256[:12]} on disk, {digest[:12]} now). Generation has "
                "been re-run here. Delete the judge file for this configuration rather "
                "than scoring two sets of answers into one."
            )
        done.add((record.query_id, record.pass_index))

    pending = [
        (query_id, index)
        for query_id in sorted(answers)
        for index in range(passes)
        if (query_id, index) not in done
    ]
    if judge is None:
        judge = LazyJudge(params)

    calls = 0
    exhausted = ""
    for position, (query_id, index) in enumerate(pending, start=1):
        answer = answers[query_id]
        query = queries[query_id]
        chunk_ids = list(answer.context_chunk_ids) or fallback.get(query_id, [])
        started = time.perf_counter()

        before = int(getattr(judge, "tokens_spent", 0))
        if is_refusal(answer.answer, refusal_text):
            verdict = Verdict(verdict=ABSTAINED, rationale="exact refusal sentence")
            from_match = True
        else:
            prompt = build_prompt(
                params,
                question=query.question,
                reference_answer=query.reference_answer,
                context=_context_for(chunk_ids, texts, separator),
                answer=answer.answer,
                judge_note=query.judge_note,
            )
            from_match = False
            calls += 1
            try:
                verdict = judge.score(prompt)
            except JudgeQuotaExhausted as exc:
                # A schedule, not a failure. Everything already appended stays;
                # stop here rather than spending retries against a wall.
                exhausted = str(exc)
                break
            except ValueError as exc:
                # Twice unparseable. Persist it so the API budget is not spent
                # again on the next run, and count it loudly in the report.
                verdict = Verdict(verdict=UNPARSED, rationale=str(exc)[:300], n_parse_retries=1)

        append_jsonl(
            path,
            Judgement(
                query_id=query_id,
                scores=verdict.scores,
                rationale=verdict.rationale,
                judge_model=getattr(judge, "name", "none") if not from_match else "refusal-match",
                rubric_id=str(params.get("rubric_id") or ""),
                verdict=verdict.verdict,
                pass_index=index,
                answer_sha256=sha256_text(answer.answer),
                n_parse_retries=verdict.n_parse_retries,
                n_tokens=int(getattr(judge, "tokens_spent", 0)) - before,
                latency_ms=round((time.perf_counter() - started) * 1000.0, 1),
                from_refusal_match=from_match,
            ).to_dict(),
        )
        if on_progress:
            on_progress(f"{config}: {position}/{len(pending)} judgements ({calls} calls)")

    records = load_judgements(path)
    return {
        "config": config,
        "chunking_level": chunking_level,
        "embedding_level": embedding_level,
        "rerank_level": rerank_level,
        "judge": getattr(judge, "name", "none (nothing to judge)"),
        "rubric_id": str(params.get("rubric_id") or ""),
        "rubric_digest": rubric_digest(params),
        "passes": passes,
        "n_judgements": len(records),
        "n_expected": len(answers) * passes,
        "written": len(records) - len(existing),
        "reused": len(existing),
        "outstanding": len(answers) * passes - len(records),
        "api_calls": calls,
        "unparsed_cleared": cleared,
        "quota_exhausted": bool(exhausted),
        "quota_message": exhausted,
        "abstained": sum(1 for r in records if r.verdict == ABSTAINED),
        "unparsed": sum(1 for r in records if r.verdict == UNPARSED),
        "parse_retries": sum(r.n_parse_retries for r in records),
        "tokens": sum(r.n_tokens for r in records),
        "path": str(path),
    }


def run_judge(
    resolved: dict[str, Any],
    configs_dir: Path,
    data_root: Path,
    run_directory: Path,
    levels: Sequence[tuple[str, str, str]] | None = None,
    judge: Any = None,
    retry_unparsed: bool = False,
    on_progress: Progress = None,
) -> list[dict[str, Any]]:
    """Every cell, sharing one judge so the rate limiter paces the whole run."""
    wanted = list(levels) if levels else list(cells(resolved))
    judge = judge or LazyJudge(judge_params(resolved))
    reports = [
        judge_one_config(
            resolved, chunking, embedding, rerank, configs_dir, data_root, run_directory,
            judge=judge, retry_unparsed=retry_unparsed, on_progress=on_progress,
        )
        for chunking, embedding, rerank in wanted
    ]
    summary = Path(run_directory) / "judge" / "summary.json"
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(json.dumps(reports, indent=2, sort_keys=True), encoding="utf-8", newline="")
    return reports
