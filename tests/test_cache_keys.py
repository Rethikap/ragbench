"""The cache-key hierarchy, and invariant I2 in executable form."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pytest

from ragbench import cache_keys
from ragbench.cache_keys import (
    CacheKeyError,
    chunk_set_key,
    index_key,
    parsed_papers_key,
    run_key,
)
from ragbench.config import resolve_config

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_CONFIG = REPO_ROOT / "configs" / "base.yaml"
SHA = "0123456789ab"


@pytest.fixture
def resolved() -> dict[str, Any]:
    return resolve_config(BASE_CONFIG)


def _arm(resolved: dict[str, Any], chunking_level: str) -> dict[str, Any]:
    """Chunking params for one arm: base chunking + the factor level."""
    return {**resolved["base"]["chunking"], **resolved["factors"]["chunking"][chunking_level]}


# --------------------------------------------------------------- invariant I2


def test_both_embedding_arms_resolve_to_the_same_chunk_set(resolved: dict[str, Any]) -> None:
    """Two chunk sets, not four.

    The loop deliberately merges each embedding level into the chunking params,
    simulating the most likely mistake: a caller passing "this arm's config"
    wholesale. The ids must still be identical, because chunk_set_key reads only
    the chunking allowlist.
    """
    for chunking_level in resolved["factors"]["chunking"]:
        params = _arm(resolved, chunking_level)
        ids = {
            chunk_set_key(SHA, {**params, **embedding_level})
            for embedding_level in resolved["factors"]["embedding"].values()
        }
        assert len(ids) == 1, f"{chunking_level}: embedding model leaked into the chunk-set key"


def test_the_whole_design_has_exactly_two_chunk_sets(resolved: dict[str, Any]) -> None:
    ids = {
        chunk_set_key(SHA, {**_arm(resolved, chunking_level), **embedding_level})
        for chunking_level in resolved["factors"]["chunking"]
        for embedding_level in resolved["factors"]["embedding"].values()
    }
    assert len(ids) == 2
    assert math.prod(len(levels) for levels in resolved["factors"].values()) == 8


def test_the_two_chunking_strategies_differ(resolved: dict[str, Any]) -> None:
    assert chunk_set_key(SHA, _arm(resolved, "fixed")) != chunk_set_key(
        SHA, _arm(resolved, "recursive")
    )


def test_chunk_set_key_rejects_incomplete_params() -> None:
    with pytest.raises(CacheKeyError, match="target_tokens"):
        chunk_set_key(SHA, {"strategy": "fixed"})


# --------------------------------------------------------------- parsed papers


def test_parsed_papers_key_tracks_the_manifest() -> None:
    assert parsed_papers_key(SHA) != parsed_papers_key("ffffffffffff")


#: Sentinels, so these tests keep working after a real version bump.
BUMPED_PARSER = "parser-bumped-for-test"
BUMPED_CHUNKER = "chunker-bumped-for-test"


def test_parsed_papers_key_tracks_the_parser_version(monkeypatch: pytest.MonkeyPatch) -> None:
    before = parsed_papers_key(SHA)
    monkeypatch.setattr(cache_keys, "PARSER_VERSION", BUMPED_PARSER)
    assert parsed_papers_key(SHA) != before


def test_parsed_papers_key_ignores_the_chunker_version(monkeypatch: pytest.MonkeyPatch) -> None:
    """A chunker change must not force a re-fetch and re-parse of 100 papers."""
    before = parsed_papers_key(SHA)
    monkeypatch.setattr(cache_keys, "CHUNKER_VERSION", BUMPED_CHUNKER)
    assert parsed_papers_key(SHA) == before


def test_chunk_set_key_tracks_both_version_stamps(
    monkeypatch: pytest.MonkeyPatch, resolved: dict[str, Any]
) -> None:
    params = _arm(resolved, "fixed")
    before = chunk_set_key(SHA, params)
    monkeypatch.setattr(cache_keys, "CHUNKER_VERSION", BUMPED_CHUNKER)
    after_chunker = chunk_set_key(SHA, params)
    assert after_chunker != before
    monkeypatch.setattr(cache_keys, "PARSER_VERSION", BUMPED_PARSER)
    assert chunk_set_key(SHA, params) != after_chunker


# --------------------------------------------------------------- index and run


def test_index_key_separates_the_embedding_arms(resolved: dict[str, Any]) -> None:
    chunk_set = chunk_set_key(SHA, _arm(resolved, "fixed"))
    arms = resolved["factors"]["embedding"]
    ids = {
        index_key(
            chunk_set,
            level["model_id"],
            level.get("model_revision", ""),
            level.get("adapter_id"),
            level.get("adapter_revision"),
        )
        for level in arms.values()
    }
    assert len(ids) == len(arms)


def test_index_key_tracks_the_adapter() -> None:
    """specter2 is the base encoder PLUS its proximity adapter. Loading the base
    alone is a different model, and the id has to say so."""
    chunk_set = "aaaaaaaaaaaa"
    with_adapter = index_key(
        chunk_set, "allenai/specter2_base", "rev", "allenai/specter2", "arev"
    )
    without = index_key(chunk_set, "allenai/specter2_base", "rev", None, None)
    assert with_adapter != without


def test_index_key_tracks_both_revisions() -> None:
    """A checkpoint or an adapter that moves under a fixed Hub id would otherwise
    re-embed the corpus into an index still wearing the old name."""
    base = index_key("aaaaaaaaaaaa", "m", "rev", "a", "arev")
    assert index_key("aaaaaaaaaaaa", "m", "other", "a", "arev") != base
    assert index_key("aaaaaaaaaaaa", "m", "rev", "a", "other") != base


def test_index_key_tracks_the_chunk_set() -> None:
    assert index_key("aaaaaaaaaaaa", "m", "rev") != index_key("bbbbbbbbbbbb", "m", "rev")


def test_run_key_is_order_independent(resolved: dict[str, Any]) -> None:
    shuffled = dict(reversed(list(resolved.items())))
    assert run_key(shuffled) == run_key(resolved)


def test_run_key_tracks_every_factor(resolved: dict[str, Any]) -> None:
    before = run_key(resolved)
    resolved["factors"]["rerank"]["on"]["enabled"] = False
    assert run_key(resolved) != before
