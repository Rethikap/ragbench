"""Chunk-set construction, caching, and invariant I2 at the pipeline level."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ragbench.chunking.pipeline import chunk_one_arm, load_chunks, run_chunk
from ragbench.config import parsed_papers_dir, raw_xml_dir
from ragbench.ingest.jats import parse_article
from ragbench.ingest.manifest import manifest_sha, write_manifest
from ragbench.ingest.store import ArticleStore
from ragbench.types import ManifestEntry

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "sample_article.xml"
PMCID = "PMC9999001"

POLICY = {
    "drop_references": True,
    "drop_figure_captions": True,
    "drop_bibliographic_xrefs": True,
    "table_policy": "placeholder",
    "equation_policy": "placeholder",
    "keep_abstract": True,
}

CHUNKING = {
    "target_tokens": 20,
    "overlap_tokens": 0,
    "tokenizer_id": "whitespace",
    "min_chunk_tokens": 0,
    "separators": ["\n\n", "\n", ". ", " ", ""],
}

FACTORS = {
    "chunking": {"fixed": {"strategy": "fixed"}, "recursive": {"strategy": "recursive"}},
    "embedding": {
        "bge": {"name": "bge_base", "model_id": "BAAI/bge-base-en-v1.5", "adapter_id": None},
        "specter2": {
            "name": "specter2",
            "model_id": "allenai/specter2_base",
            "adapter_id": "allenai/specter2",
        },
    },
}


@pytest.fixture
def workspace(tmp_path: Path) -> tuple[dict[str, Any], Path, Path]:
    entry = ManifestEntry(
        pmcid=PMCID,
        doi=None,
        title="A Controlled Study of Test Biomarkers",
        journal="Journal of Test Biomarkers",
        pub_date="2021-06-03",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        source_url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{PMCID}/",
        article_type="research-article",
        license_text="CC BY 4.0",
    )
    manifest_path = tmp_path / "corpus_manifest.jsonl"
    write_manifest(manifest_path, [entry])
    digest = manifest_sha([entry])

    data_root = tmp_path / "data"
    store = ArticleStore(raw_xml_dir(data_root), parsed_papers_dir(digest, data_root))
    store.write_parsed(parse_article(FIXTURE.read_bytes(), POLICY))

    resolved = {
        "base": {"chunking": dict(CHUNKING), "seed": 1},
        "corpus": {**POLICY, "manifest_sha": digest},
        "factors": {k: {kk: dict(vv) for kk, vv in v.items()} for k, v in FACTORS.items()},
    }
    return resolved, manifest_path, data_root


# ------------------------------------------------------------- invariant I2


def test_changing_the_embedding_factor_does_not_change_the_chunk_set(
    workspace: tuple[dict[str, Any], Path, Path],
) -> None:
    resolved, manifest_path, data_root = workspace
    before = chunk_one_arm(resolved, "fixed", manifest_path, data_root)["chunk_set_id"]

    resolved["factors"]["embedding"] = {"only": {"model_id": "some/other-model"}}
    resolved["base"]["embedding"] = {"model_id": "some/other-model"}
    after = chunk_one_arm(resolved, "fixed", manifest_path, data_root)["chunk_set_id"]

    assert after == before


def test_the_design_yields_exactly_two_chunk_sets(
    workspace: tuple[dict[str, Any], Path, Path],
) -> None:
    resolved, manifest_path, data_root = workspace
    reports = run_chunk(resolved, manifest_path, data_root)
    identifiers = {report["chunk_set_id"] for report in reports}
    assert len(reports) == 2
    assert len(identifiers) == 2


# ----------------------------------------------------------------- caching


def test_second_build_is_reused_not_recomputed(
    workspace: tuple[dict[str, Any], Path, Path],
) -> None:
    resolved, manifest_path, data_root = workspace
    first = chunk_one_arm(resolved, "recursive", manifest_path, data_root)
    second = chunk_one_arm(resolved, "recursive", manifest_path, data_root)
    assert first["reused"] is False
    assert second["reused"] is True
    assert second["n_chunks"] == first["n_chunks"]


def test_changing_a_chunking_parameter_makes_a_new_chunk_set(
    workspace: tuple[dict[str, Any], Path, Path],
) -> None:
    resolved, manifest_path, data_root = workspace
    before = chunk_one_arm(resolved, "fixed", manifest_path, data_root)["chunk_set_id"]
    resolved["base"]["chunking"]["target_tokens"] = 30
    after = chunk_one_arm(resolved, "fixed", manifest_path, data_root)["chunk_set_id"]
    assert after != before


# ------------------------------------------------------------------ output


def test_chunks_index_the_parsed_body(
    workspace: tuple[dict[str, Any], Path, Path],
) -> None:
    resolved, manifest_path, data_root = workspace
    report = chunk_one_arm(resolved, "recursive", manifest_path, data_root)
    store = ArticleStore(
        raw_xml_dir(data_root), parsed_papers_dir(resolved["corpus"]["manifest_sha"], data_root)
    )
    paper = store.read_parsed(PMCID)
    chunks = load_chunks(report["directory"])

    assert chunks
    for chunk in chunks:
        assert paper.body[chunk.char_start : chunk.char_end] == chunk.text
        assert chunk.pmcid == PMCID
        assert chunk.n_tokens > 0
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_recursive_records_which_separator_fired(
    workspace: tuple[dict[str, Any], Path, Path],
) -> None:
    resolved, manifest_path, data_root = workspace
    report = chunk_one_arm(resolved, "recursive", manifest_path, data_root)
    assert report["separator_levels"]
    assert set(report["separator_levels"]) <= {"whole", "0", "1", "2", "3", "4"}


def test_fixed_records_no_separator_levels(
    workspace: tuple[dict[str, Any], Path, Path],
) -> None:
    resolved, manifest_path, data_root = workspace
    report = chunk_one_arm(resolved, "fixed", manifest_path, data_root)
    assert set(report["separator_levels"]) <= {"whole"}


def test_missing_parsed_papers_are_reported(
    workspace: tuple[dict[str, Any], Path, Path],
) -> None:
    resolved, manifest_path, data_root = workspace
    store = ArticleStore(
        raw_xml_dir(data_root), parsed_papers_dir(resolved["corpus"]["manifest_sha"], data_root)
    )
    store.parsed_path(PMCID).unlink()
    with pytest.raises(ValueError, match="run `ragbench ingest`"):
        chunk_one_arm(resolved, "fixed", manifest_path, data_root)
