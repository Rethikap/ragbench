"""Manifest identity and the one-time freeze."""

from __future__ import annotations

from pathlib import Path

import pytest

from ragbench.ingest.manifest import (
    ManifestError,
    freeze_sha,
    manifest_sha,
    read_manifest,
    sort_entries,
    write_manifest,
)
from ragbench.types import ManifestEntry

CORPUS_YAML = Path(__file__).resolve().parents[2] / "configs" / "corpus.yaml"


def _entry(pmcid: str) -> ManifestEntry:
    return ManifestEntry(
        pmcid=pmcid,
        doi=None,
        title=f"Paper {pmcid}",
        journal="Journal",
        pub_date="2021-06-03",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        source_url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/",
        article_type="research-article",
        license_text="CC BY 4.0",
    )


ENTRIES = [_entry("PMC30"), _entry("PMC4"), _entry("PMC100")]


def test_entries_sort_by_numeric_pmcid() -> None:
    """Lexicographic order would put PMC100 before PMC30."""
    assert [e.pmcid for e in sort_entries(ENTRIES)] == ["PMC4", "PMC30", "PMC100"]


def test_digest_ignores_selection_order() -> None:
    """Note the absence of sort_entries: the digest must not depend on callers."""
    assert manifest_sha(ENTRIES) == manifest_sha(list(reversed(ENTRIES)))


def test_digest_describes_what_actually_gets_written(tmp_path: Path) -> None:
    """Regression: selection froze its keep-order digest while write_manifest
    stored PMCID order, so the pinned sha described a file that never existed."""
    path = tmp_path / "corpus_manifest.jsonl"
    unsorted = list(reversed(ENTRIES))
    frozen = manifest_sha(unsorted)
    write_manifest(path, unsorted)
    assert manifest_sha(read_manifest(path)) == frozen


def test_digest_changes_when_a_paper_changes() -> None:
    altered = [_entry("PMC30"), _entry("PMC4"), _entry("PMC101")]
    assert manifest_sha(sort_entries(altered)) != manifest_sha(sort_entries(ENTRIES))


def test_manifest_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "corpus_manifest.jsonl"
    assert write_manifest(path, ENTRIES) == 3
    assert read_manifest(path) == sort_entries(ENTRIES)


def test_written_manifest_is_byte_stable(tmp_path: Path) -> None:
    first = tmp_path / "a.jsonl"
    second = tmp_path / "b.jsonl"
    write_manifest(first, ENTRIES)
    write_manifest(second, list(reversed(ENTRIES)))
    assert first.read_bytes() == second.read_bytes()
    assert b"\r\n" not in first.read_bytes()


def test_reading_a_missing_manifest_explains_how_to_build_it(tmp_path: Path) -> None:
    with pytest.raises(ManifestError, match="--select-corpus"):
        read_manifest(tmp_path / "absent.jsonl")


def test_freeze_preserves_comments(tmp_path: Path) -> None:
    """A YAML round-trip would discard every comment; this is why freeze_sha
    does a line substitution instead."""
    target = tmp_path / "corpus.yaml"
    target.write_text(CORPUS_YAML.read_text(encoding="utf-8"), encoding="utf-8", newline="")
    before = target.read_text(encoding="utf-8")

    freeze_sha(target, "abcdef123456")
    after = target.read_text(encoding="utf-8")

    assert "manifest_sha: abcdef123456" in after
    assert "unfrozen" not in after.split("manifest_sha:")[1].splitlines()[0]
    comments_before = [line for line in before.splitlines() if line.strip().startswith("#")]
    comments_after = [line for line in after.splitlines() if line.strip().startswith("#")]
    assert comments_before == comments_after
    assert len(before.splitlines()) == len(after.splitlines())


def test_freeze_requires_the_key_to_exist(tmp_path: Path) -> None:
    target = tmp_path / "corpus.yaml"
    target.write_text("corpus:\n  name: x\n", encoding="utf-8")
    with pytest.raises(ManifestError, match="no 'manifest_sha:' line"):
        freeze_sha(target, "abcdef123456")
