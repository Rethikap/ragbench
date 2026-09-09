"""Ingest resumability and idempotence -- entirely offline.

Every test here runs with :class:`NcbiClient` replaced by a landmine, so a test
passing is positive evidence that a warm cache does no network I/O at all.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ragbench.config import raw_xml_dir
from ragbench.ingest.manifest import ManifestError, manifest_sha, write_manifest
from ragbench.ingest.pipeline import ROLLUP_FILENAME, run_ingest
from ragbench.jsonl import read_jsonl
from ragbench.types import ManifestEntry

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "sample_article.xml"
PMCID = "PMC9999001"
OTHER = "PMC9999002"

POLICY = {
    "drop_references": True,
    "drop_figure_captions": True,
    "drop_bibliographic_xrefs": True,
    "table_policy": "placeholder",
    "equation_policy": "placeholder",
    "keep_abstract": True,
}


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def landmine(*args: object, **kwargs: object) -> None:
        raise AssertionError("ingest opened a network client although the cache was warm")

    monkeypatch.setattr("ragbench.ingest.pipeline.NcbiClient", landmine)


def _entry(pmcid: str) -> ManifestEntry:
    return ManifestEntry(
        pmcid=pmcid,
        doi="10.1234/test.2021.001",
        title="A Controlled Study of Test Biomarkers",
        journal="Journal of Test Biomarkers",
        pub_date="2021-06-03",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        source_url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/",
        article_type="research-article",
        license_text="Open access under the CC BY 4.0 license.",
    )


@pytest.fixture
def workspace(tmp_path: Path) -> tuple[dict[str, Any], Path, Path]:
    """A frozen one-paper corpus with its raw JATS already cached."""
    entries = [_entry(PMCID)]
    manifest_path = tmp_path / "corpus_manifest.jsonl"
    write_manifest(manifest_path, entries)

    data_root = tmp_path / "data"
    raw_directory = raw_xml_dir(data_root)
    raw_directory.mkdir(parents=True)
    (raw_directory / f"{PMCID}.xml").write_bytes(FIXTURE.read_bytes())

    resolved = {"corpus": {**POLICY, "manifest_sha": manifest_sha(entries)}}
    return resolved, manifest_path, data_root


# ------------------------------------------------------------- idempotence


def test_first_run_works_second_run_does_not(
    workspace: tuple[dict[str, Any], Path, Path],
) -> None:
    resolved, manifest_path, data_root = workspace

    first = run_ingest(resolved, manifest_path, data_root)
    assert (first["n_parsed"], first["n_cached"], first["n_fetched"]) == (1, 0, 0)

    second = run_ingest(resolved, manifest_path, data_root)
    assert (second["n_parsed"], second["n_cached"], second["n_fetched"]) == (0, 1, 0)
    assert second["failures"] == []


def test_interrupted_run_resumes_rather_than_restarting(tmp_path: Path) -> None:
    entries = [_entry(PMCID), _entry(OTHER)]
    manifest_path = tmp_path / "corpus_manifest.jsonl"
    write_manifest(manifest_path, entries)

    data_root = tmp_path / "data"
    raw_directory = raw_xml_dir(data_root)
    raw_directory.mkdir(parents=True)
    original = FIXTURE.read_bytes()
    (raw_directory / f"{PMCID}.xml").write_bytes(original)
    (raw_directory / f"{OTHER}.xml").write_bytes(original.replace(b"PMC9999001", b"PMC9999002"))

    resolved = {"corpus": {**POLICY, "manifest_sha": manifest_sha(entries)}}

    first = run_ingest(resolved, manifest_path, data_root)
    assert first["n_parsed"] == 2

    # Simulate an interruption after the first paper: drop the second's output.
    parsed_directory = first["parsed_dir"]
    (parsed_directory / f"{OTHER}.json").unlink()

    resumed = run_ingest(resolved, manifest_path, data_root)
    assert (resumed["n_parsed"], resumed["n_cached"]) == (1, 1)


def test_parsed_output_is_byte_identical_across_runs(
    workspace: tuple[dict[str, Any], Path, Path],
) -> None:
    resolved, manifest_path, data_root = workspace
    first = run_ingest(resolved, manifest_path, data_root)
    before = (first["parsed_dir"] / f"{PMCID}.json").read_bytes()

    (first["parsed_dir"] / f"{PMCID}.json").unlink()
    run_ingest(resolved, manifest_path, data_root)
    assert (first["parsed_dir"] / f"{PMCID}.json").read_bytes() == before


# ------------------------------------------------------------------- output


def test_rollup_is_written_and_sorted(workspace: tuple[dict[str, Any], Path, Path]) -> None:
    resolved, manifest_path, data_root = workspace
    report = run_ingest(resolved, manifest_path, data_root)
    rollup = report["parsed_dir"] / ROLLUP_FILENAME
    assert rollup.is_file()
    records = list(read_jsonl(rollup))
    assert [record["pmcid"] for record in records] == sorted(r["pmcid"] for r in records)


def test_stats_are_reported_per_paper(workspace: tuple[dict[str, Any], Path, Path]) -> None:
    resolved, manifest_path, data_root = workspace
    report = run_ingest(resolved, manifest_path, data_root)
    row = report["stats"][0]
    assert row["pmcid"] == PMCID
    assert row["tables_placeholdered"] == 1
    assert row["equations_placeholdered"] == 1
    assert row["sections_dropped"] == 1
    assert row["retained_chars"] > 0


# ---------------------------------------------------------- invariant I4


def test_unfrozen_corpus_is_refused(workspace: tuple[dict[str, Any], Path, Path]) -> None:
    resolved, manifest_path, data_root = workspace
    resolved["corpus"]["manifest_sha"] = "unfrozen"
    with pytest.raises(ManifestError, match="unfrozen"):
        run_ingest(resolved, manifest_path, data_root)


def test_tampered_manifest_is_detected(workspace: tuple[dict[str, Any], Path, Path]) -> None:
    resolved, manifest_path, data_root = workspace
    write_manifest(manifest_path, [_entry(PMCID), _entry(OTHER)])
    with pytest.raises(ManifestError, match="digest mismatch"):
        run_ingest(resolved, manifest_path, data_root)


def test_missing_manifest_is_a_clean_error(
    workspace: tuple[dict[str, Any], Path, Path],
) -> None:
    resolved, manifest_path, data_root = workspace
    manifest_path.unlink()
    with pytest.raises(ManifestError, match="not found"):
        run_ingest(resolved, manifest_path, data_root)
