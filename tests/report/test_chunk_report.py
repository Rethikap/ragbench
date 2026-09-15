"""Chunk-report statistics, offline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ragbench.chunking.pipeline import run_chunk
from ragbench.config import parsed_papers_dir, raw_xml_dir
from ragbench.ingest.jats import parse_article
from ragbench.ingest.manifest import manifest_sha, write_manifest
from ragbench.ingest.store import ArticleStore
from ragbench.report.chunks import SENTENCE_END, budget_fill, build_report, distribution
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


# ---------------------------------------------------------------- statistics


def test_distribution_reports_the_requested_percentiles() -> None:
    stats = distribution(list(range(1, 101)))
    assert stats["n"] == 100
    assert stats["min"] == 1
    assert stats["max"] == 100
    assert stats["median"] == pytest.approx(50.5)
    assert stats["p10"] < stats["p25"] < stats["median"] < stats["p75"] < stats["p90"]


def test_distribution_of_nothing_is_not_an_error() -> None:
    assert distribution([]) == {"n": 0}


# --------------------------------------------------------------- budget fill


def test_a_fill_never_exceeds_the_budget() -> None:
    """stop_at_overflow: chunks are added until one will not fit, never truncated."""
    result = budget_fill([300, 450, 700, 1100], budget=2000, seed=1, trials=500)
    assert result["tokens_used"]["max"] <= 2000


def test_fill_counts_are_plausible_for_uniform_chunks() -> None:
    result = budget_fill([500] * 20, budget=2000, seed=1, trials=200)
    assert result["chunks_per_budget"]["min"] == 4
    assert result["chunks_per_budget"]["max"] == 4


def test_smaller_chunks_mean_more_chunks_per_budget() -> None:
    coarse = budget_fill([500] * 50, budget=2000, seed=7, trials=400)
    fine = budget_fill([250] * 50, budget=2000, seed=7, trials=400)
    assert fine["chunks_per_budget"]["mean"] > coarse["chunks_per_budget"]["mean"]


def test_chunks_too_large_to_fit_are_counted() -> None:
    result = budget_fill([100, 2500, 3000], budget=2000, seed=1, trials=100)
    assert result["chunks_larger_than_budget"] == 2


def test_fill_is_deterministic_for_a_seed() -> None:
    first = budget_fill([300, 700, 450], budget=2000, seed=42, trials=200)
    second = budget_fill([300, 700, 450], budget=2000, seed=42, trials=200)
    assert first["histogram"] == second["histogram"]


# ----------------------------------------------------------- sentence ending


@pytest.mark.parametrize(
    "text",
    ["A sentence.", "A question?", "An exclamation!", 'He said "yes."', "[TABLE: Table 2]"],
)
def test_complete_endings_are_not_flagged(text: str) -> None:
    assert SENTENCE_END.search(text)


@pytest.mark.parametrize("text", ["cut off here", "the ratio was 1.2 and", "Methods"])
def test_incomplete_endings_are_flagged(text: str) -> None:
    assert not SENTENCE_END.search(text)


# ------------------------------------------------------------- end to end


@pytest.fixture
def built(tmp_path: Path) -> tuple[dict[str, Any], Path]:
    entry = ManifestEntry(
        pmcid=PMCID,
        doi=None,
        title="t",
        journal="j",
        pub_date="2021-06-03",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        source_url="https://example.invalid/",
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
                "tokenizer_revision": "offline-stand-in",
                "min_chunk_tokens": 0,
                "chunk_abstract": False,
                "separators": ["\n\n", "\n", ". ", " ", ""],
            },
            "retrieval": {
                "context_token_budget": 100,
                "budget_tokenizer_id": "whitespace",
                "budget_tokenizer_revision": "offline-stand-in",
                "fill_policy": "stop_at_overflow",
            },
        },
        "corpus": {**POLICY, "manifest_sha": digest},
        "factors": {
            "chunking": {"fixed": {"strategy": "fixed"}, "recursive": {"strategy": "recursive"}}
        },
    }
    run_chunk(resolved, manifest_path, data_root)
    return resolved, data_root


def test_report_covers_both_arms(built: tuple[dict[str, Any], Path]) -> None:
    resolved, data_root = built
    report = build_report(resolved, data_root, trials=200)
    assert [arm["level"] for arm in report["arms"]] == ["fixed", "recursive"]
    assert report["comparison"]["levels"] == ["fixed", "recursive"]
    assert len({arm["chunk_set_id"] for arm in report["arms"]}) == 2


def test_report_is_json_serialisable(built: tuple[dict[str, Any], Path]) -> None:
    import json

    resolved, data_root = built
    json.dumps(build_report(resolved, data_root, trials=50))


def test_every_arm_reports_the_required_sections(built: tuple[dict[str, Any], Path]) -> None:
    resolved, data_root = built
    for arm in build_report(resolved, data_root, trials=50)["arms"]:
        assert arm["canonical_tokens"]["n"] == arm["n_chunks"]
        assert arm["chunks_per_paper"]["n"] == arm["n_papers"]
        assert "budget_fill" in arm
        assert "mid_sentence" in arm
        assert "placeholders" in arm
        assert arm["placeholders"]["n_chunks_with_placeholder"] >= 1
        assert arm["over_target"] == 0
        assert set(arm["tiny"]) == {"under_10", "under_25", "under_50", "under_100"}
        for row in arm["tiny"].values():
            assert row["n"] == row["final_chunk_of_paper"] + row["mid_body"]


def test_no_arm_exceeds_the_token_target(built: tuple[dict[str, Any], Path]) -> None:
    """The measurement the 513-token defect would have shown.

    A chunk longer than target_tokens is not a rounding artefact: it is one arm
    quietly getting a larger unit of retrieval than the other, which is the
    thing the chunking factor is supposed to be varying deliberately.
    """
    from ragbench.chunking.pipeline import load_chunks

    resolved, data_root = built
    target = resolved["base"]["chunking"]["target_tokens"]
    for arm in build_report(resolved, data_root, trials=50)["arms"]:
        for chunk in load_chunks(arm["directory"]):
            assert chunk.n_tokens <= target


def test_unbuilt_chunk_set_is_a_clean_error(tmp_path: Path) -> None:
    resolved: dict[str, Any] = {
        "base": {
            "seed": 1,
            "chunking": {
                "target_tokens": 20,
                "overlap_tokens": 0,
                "tokenizer_id": "whitespace",
                "tokenizer_revision": "offline-stand-in",
                "min_chunk_tokens": 0,
                "chunk_abstract": False,
                "separators": [" ", ""],
            },
            "retrieval": {
                "context_token_budget": 100,
                "budget_tokenizer_id": "whitespace",
                "budget_tokenizer_revision": "offline-stand-in",
                "fill_policy": "stop_at_overflow",
            },
        },
        "corpus": {"manifest_sha": "0" * 12},
        "factors": {"chunking": {"fixed": {"strategy": "fixed"}}},
    }
    with pytest.raises(ValueError, match="run `ragbench chunk`"):
        build_report(resolved, tmp_path, trials=10)
