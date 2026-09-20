"""Generation orchestration: one answer per (configuration, question).

The same shape as retrieval -- JSONL per configuration, keyed by query id, so an
interrupted run continues and a finished one does nothing. What is different is
the integrity check on resume: every record already on disk has its prompt
re-rendered and its digest compared before anything new is written.

That is not redundant with the prompt living in config. Those two guards cover
different halves of the same failure. Editing the template moves the resolved
config and therefore the run id, so the new answers land in a new directory and
can never mix with the old. What that cannot catch is a prompt that changes
while the config does not -- retrieval re-run over the same directory and
selecting different chunks, a chunk set rebuilt underneath, a file copied in
from another run. The context is part of the prompt, so those change it too, and
without the digest the stage would top up a file whose answers came from a
different context and nothing afterwards could separate them.
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
from ..gold.freeze import GOLD_SET_FILENAME, verify_frozen
from ..jsonl import append_jsonl, read_jsonl
from ..retrieval.pipeline import cells, config_name, load_results, results_path
from ..types import Chunk, GeneratedAnswer, Query, RetrievalResult
from .base import FINISH_LENGTH, build_generator, generation_params, sampling_params
from .prompt import Prompt, build_prompt, render_context, template_digest

Progress = Callable[[str], None] | None


def answers_path(run_directory: Path, chunking: str, embedding: str, rerank: str) -> Path:
    return Path(run_directory) / "generate" / f"{config_name(chunking, embedding, rerank)}.jsonl"


def load_answers(path: Path) -> list[GeneratedAnswer]:
    return [GeneratedAnswer.from_dict(record) for record in read_jsonl(path)]


def prompt_for(
    query: Query,
    result: RetrievalResult,
    chunks_by_id: dict[str, Chunk],
    params: dict[str, Any],
) -> Prompt:
    """Assemble one prompt from what retrieval selected, in rank order."""
    texts = [chunks_by_id[scored.chunk_id].text for scored in result.selected]
    context = render_context(texts, str(params.get("context_separator") or "\n\n"))
    return build_prompt(params, context, query.question)


def _check_resumable(
    existing: list[GeneratedAnswer], prompts: dict[str, Prompt], config: str
) -> None:
    """Refuse to top up a file whose answers came from a different prompt."""
    for record in existing:
        prompt = prompts.get(record.query_id)
        if prompt is None:
            raise ValueError(
                f"{config}: {record.query_id} has an answer but is not in the gold set. "
                "The gold set changed under this run directory."
            )
        if record.prompt_sha256 != prompt.sha256:
            raise ValueError(
                f"{config}: {record.query_id} was answered from a different prompt "
                f"({record.prompt_sha256[:12]} on disk, {prompt.sha256[:12]} now). Most "
                "likely retrieval was re-run over this directory and chose different "
                "chunks, or the chunk set on disk was rebuilt. Delete the file and "
                "regenerate this configuration, rather than mixing two prompts in one run."
            )


def generate_one_config(
    resolved: dict[str, Any],
    chunking_level: str,
    embedding_level: str,
    rerank_level: str,
    configs_dir: Path,
    data_root: Path,
    run_directory: Path,
    generator: Any = None,
    batch_size: int = 0,
    on_progress: Progress = None,
) -> dict[str, Any]:
    """One of the 8 cells, resumable at question granularity."""
    params = generation_params(resolved)
    config = config_name(chunking_level, embedding_level, rerank_level)
    digest = str(resolved["corpus"].get("manifest_sha", ""))

    queries = verify_frozen(
        Path(configs_dir) / GOLD_SET_FILENAME, str(resolved["gold"].get("gold_set_sha", ""))
    )
    chunk_set_id = chunk_set_key(digest, chunking_params(resolved, chunking_level))
    chunks_by_id = {
        chunk.chunk_id: chunk for chunk in load_chunks(chunk_set_dir(chunk_set_id, data_root))
    }

    source = results_path(run_directory, chunking_level, embedding_level, rerank_level)
    if not source.is_file():
        raise ValueError(f"no retrieval results at {source}; run `ragbench retrieve` first")
    results = {result.query_id: result for result in load_results(source)}
    absent = [query.query_id for query in queries if query.query_id not in results]
    if absent:
        raise ValueError(
            f"{config}: retrieval is incomplete -- no result for {', '.join(absent)}. "
            "Finish `ragbench retrieve` before generating."
        )

    prompts = {
        query.query_id: prompt_for(query, results[query.query_id], chunks_by_id, params)
        for query in queries
    }
    path = answers_path(run_directory, chunking_level, embedding_level, rerank_level)
    existing = load_answers(path)
    _check_resumable(existing, prompts, config)

    done = {record.query_id for record in existing}
    pending = [query.query_id for query in queries if query.query_id not in done]
    if generator is None and pending:
        generator = build_generator(params)

    size = max(1, batch_size if batch_size > 0 else len(pending))
    started = time.perf_counter()
    for start in range(0, len(pending), size):
        window = pending[start : start + size]
        batch_started = time.perf_counter()
        completions = generator.generate_many([prompts[identifier] for identifier in window])
        elapsed_ms = (time.perf_counter() - batch_started) * 1000.0
        # Amortised, not measured: vLLM decodes a batch concurrently, so there is
        # no per-answer wall clock to record. The configuration's own wall clock
        # below is the measured quantity, and the report says which is which.
        each_ms = elapsed_ms / len(window)
        for identifier, completion in zip(window, completions, strict=True):
            append_jsonl(
                path,
                GeneratedAnswer(
                    query_id=identifier,
                    answer=completion.text,
                    prompt_sha256=prompts[identifier].sha256,
                    n_prompt_tokens=completion.n_prompt_tokens,
                    n_completion_tokens=completion.n_completion_tokens,
                    latency_ms=round(each_ms, 2),
                    finish_reason=completion.finish_reason,
                    context_chunk_ids=tuple(
                        scored.chunk_id for scored in results[identifier].selected
                    ),
                    n_context_chunks=results[identifier].n_chunks,
                ).to_dict(),
            )
        if on_progress:
            on_progress(f"{config}: {min(start + len(window), len(pending))}/{len(pending)} new")
    wall_ms = (time.perf_counter() - started) * 1000.0

    answers = load_answers(path)
    return {
        "config": config,
        "chunking_level": chunking_level,
        "embedding_level": embedding_level,
        "rerank_level": rerank_level,
        "generator": getattr(generator, "name", "none (nothing to generate)"),
        "prompt_template_id": str(params.get("prompt_template_id") or ""),
        "prompt_digest": template_digest(params),
        "sampling": sampling_params(params),
        "n_answers": len(answers),
        "answers_written": len(pending),
        "answers_reused": len(answers) - len(pending),
        "batch_size": size if pending else 0,
        "wall_clock_ms": round(wall_ms, 1) if pending else 0.0,
        "hit_max_new_tokens": sum(1 for a in answers if a.finish_reason == FINISH_LENGTH),
        "path": str(path),
    }


def run_generate(
    resolved: dict[str, Any],
    configs_dir: Path,
    data_root: Path,
    run_directory: Path,
    levels: Sequence[tuple[str, str, str]] | None = None,
    generator: Any = None,
    batch_size: int = 0,
    runtime: dict[str, Any] | None = None,
    on_progress: Progress = None,
) -> list[dict[str, Any]]:
    """Every cell, sharing one generator: loading a 7B model 8 times is 8x the wait.

    ``runtime`` carries host settings (VRAM fraction, eager mode) that cannot
    change an answer, which is why they arrive here as an argument rather than
    through the resolved config and the run id.
    """
    wanted = list(levels) if levels else list(cells(resolved))
    if generator is None:
        generator = build_generator(generation_params(resolved), **(runtime or {}))
    reports = [
        generate_one_config(
            resolved, chunking, embedding, rerank, configs_dir, data_root, run_directory,
            generator=generator, batch_size=batch_size, on_progress=on_progress,
        )
        for chunking, embedding, rerank in wanted
    ]
    summary = Path(run_directory) / "generate" / "summary.json"
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(json.dumps(reports, indent=2, sort_keys=True), encoding="utf-8", newline="")
    return reports
