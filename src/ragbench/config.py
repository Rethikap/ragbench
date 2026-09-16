"""Config resolution and run-directory derivation.

`--config` points at ``configs/base.yaml``; its siblings ``corpus.yaml``,
``factors.yaml`` and ``gold.yaml`` are read from the same directory. The four
files are one logical config split for editing convenience, and a run id is only
meaningful if all of them are pinned -- so they are resolved together, once, at
CLI entry.

The resolved mapping is the sole input to the run id, which means changing any
of them (including freezing ``manifest_sha`` or ``gold_set_sha``) yields a
different run directory rather than silently overwriting incomparable results.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .cache_keys import parsed_papers_key, run_key
from .constants import CONFIG_SCHEMA_VERSION
from .hashing import canonical_json

CORPUS_FILENAME = "corpus.yaml"
FACTORS_FILENAME = "factors.yaml"
GOLD_FILENAME = "gold.yaml"
MANIFEST_FILENAME = "corpus_manifest.jsonl"
RESOLVED_FILENAME = "resolved_config.json"
DEFAULT_RUNS_ROOT = Path("runs")
DEFAULT_DATA_ROOT = Path("data")


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


def _validate_factors(factors: dict[str, Any], path: Path) -> dict[str, Any]:
    """Reject non-string factor or level names.

    YAML 1.1 reads bare ``on``/``off``/``yes``/``no`` as booleans, so ``on:`` as a
    level name silently becomes ``True``. Level names reach run ids and reports,
    and a bool key sorted alongside a string key makes canonical_json raise. Fail
    loudly at load time instead.
    """
    for factor, levels in factors.items():
        if not isinstance(factor, str):
            raise ConfigError(f"{path}: factor name {factor!r} is not a string; quote it")
        if not isinstance(levels, dict):
            raise ConfigError(f"{path}: factor '{factor}' must map level names to parameters")
        for level in levels:
            if not isinstance(level, str):
                raise ConfigError(
                    f"{path}: factor '{factor}' has non-string level name {level!r}. "
                    'YAML 1.1 reads bare on/off/yes/no as booleans -- quote it as "on".'
                )
    return factors


def resolve_config(base_path: Path) -> dict[str, Any]:
    """Load base + corpus + factors + gold into one mapping.

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
    gold_path = directory / GOLD_FILENAME
    return {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "base": base,
        "corpus": _section(_load_yaml(corpus_path), "corpus", corpus_path),
        "factors": _validate_factors(
            _section(_load_yaml(factors_path), "factors", factors_path), factors_path
        ),
        # The evaluation set is pinned into the run id for the same reason the
        # corpus is: results scored against a different set of questions are not
        # the same results, however identical every other setting.
        "gold": _section(_load_yaml(gold_path), "gold", gold_path),
    }


def run_dir(resolved: dict[str, Any], root: Path = DEFAULT_RUNS_ROOT) -> Path:
    """Per-run output directory, keyed on the whole resolved config."""
    return Path(root) / run_key(resolved)


def parsed_papers_dir(manifest_sha: str, root: Path = DEFAULT_DATA_ROOT) -> Path:
    """Parsed-paper cache: shared by all 8 runs, so it lives under data/ rather
    than inside any one run directory."""
    return Path(root) / "parsed" / parsed_papers_key(manifest_sha)


def chunk_set_dir(chunk_set_id: str, root: Path = DEFAULT_DATA_ROOT) -> Path:
    """One chunk set. There are exactly two of these across the 8 runs."""
    return Path(root) / "chunks" / chunk_set_id


def index_dir(index_id: str, root: Path = DEFAULT_DATA_ROOT) -> Path:
    """One vector index. There are exactly four across the 8 runs -- two chunk
    sets times two embedding arms -- and the id says which."""
    return Path(root) / "indexes" / index_id


def gold_candidates_dir(manifest_sha: str, root: Path = DEFAULT_DATA_ROOT) -> Path:
    """Working directory for drafted candidates, before any are verified.

    Under ``data/`` because it is regenerable from the seed and the drafter; the
    *verified* set is not, and lands in ``configs/`` instead.
    """
    return Path(root) / "gold" / parsed_papers_key(manifest_sha)


def raw_xml_dir(root: Path = DEFAULT_DATA_ROOT) -> Path:
    """Raw JATS cache.

    Keyed by nothing but the PMCID: the bytes NCBI returns for a frozen PMCID do
    not depend on our parser, so a PARSER_VERSION bump must re-parse but must not
    re-download.
    """
    return Path(root) / "raw_jats"


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
