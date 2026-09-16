"""Four indexes, the keys that keep them apart, and resumability.

Built against MemoryStore rather than Chroma, except for one test that is about
Chroma: what is under test here is the pipeline's arithmetic -- which ids exist,
what gets re-embedded, what the census counts -- and a database would only make
those answers slower to obtain.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ragbench.cache_keys import index_key
from ragbench.chunking.pipeline import run_chunk
from ragbench.config import parsed_papers_dir, raw_xml_dir
from ragbench.index.pipeline import build_one_index, run_index, truncation_census
from ragbench.index.store import MemoryStore
from ragbench.ingest.jats import parse_article
from ragbench.ingest.manifest import manifest_sha, write_manifest
from ragbench.ingest.store import ArticleStore
from ragbench.types import Chunk, ManifestEntry

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


def chunk(index: int, text: str) -> Chunk:
    return Chunk(
        chunk_id=f"PMC1-{index:04d}",
        pmcid="PMC1",
        chunk_index=index,
        text=text,
        n_tokens=len(text.split()),
        char_start=index * 100,
        char_end=index * 100 + len(text),
        sections=("Results",),
        content_sha256="0" * 64,
    )


@pytest.fixture
def workspace(tmp_path: Path) -> tuple[dict[str, Any], Path]:
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

    resolved: dict[str, Any] = {
        "base": {
            "seed": 1,
            "chunking": {
                "target_tokens": 20,
                "overlap_tokens": 0,
                "tokenizer_id": "whitespace",
                "tokenizer_revision": "offline",
                "min_chunk_tokens": 0,
                "separators": ["\n\n", "\n", ". ", " ", ""],
                "chunk_abstract": False,
            },
            "embedding": {
                "normalize": True,
                "pooling": "cls",
                "max_seq_tokens": 32,
                "batch_size": 4,
                "dimension": 16,
            },
        },
        "corpus": {**POLICY, "manifest_sha": digest},
        "factors": {
            "chunking": {"fixed": {"strategy": "fixed"}, "recursive": {"strategy": "recursive"}},
            "embedding": {
                "bge": {
                    "model_id": "stand-in",
                    "model_revision": "offline-bge",
                    "adapter_id": None,
                    "adapter_revision": None,
                    "query_instruction": "Represent this sentence: ",
                },
                "specter2": {
                    "model_id": "stand-in",
                    "model_revision": "offline-specter2",
                    "adapter_id": "allenai/specter2",
                    "adapter_revision": "offline-adapter",
                    "query_instruction": "",
                },
            },
        },
    }
    run_chunk(resolved, manifest_path, data_root)
    return resolved, data_root


# ------------------------------------------------------------- the 2x2 design


def test_the_design_yields_exactly_four_indexes(
    workspace: tuple[dict[str, Any], Path],
) -> None:
    resolved, data_root = workspace
    reports = [
        build_one_index(resolved, chunking, embedding, data_root, store=MemoryStore())
        for chunking in resolved["factors"]["chunking"]
        for embedding in resolved["factors"]["embedding"]
    ]
    assert len(reports) == 4
    assert len({report["index_id"] for report in reports}) == 4


def test_changing_the_embedder_does_not_change_the_chunk_set(
    workspace: tuple[dict[str, Any], Path],
) -> None:
    """Invariant I2 one level up: the two factors meet in the index id, and they
    meet there as two opaque strings. Two chunk sets, four indexes -- never four
    chunk sets."""
    resolved, data_root = workspace
    reports = [
        build_one_index(resolved, chunking, embedding, data_root, store=MemoryStore())
        for chunking in resolved["factors"]["chunking"]
        for embedding in resolved["factors"]["embedding"]
    ]
    by_chunking: dict[str, set[str]] = {}
    for report in reports:
        by_chunking.setdefault(report["chunking_level"], set()).add(report["chunk_set_id"])
    assert all(len(ids) == 1 for ids in by_chunking.values())
    assert len({next(iter(ids)) for ids in by_chunking.values()}) == 2


def test_run_index_covers_the_cartesian_product(
    workspace: tuple[dict[str, Any], Path],
) -> None:
    resolved, data_root = workspace
    reports = run_index(resolved, data_root)
    assert {(r["chunking_level"], r["embedding_level"]) for r in reports} == {
        ("fixed", "bge"),
        ("fixed", "specter2"),
        ("recursive", "bge"),
        ("recursive", "specter2"),
    }


# ----------------------------------------------------------------- the key


def test_the_index_key_separates_every_part_of_an_arms_identity() -> None:
    base = index_key("chunks", "m", "rev", None, None)
    assert index_key("other", "m", "rev", None, None) != base
    assert index_key("chunks", "other", "rev", None, None) != base
    # A checkpoint that moves under a fixed id is a different index.
    assert index_key("chunks", "m", "other", None, None) != base
    # The adapter is half of specter2's identity, and so is its revision.
    assert index_key("chunks", "m", "rev", "adapter", "arev") != base
    assert index_key("chunks", "m", "rev", "adapter", "other") != index_key(
        "chunks", "m", "rev", "adapter", "arev"
    )


def test_the_index_key_is_order_independent() -> None:
    assert index_key("c", "m", "r", "a", "ar") == index_key("c", "m", "r", "a", "ar")


# ------------------------------------------------------------- resumability


def test_an_interrupted_build_resumes_where_it_stopped(
    workspace: tuple[dict[str, Any], Path],
) -> None:
    """Interrupting mid-embed and re-running must continue, not restart."""
    resolved, data_root = workspace
    store = MemoryStore()
    first = build_one_index(resolved, "fixed", "bge", data_root, store=store)
    assert first["vectors_written"] == first["n_chunks"]

    # Lose half the collection, as an interrupted write would.
    for identifier in list(store.vectors)[: len(store.vectors) // 2]:
        del store.vectors[identifier]
    missing = first["n_chunks"] - store.count()

    second = build_one_index(resolved, "fixed", "bge", data_root, store=store)
    assert second["vectors_written"] == missing
    assert second["vectors_reused"] == first["n_chunks"] - missing
    assert store.count() == first["n_chunks"]


def test_a_completed_index_re_runs_to_zero_work(
    workspace: tuple[dict[str, Any], Path],
) -> None:
    resolved, data_root = workspace
    store = MemoryStore()
    build_one_index(resolved, "fixed", "bge", data_root, store=store)
    again = build_one_index(resolved, "fixed", "bge", data_root, store=store)
    assert again["vectors_written"] == 0
    assert again["vectors_reused"] == again["n_chunks"]


def test_the_index_records_what_it_was_built_from(
    workspace: tuple[dict[str, Any], Path],
) -> None:
    """A run is self-describing: the metadata names the checkpoint, the adapter
    and both revisions, so an index cannot be mistaken for another arm's."""
    resolved, data_root = workspace
    report = build_one_index(resolved, "recursive", "specter2", data_root, store=MemoryStore())
    written = json.loads((Path(report["directory"]) / "index.json").read_text(encoding="utf-8"))
    assert written["adapter_id"] == "allenai/specter2"
    assert written["adapter_revision"] == "offline-adapter"
    assert written["model_revision"] == "offline-specter2"
    assert written["pooling"] == "cls"
    assert written["normalize"] is True


