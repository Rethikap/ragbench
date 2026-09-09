"""Live NCBI behaviour. Deselected by default; run with `pytest -m network`.

These pin the two API facts the selection design rests on, so that if NCBI ever
changes them the suite says so instead of the corpus quietly becoming wrong.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ragbench.config import resolve_config
from ragbench.ingest.jats import read_metadata
from ragbench.ingest.ncbi import ESEARCH_CAP, NcbiClient, NcbiError
from ragbench.ingest.select import canonical_candidates

pytestmark = pytest.mark.network

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_CONFIG = REPO_ROOT / "configs" / "base.yaml"


@pytest.fixture(scope="module")
def corpus() -> dict:
    return resolve_config(BASE_CONFIG)["corpus"]


def test_whole_range_exceeds_the_esearch_cap(corpus: dict) -> None:
    """The premise of year-partitioning: the query cannot be paged directly."""
    client = NcbiClient()
    total = client.count(corpus["query"], corpus["date_from"], corpus["date_to"])
    assert total > ESEARCH_CAP


def test_an_oversized_window_is_refused_not_truncated(corpus: dict) -> None:
    client = NcbiClient()
    with pytest.raises(NcbiError, match="above the"):
        client.search_window(corpus["query"], corpus["date_from"], corpus["date_to"])


def test_year_partition_enumerates_the_whole_query(corpus: dict) -> None:
    """Seven windows must sum to the whole-range count: no loss, no overlap."""
    survey = canonical_candidates(NcbiClient(), corpus)
    assert survey["partition_is_exact"]
    assert survey["unique_total"] == survey["whole_range_count"]
    assert survey["partition_total"] == survey["unique_total"]


def test_fetch_returns_parseable_jats() -> None:
    xml = NcbiClient().fetch_article("PMC6441964")
    metadata = read_metadata(xml)
    assert metadata["pmcid"] == "PMC6441964"
    assert metadata["article_type"]
