"""The frozen corpus manifest.

Selection runs once and writes ``configs/corpus_manifest.jsonl``; its digest is
pinned into ``configs/corpus.yaml`` as ``manifest_sha``. From that commit the
corpus is immutable and every later stage reads the manifest instead of querying
NCBI, because PMC grows continuously and an unpinned query is not reproducible.

The manifest lives in ``configs/`` rather than ``data/``: everything under
``data/`` is declared regenerable from configs, and the manifest is precisely the
artefact that is not.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..hashing import stable_hash
from ..jsonl import read_jsonl, write_jsonl
from ..types import ManifestEntry

UNFROZEN = "unfrozen"
_SHA_LINE = re.compile(r"^(\s*manifest_sha:\s*)(\S+)(.*)$", re.MULTILINE)


class ManifestError(Exception):
    """The manifest is missing, malformed, or does not match the frozen digest."""


def sort_entries(entries: list[ManifestEntry]) -> list[ManifestEntry]:
    """Canonical order: ascending numeric PMCID.

    Selection order is seeded and deliberately spread across the date range, but
    the stored order must not depend on it -- otherwise the same 100 papers could
    produce two different digests.
    """
    return sorted(entries, key=lambda entry: int(entry.pmcid.removeprefix("PMC")))


def manifest_sha(entries: list[ManifestEntry]) -> str:
    """Digest of the manifest's *content*, not its file bytes.

    Sorts before hashing rather than trusting the caller to have done it. The
    alternative cost a real bug: selection hashed its keep-order while
    write_manifest stored PMCID order, so the frozen digest described an
    arrangement the manifest file did not have.

    Hashing records rather than file bytes means reformatting the file, or
    writing it on another platform, cannot change the corpus identity.
    """
    return stable_hash([entry.to_dict() for entry in sort_entries(entries)])


def write_manifest(path: Path, entries: list[ManifestEntry]) -> int:
    return write_jsonl(Path(path), [entry.to_dict() for entry in sort_entries(entries)])


def read_manifest(path: Path) -> list[ManifestEntry]:
    path = Path(path)
    if not path.is_file():
        raise ManifestError(
            f"corpus manifest not found: {path}. Run `ragbench ingest --select-corpus` "
            "once to build and freeze it."
        )
    entries = [ManifestEntry.from_dict(record) for record in read_jsonl(path)]
    if not entries:
        raise ManifestError(f"corpus manifest is empty: {path}")
    return entries


def verify_frozen(path: Path, expected_sha: str) -> list[ManifestEntry]:
    """Load the manifest and check it against the sha pinned in corpus.yaml."""
    if not expected_sha or expected_sha == UNFROZEN:
        raise ManifestError(
            "corpus.yaml has manifest_sha: unfrozen. The corpus must be frozen "
            "before anything downstream may run; use `ragbench ingest --select-corpus`."
        )
    entries = read_manifest(path)
    found = manifest_sha(entries)
    if found != expected_sha:
        raise ManifestError(
            f"manifest digest mismatch: {path} hashes to {found}, but corpus.yaml pins "
            f"{expected_sha}. The frozen corpus has been altered."
        )
    return entries


def freeze_sha(corpus_yaml: Path, sha: str) -> None:
    """Write ``manifest_sha`` back into corpus.yaml.

    A line-level substitution rather than a YAML round-trip: dumping the parsed
    document would silently discard every comment in the file, and those comments
    are the record of why the corpus is defined the way it is.
    """
    corpus_yaml = Path(corpus_yaml)
    text = corpus_yaml.read_text(encoding="utf-8")
    if not _SHA_LINE.search(text):
        raise ManifestError(f"{corpus_yaml}: no 'manifest_sha:' line to freeze")
    updated = _SHA_LINE.sub(lambda m: f"{m.group(1)}{sha}{m.group(3)}", text, count=1)
    corpus_yaml.write_text(updated, encoding="utf-8", newline="")
