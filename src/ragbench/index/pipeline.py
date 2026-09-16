"""Index orchestration: four indexes, one per (chunk set, embedding arm) pair.

The chunk set arrives as an id and a list of Chunk records. The embedder arrives
built. Neither can reach the other's parameters, which is invariant I2 holding
one level up from where it was enforced during chunking: the two factors meet
here, in :func:`~ragbench.cache_keys.index_key`, and they meet as two opaque
strings.

Resumability is per batch, not per index. A run interrupted halfway leaves a
collection holding the chunks it got to; the next run asks the store which ids
it already has and embeds only the rest. A completed run therefore does one
`existing_ids` call per batch and no model work at all.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from ..cache_keys import chunk_set_key, index_key
from ..chunking.pipeline import arm_params as chunking_params
from ..chunking.pipeline import load_chunks
from ..config import chunk_set_dir, index_dir
from ..embedding.base import (
    SPECIAL_TOKENS,
    arm_params,
    build_embedder,
    token_counter,
    usable_tokens,
)
from ..types import Chunk
from .store import ChromaStore, VectorStore

META_FILENAME = "index.json"
Progress = Callable[[str], None] | None


def _peak_rss_mb() -> float:
    """Resident set size now, in MB. Sampled at batch boundaries; the maximum of
    those samples is the peak this stage reports."""
    try:
        import psutil

        return psutil.Process().memory_info().rss / (1024 * 1024)
    except Exception:  # noqa: BLE001 - a missing metric must not fail a build
        return 0.0


def truncation_census(
    chunks: Sequence[Chunk],
    count_tokens: Callable[[str], int],
    max_seq_tokens: int,
    canonical_tokenizer: bool = False,
) -> dict[str, Any]:
    """Chunks whose tail the encoder will drop, counted before anything is written.

    `max_seq_tokens` is the model's position limit and it *includes* [CLS] and
    [SEP], so a chunk has room for ``max_seq_tokens - 2`` content tokens. The
    chunker's own target is expressed in content tokens and knows nothing about
    special tokens, which is exactly where the two can disagree -- and they do.
    Counted rather than assumed, per index, with the worst overflow recorded so
    the size of the problem is visible and not just its existence.
    """
    limit = usable_tokens(max_seq_tokens)
    lengths = [count_tokens(chunk.text) for chunk in chunks]
    over = [length for length in lengths if length > limit]
    return {
        "max_seq_tokens": max_seq_tokens,
        "special_tokens": SPECIAL_TOKENS,
        "usable_content_tokens": limit,
        # Which of the two causes this arm can suffer from. An arm using the
        # canonical chunk tokenizer can only overflow by miscounting the special
        # tokens, which is arithmetic and fixable. Any other arm can overflow
        # because its tokenizer makes more of the same text than the canonical
        # one did -- a consequence of I2, not a defect. See CLAUDE.md.
        "canonical_tokenizer": canonical_tokenizer,
        "cause": "special_token_budget" if canonical_tokenizer else "cross_tokenizer_expansion",
        "n_truncated": len(over),
        "share_truncated": round(len(over) / len(lengths), 4) if lengths else 0.0,
        "max_content_tokens": max(lengths) if lengths else 0,
        "worst_overflow_tokens": max(over) - limit if over else 0,
        "mean_content_tokens": round(sum(lengths) / len(lengths), 1) if lengths else 0.0,
    }


def build_one_index(
    resolved: dict[str, Any],
    chunking_level: str,
    embedding_level: str,
    data_root: Path,
    store: VectorStore | None = None,
    census_only: bool = False,
    on_progress: Progress = None,
) -> dict[str, Any]:
    """Build (or resume, or reuse) one index.

    ``census_only`` stops after the truncation census, which needs the arm's
    tokenizer and not its weights. It is how the one number in this stage that
    must be checked rather than assumed gets checked without a GPU.
    """
    digest = str(resolved["corpus"].get("manifest_sha", ""))
    chunk_params = chunking_params(resolved, chunking_level)
    chunk_set_id = chunk_set_key(digest, chunk_params)
    directory = chunk_set_dir(chunk_set_id, data_root)
    if not (directory / "chunk_set.json").is_file():
        raise ValueError(
            f"chunk set for {chunking_level!r} not built; run `ragbench chunk` first"
        )
    chunks = load_chunks(directory)

    params = arm_params(resolved, embedding_level)
    identifier = index_key(
        chunk_set_id,
        str(params["model_id"]),
        str(params.get("model_revision") or ""),
        params.get("adapter_id"),
        params.get("adapter_revision"),
    )
    target = index_dir(identifier, data_root)
    meta_path = target / META_FILENAME

    canonical = str(params["model_id"]) == str(chunk_params["tokenizer_id"])
    census = truncation_census(
        chunks, token_counter(params), int(params["max_seq_tokens"]), canonical
    )
    if census_only:
        return {
            "index_id": identifier,
            "chunking_level": chunking_level,
            "embedding_level": embedding_level,
            "chunk_set_id": chunk_set_id,
            "model_id": params["model_id"],
            "model_revision": params.get("model_revision"),
            "adapter_id": params.get("adapter_id"),
            "n_chunks": len(chunks),
            "census_only": True,
            "truncation": census,
        }

    embedder = build_embedder(params)
    if store is None:
        store = ChromaStore(target / "chroma", identifier)

    batch_size = int(params.get("batch_size", 32))
    started = time.perf_counter()
    peak_rss = _peak_rss_mb()
    written = 0
    skipped = 0

    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        ids = [chunk.chunk_id for chunk in batch]
        already = store.existing_ids(ids)
        pending = [chunk for chunk in batch if chunk.chunk_id not in already]
        skipped += len(batch) - len(pending)
        if pending:
            vectors = embedder.encode_documents([chunk.text for chunk in pending])
            store.add(
                [chunk.chunk_id for chunk in pending],
                vectors,
                [chunk.text for chunk in pending],
                [
                    {
                        "pmcid": chunk.pmcid,
                        "chunk_index": chunk.chunk_index,
                        "n_tokens": chunk.n_tokens,
                        "char_start": chunk.char_start,
                        "char_end": chunk.char_end,
                        "sections": " | ".join(chunk.sections),
                    }
                    for chunk in pending
                ],
            )
            written += len(pending)
        peak_rss = max(peak_rss, _peak_rss_mb())
        if on_progress:
            on_progress(
                f"{chunking_level}/{embedding_level}: {start + len(batch)}/{len(chunks)} "
                f"chunks ({written} embedded, {skipped} already present)"
            )

    meta = {
        "index_id": identifier,
        "chunking_level": chunking_level,
        "embedding_level": embedding_level,
        "chunk_set_id": chunk_set_id,
        "manifest_sha": digest,
        "embedder": embedder.name,
        "model_id": params["model_id"],
        "model_revision": params.get("model_revision"),
        "adapter_id": params.get("adapter_id"),
        "adapter_revision": params.get("adapter_revision"),
        "dimension": int(embedder.dimension),
        "normalize": bool(params.get("normalize", True)),
        "pooling": params.get("pooling"),
        "n_chunks": len(chunks),
        "vectors_written": written,
        "vectors_reused": skipped,
        "vectors_in_store": store.count(),
        "build_seconds": round(time.perf_counter() - started, 2),
        "peak_rss_mb": round(peak_rss, 1),
        "truncation": census,
        "directory": str(target),
    }
    target.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8", newline="")
    return meta


def run_index(
    resolved: dict[str, Any],
    data_root: Path,
    chunking_levels: Sequence[str] | None = None,
    embedding_levels: Sequence[str] | None = None,
    census_only: bool = False,
    on_progress: Progress = None,
) -> list[dict[str, Any]]:
    """Every (chunking, embedding) pair. Four of them, and the count is derived
    from factors.yaml rather than written down anywhere."""
    chunkings = list(chunking_levels or resolved["factors"]["chunking"])
    embeddings = list(embedding_levels or resolved["factors"]["embedding"])
    return [
        build_one_index(
            resolved,
            chunking,
            embedding,
            data_root,
            census_only=census_only,
            on_progress=on_progress,
        )
        for chunking in chunkings
        for embedding in embeddings
    ]


def load_index_meta(directory: Path) -> dict[str, Any]:
    return json.loads((Path(directory) / META_FILENAME).read_text(encoding="utf-8"))
