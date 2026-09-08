"""Config resolution, run ids, and the self-describing run directory."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from ragbench.config import (
    RESOLVED_FILENAME,
    ConfigError,
    config_digest,
    dump_resolved,
    resolve_config,
    run_dir,
)
from ragbench.hashing import canonical_json, stable_hash

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_CONFIG = REPO_ROOT / "configs" / "base.yaml"


def _write_config_set(directory: Path, schema_version: int = 1) -> Path:
    base = directory / "base.yaml"
    base.write_text(f"schema_version: {schema_version}\nseed: 1\n", encoding="utf-8")
    (directory / "corpus.yaml").write_text("corpus:\n  name: tiny\n", encoding="utf-8")
    (directory / "factors.yaml").write_text(
        "factors:\n  rerank:\n    off:\n      enabled: false\n", encoding="utf-8"
    )
    return base


# --------------------------------------------------------------------- resolution


def test_resolve_reads_all_three_files() -> None:
    resolved = resolve_config(BASE_CONFIG)
    assert set(resolved) == {"schema_version", "base", "corpus", "factors"}
    assert resolved["corpus"]["db"] == "pmc"
    assert set(resolved["factors"]) == {"chunking", "embedding", "rerank"}


def test_factors_describe_a_2x2x2_design() -> None:
    factors = resolve_config(BASE_CONFIG)["factors"]
    assert math.prod(len(levels) for levels in factors.values()) == 8


def test_missing_sibling_is_reported(tmp_path: Path) -> None:
    base = tmp_path / "base.yaml"
    base.write_text("schema_version: 1\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="corpus.yaml"):
        resolve_config(base)


def test_schema_version_mismatch_is_rejected(tmp_path: Path) -> None:
    base = _write_config_set(tmp_path, schema_version=99)
    with pytest.raises(ConfigError, match="schema_version"):
        resolve_config(base)


def test_missing_top_level_key_is_reported(tmp_path: Path) -> None:
    _write_config_set(tmp_path)
    (tmp_path / "factors.yaml").write_text("chunking: {}\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="missing top-level 'factors:'"):
        resolve_config(tmp_path / "base.yaml")


def test_absent_file_is_reported(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="config file not found"):
        resolve_config(tmp_path / "nope.yaml")


# --------------------------------------------------------------------- run ids


def test_digest_is_order_independent() -> None:
    resolved = resolve_config(BASE_CONFIG)
    shuffled = dict(reversed(list(resolved.items())))
    assert config_digest(shuffled) == config_digest(resolved)


def test_run_dir_is_named_after_the_digest(tmp_path: Path) -> None:
    resolved = resolve_config(BASE_CONFIG)
    assert run_dir(resolved, tmp_path).name == config_digest(resolved)


def test_freezing_the_manifest_changes_the_run_id() -> None:
    """Invariant I4: pinning the corpus must not silently reuse an old run."""
    resolved = resolve_config(BASE_CONFIG)
    before = config_digest(resolved)
    resolved["corpus"]["manifest_sha"] = "0123456789ab"
    assert config_digest(resolved) != before


def test_changing_the_budget_changes_the_run_id() -> None:
    resolved = resolve_config(BASE_CONFIG)
    before = config_digest(resolved)
    resolved["base"]["retrieval"]["context_token_budget"] = 4000
    assert config_digest(resolved) != before


# --------------------------------------------------------------------- dump


def test_dumped_config_reproduces_the_run_id(tmp_path: Path) -> None:
    """A run directory is self-describing: its name is re-derivable from the
    file it contains, without trusting the name."""
    resolved = resolve_config(BASE_CONFIG)
    directory = run_dir(resolved, tmp_path)
    target = dump_resolved(resolved, directory)

    assert target.name == RESOLVED_FILENAME
    assert target.read_bytes() == canonical_json(resolved).encode("utf-8")
    assert stable_hash(json.loads(target.read_text(encoding="utf-8"))) == directory.name


def test_dump_is_idempotent(tmp_path: Path) -> None:
    resolved = resolve_config(BASE_CONFIG)
    directory = run_dir(resolved, tmp_path)
    first = dump_resolved(resolved, directory).read_bytes()
    second = dump_resolved(resolved, directory).read_bytes()
    assert first == second
