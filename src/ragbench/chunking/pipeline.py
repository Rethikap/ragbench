"""Chunking orchestration.

One chunk set per chunking factor level, keyed by
``manifest_sha + PARSER_VERSION + CHUNKER_VERSION + chunking params``. The
embedding factor is not read anywhere in this module -- it is not a parameter,
not an argument, and not in scope. That is invariant I2 enforced by the shape of
the code rather than by a reviewer noticing.
"""

from __future__ import annotations

import collections
import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from ..cache_keys import chunk_set_key
from ..config import chunk_set_dir, parsed_papers_dir
from ..constants import CHUNKER_VERSION, PARSER_VERSION
from ..ingest.manifest import verify_frozen
from ..ingest.store import ArticleStore
from ..jsonl import write_jsonl
from ..tokenizers import DocumentTokens, load_tokenizer
from ..types import Chunk
from .base import assemble, build_chunker, keep_nonempty

CHUNKS_FILENAME = "chunks.jsonl"
META_FILENAME = "chunk_set.json"
Progress = Callable[[str], None] | None


def arm_params(resolved: dict[str, Any], level: str) -> dict[str, Any]:
    """Chunking parameters for one arm: base chunking plus the factor level.

    Deliberately built from ``base.chunking`` and ``factors.chunking`` only. No
    embedding input reaches a chunker.
    """
    try:
        override = resolved["factors"]["chunking"][level]
    except KeyError:
        known = ", ".join(sorted(resolved["factors"]["chunking"]))
        raise ValueError(f"unknown chunking level {level!r}; known: {known}") from None
    params = {**resolved["base"]["chunking"], **override}
    if params.get("chunk_abstract", False):
        # ParsedPaper.body does not contain the abstract, and gold spans are
        # character offsets into that stream. Prepending abstracts would shift
        # every offset in the gold set and hand the specter2 arm the retrieval
        # task it was trained on. See the comment on chunking.chunk_abstract.
        raise ValueError(
            "chunking.chunk_abstract: true is not implemented. Abstracts are kept "
            "in ParsedPaper.abstract for question generation but are deliberately "
            "not part of the chunked, retrievable corpus."
        )
    return params


def chunk_one_arm(
    resolved: dict[str, Any],
    level: str,
    manifest_path: Path,
    data_root: Path,
    on_progress: Progress = None,
) -> dict[str, Any]:
    corpus = resolved["corpus"]
    digest = str(corpus.get("manifest_sha", ""))
    entries = verify_frozen(manifest_path, digest)

    params = arm_params(resolved, level)
    chunk_set_id = chunk_set_key(digest, params)
    directory = chunk_set_dir(chunk_set_id, data_root)
    meta_path = directory / META_FILENAME

    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("n_papers") == len(entries):
            return {**meta, "reused": True, "directory": directory}

    store = ArticleStore(Path(data_root) / "raw_jats", parsed_papers_dir(digest, data_root))
    tokenizer = load_tokenizer(params["tokenizer_id"], params["tokenizer_revision"])
    chunker = build_chunker(params["strategy"], params, tokenizer)

    all_chunks: list[Chunk] = []
    per_paper: dict[str, int] = {}
    separator_levels: collections.Counter[str] = collections.Counter()
    missing: list[str] = []

    for position, entry in enumerate(entries, start=1):
        if not store.has_parsed(entry.pmcid):
            missing.append(entry.pmcid)
            continue
        paper = store.read_parsed(entry.pmcid)
        document = DocumentTokens(paper.body, tokenizer)
        pieces = keep_nonempty(paper.body, chunker.split(document))
        chunks = assemble(paper, pieces, tokenizer)
        for piece in pieces:
            key = "whole" if piece.separator_level is None else str(piece.separator_level)
            separator_levels[key] += 1
        all_chunks.extend(chunks)
        per_paper[paper.pmcid] = len(chunks)
        if on_progress:
            on_progress(f"{level}: {position}/{len(entries)} papers, {len(all_chunks)} chunks")

    if missing:
        raise ValueError(
            f"{len(missing)} manifest papers have no parsed output "
            f"(first: {missing[0]}); run `ragbench ingest` first"
        )

    write_jsonl(directory / CHUNKS_FILENAME, [chunk.to_dict() for chunk in all_chunks])
    meta = {
        "chunk_set_id": chunk_set_id,
        "level": level,
        "strategy": params["strategy"],
        "manifest_sha": digest,
        "parser_version": PARSER_VERSION,
        "chunker_version": CHUNKER_VERSION,
        "tokenizer_id": params["tokenizer_id"],
        "tokenizer_revision": params["tokenizer_revision"],
        "params": {key: params[key] for key in sorted(params)},
        "n_papers": len(entries),
        "n_chunks": len(all_chunks),
        "chunks_per_paper": dict(sorted(per_paper.items())),
        "separator_levels": dict(sorted(separator_levels.items())),
    }
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8", newline="")
    return {**meta, "reused": False, "directory": directory}


def run_chunk(
    resolved: dict[str, Any],
    manifest_path: Path,
    data_root: Path,
    levels: Sequence[str] | None = None,
    on_progress: Progress = None,
) -> list[dict[str, Any]]:
    """Chunk every requested arm. Defaults to every configured chunking level."""
    wanted = list(levels) if levels else list(resolved["factors"]["chunking"])
    return [
        chunk_one_arm(resolved, level, manifest_path, data_root, on_progress) for level in wanted
    ]


def load_chunks(directory: Path) -> list[Chunk]:
    from ..jsonl import read_jsonl

    return [Chunk.from_dict(record) for record in read_jsonl(Path(directory) / CHUNKS_FILENAME)]


def load_meta(directory: Path) -> dict[str, Any]:
    return json.loads((Path(directory) / META_FILENAME).read_text(encoding="utf-8"))
