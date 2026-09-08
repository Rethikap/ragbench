"""Config resolution and run-directory derivation.

`--config` points at ``configs/base.yaml``; its siblings ``corpus.yaml`` and
``factors.yaml`` are read from the same directory. The three files are one
logical config split for editing convenience, and a run id is only meaningful if
all three are pinned -- so they are resolved together, once, at CLI entry.

The resolved mapping is the sole input to the run id, which means changing any
of them (including freezing ``manifest_sha``) yields a different run directory
rather than silently overwriting incomparable results.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .constants import CONFIG_SCHEMA_VERSION
from .hashing import canonical_json, stable_hash

CORPUS_FILENAME = "corpus.yaml"
FACTORS_FILENAME = "factors.yaml"
RESOLVED_FILENAME = "resolved_config.json"
DEFAULT_RUNS_ROOT = Path("runs")


class ConfigError(Exception):
    """Malformed, missing or mismatched config.

    Raised instead of letting yaml/OSError escape, so the CLI can turn it into a
    one-line message and an exit code rather than a traceback.
    """


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ConfigError(f"config file not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: expected a mapping at the top level")
    return data


def _section(data: dict[str, Any], key: str, path: Path) -> dict[str, Any]:
    try:
        section = data[key]
    except KeyError:
        raise ConfigError(f"{path}: missing top-level '{key}:' key") from None
    if not isinstance(section, dict):
        raise ConfigError(f"{path}: '{key}:' must be a mapping")
    return section


def resolve_config(base_path: Path) -> dict[str, Any]:
    """Load base + corpus + factors into one mapping.

    No merging of factor levels happens here: this is the *shared* config that
    all 8 runs agree on. Expanding the Cartesian product is the caller's job.
    """
    base_path = Path(base_path)
    base = _load_yaml(base_path)

    found = base.get("schema_version")
    if found != CONFIG_SCHEMA_VERSION:
        raise ConfigError(
            f"{base_path}: schema_version is {found!r}, expected {CONFIG_SCHEMA_VERSION}"
        )

    directory = base_path.parent
    corpus_path = directory / CORPUS_FILENAME
    factors_path = directory / FACTORS_FILENAME
    return {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "base": base,
        "corpus": _section(_load_yaml(corpus_path), "corpus", corpus_path),
        "factors": _section(_load_yaml(factors_path), "factors", factors_path),
    }


def config_digest(resolved: dict[str, Any]) -> str:
    """Run id: a short digest of the resolved config.

    Order-independent, because :func:`~ragbench.hashing.canonical_json` sorts
    keys -- reordering a YAML mapping must not invent a new run.
    """
    return stable_hash(resolved)


def run_dir(resolved: dict[str, Any], root: Path = DEFAULT_RUNS_ROOT) -> Path:
    return Path(root) / config_digest(resolved)


def dump_resolved(resolved: dict[str, Any], directory: Path) -> Path:
    """Write the resolved config next to the outputs it describes.

    Deliberately written as canonical JSON -- the exact bytes that were hashed --
    so the directory name can be re-derived from the file it contains, and a run
    is self-describing without trusting the name.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / RESOLVED_FILENAME
    target.write_text(canonical_json(resolved), encoding="utf-8", newline="")
    return target
