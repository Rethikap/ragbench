"""The cache-key hierarchy: the single place where every artefact id is derived.

Four levels, each keyed on exactly what its artefact depends on and nothing more.
Over-keying is not the safe direction: adding an irrelevant input silently
invalidates a cache and forces expensive rebuilds (re-fetching 100 papers because
a factor level was added). Under-keying is worse -- it mixes incomparable
artefacts. So each level is enumerated explicitly here rather than derived from
whatever mapping a caller happens to hold.

    parsed papers  manifest_sha + PARSER_VERSION
    chunk set      manifest_sha + PARSER_VERSION + CHUNKER_VERSION + chunking params
    index          chunk_set_id + embedding model identity
    run outputs    the full resolved config

The chunk-set level is invariant I2 in executable form. The embedding model must
not reach it: if it did, the two embedding arms would produce four chunk sets
instead of two and the factors would stop being orthogonal. That is enforced
structurally by CHUNKING_KEY_FIELDS below -- only those fields are read, so an
embedding id cannot leak in even if the caller passes a mapping containing one.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .constants import CHUNKER_VERSION, PARSER_VERSION
from .hashing import stable_hash

#: The only chunking inputs that may influence chunk boundaries. Note the absence
#: of anything embedding-related; see the module docstring.
CHUNKING_KEY_FIELDS: tuple[str, ...] = (
    "strategy",
    "target_tokens",
    "overlap_tokens",
    "tokenizer_id",
    # The revision, not just the id: the id is a mutable Hub pointer, and a
    # tokenizer that re-segments one word re-draws the boundaries around it.
    "tokenizer_revision",
    "min_chunk_tokens",
    "separators",
    # Whether abstracts enter the chunked corpus at all. Only `false` is
    # implemented, but it decides what is in the chunk set, so it is keyed.
    "chunk_abstract",
)


class CacheKeyError(Exception):
    """A key was requested from an incomplete set of inputs."""


def _select(params: Mapping[str, Any], fields: tuple[str, ...], label: str) -> dict[str, Any]:
    missing = [field for field in fields if field not in params]
    if missing:
        raise CacheKeyError(f"{label}: missing required field(s): {', '.join(missing)}")
    return {field: params[field] for field in fields}


def parsed_papers_key(manifest_sha: str) -> str:
    """Id for the parsed-paper cache.

    Deliberately independent of every factor: parsing depends only on which
    papers were selected and on how the parser behaves. Adding a factor level
    must not invalidate 100 fetched and parsed papers.
    """
    return stable_hash(
        {
            "kind": "parsed_papers",
            "manifest_sha": manifest_sha,
            "parser_version": PARSER_VERSION,
        }
    )


def chunk_set_key(manifest_sha: str, chunking: Mapping[str, Any]) -> str:
    """Id for one chunk set.

    There are exactly two of these across the 8 runs -- one per chunking factor
    level -- because the canonical chunk tokenizer is fixed and no embedding
    input is read here.
    """
    return stable_hash(
        {
            "kind": "chunk_set",
            "manifest_sha": manifest_sha,
            "parser_version": PARSER_VERSION,
            "chunker_version": CHUNKER_VERSION,
            "chunking": _select(chunking, CHUNKING_KEY_FIELDS, "chunking"),
        }
    )


def index_key(chunk_set_id: str, model_id: str, adapter_id: str | None = None) -> str:
    """Id for one vector index.

    ``adapter_id`` is part of the embedding model's identity, not an extra: the
    specter2 arm is ``allenai/specter2_base`` *plus* its adapter, and swapping
    the adapter changes every vector.

    ``embedding.normalize`` and ``embedding.max_seq_tokens`` also affect vectors
    but are fixed in base.yaml for all 8 runs, so they cannot vary and are not
    keyed. If either ever becomes a factor level, it must be added here.
    """
    return stable_hash(
        {
            "kind": "index",
            "chunk_set_id": chunk_set_id,
            "model_id": model_id,
            "adapter_id": adapter_id,
        }
    )


def run_key(resolved: Mapping[str, Any]) -> str:
    """Id for one run's outputs: the full resolved config.

    Order-independent, because canonical_json sorts keys -- reordering a YAML
    mapping must not invent a new run.
    """
    return stable_hash(resolved)