def test_chunk_metadata_travels_with_the_vector(
    workspace: tuple[dict[str, Any], Path],
) -> None:
    """Retrieval needs the character offsets to score span coverage (I5), so they
    have to be on the record, not re-derived from a chunk id."""
    resolved, data_root = workspace
    store = MemoryStore()
    build_one_index(resolved, "fixed", "bge", data_root, store=store)
    metadata = next(iter(store.metadatas.values()))
    assert {"pmcid", "chunk_index", "n_tokens", "char_start", "char_end"} <= set(metadata)


# ---------------------------------------------------------------- the census


def test_the_census_counts_the_chunks_the_encoder_would_cut() -> None:
    """max_seq_tokens includes [CLS] and [SEP], so the usable content budget is
    two smaller -- which is exactly where the chunker's target and the model's
    limit disagree."""
    chunks = [chunk(0, "a b c"), chunk(1, " ".join("w" * 1 for _ in range(12)))]
    census = truncation_census(chunks, lambda text: len(text.split()), max_seq_tokens=10)
    assert census["usable_content_tokens"] == 8
    assert census["n_truncated"] == 1
    assert census["worst_overflow_tokens"] == 4
    assert census["max_content_tokens"] == 12


def test_a_census_with_nothing_over_the_limit_reports_zero() -> None:
    census = truncation_census([chunk(0, "a b")], lambda t: len(t.split()), max_seq_tokens=512)
    assert census["n_truncated"] == 0
    assert census["share_truncated"] == 0.0
    assert census["worst_overflow_tokens"] == 0


def test_census_only_writes_nothing(workspace: tuple[dict[str, Any], Path]) -> None:
    """It loads a tokenizer, not an encoder, so it can answer the truncation
    question on a machine that cannot run the models."""
    resolved, data_root = workspace
    report = build_one_index(
        resolved, "fixed", "bge", data_root, store=MemoryStore(), census_only=True
    )
    assert report["census_only"] is True
    assert "truncation" in report
    assert not (data_root / "indexes" / report["index_id"] / "index.json").exists()


def test_an_unbuilt_chunk_set_is_a_clean_error(tmp_path: Path) -> None:
    resolved: dict[str, Any] = {
        "base": {
            "chunking": {
                "target_tokens": 20,
                "overlap_tokens": 0,
                "tokenizer_id": "whitespace",
                "tokenizer_revision": "offline",
                "min_chunk_tokens": 0,
                "separators": [" ", ""],
                "chunk_abstract": False,
            },
            "embedding": {"max_seq_tokens": 32, "dimension": 8},
        },
        "corpus": {"manifest_sha": "0" * 12},
        "factors": {
            "chunking": {"fixed": {"strategy": "fixed"}},
            "embedding": {"bge": {"model_id": "stand-in", "model_revision": "x"}},
        },
    }
    with pytest.raises(ValueError, match="run `ragbench chunk`"):
        build_one_index(resolved, "fixed", "bge", tmp_path, store=MemoryStore())
