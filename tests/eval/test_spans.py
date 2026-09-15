"""Span coverage and the secondary rank metrics.

The tests are written against a synthetic two-arm chunking of one body, because
the property under test is precisely that the metric does not depend on which
arm produced the chunks.
"""

from __future__ import annotations

import pytest

from ragbench.eval.spans import (
    covering_chunks,
    minimum_cover,
    ndcg_at_k,
    recall_at_k,
    span_coverage,
)
from ragbench.types import Chunk, GoldSpan


def chunk(index: int, start: int, end: int, pmcid: str = "PMC1") -> Chunk:
    return Chunk(
        chunk_id=f"{pmcid}-{index:04d}",
        pmcid=pmcid,
        chunk_index=index,
        text="x" * (end - start),
        n_tokens=end - start,
        char_start=start,
        char_end=end,
        sections=(),
        content_sha256="0" * 64,
    )


#: One body, chunked two ways. COARSE covers [0, 300) in one chunk; FINE needs
#: three. This is the shape the whole design point is about.
COARSE = [chunk(0, 0, 300), chunk(1, 300, 600)]
FINE = [chunk(i, i * 100, i * 100 + 100) for i in range(6)]

def gold(start: int, end: int, pmcid: str = "PMC1") -> GoldSpan:
    """A span with a context wide enough to hold it.

    The context is provenance and no metric reads it, so these tests set it to
    the whole synthetic body and then forget about it.
    """
    return GoldSpan(
        pmcid=pmcid,
        char_start=start,
        char_end=end,
        section="Results",
        context_start=0,
        context_end=600,
    )


GOLD = gold(120, 260)


# ------------------------------------------------------------- span coverage


def test_full_coverage_scores_one_in_both_arms() -> None:
    """The headline property: the same retrieved text scores the same either way."""
    assert span_coverage(GOLD, [COARSE[0]]) == 1.0
    assert span_coverage(GOLD, FINE[1:3]) == 1.0


def test_partial_coverage_is_the_character_fraction() -> None:
    # FINE[1] covers [100, 200), so 80 of the span's 140 characters.
    assert span_coverage(GOLD, [FINE[1]]) == pytest.approx(80 / 140)
    # FINE[2] covers [200, 300), so the remaining 60.
    assert span_coverage(GOLD, [FINE[2]]) == pytest.approx(60 / 140)


def test_chunks_from_another_paper_contribute_nothing() -> None:
    """However high they ranked. The span names one paper."""
    other = chunk(0, 120, 260, pmcid="PMC2")
    assert span_coverage(GOLD, [other]) == 0.0
    assert span_coverage(GOLD, [other, FINE[1]]) == pytest.approx(80 / 140)


def test_retrieving_the_same_text_twice_cannot_score_above_one() -> None:
    """Overlapping chunks are unioned, not summed."""
    overlapping = [chunk(0, 100, 300), chunk(1, 150, 280)]
    assert span_coverage(GOLD, overlapping) == 1.0


def test_empty_retrieval_scores_zero() -> None:
    assert span_coverage(GOLD, []) == 0.0


def test_non_overlapping_chunks_score_zero() -> None:
    assert span_coverage(GOLD, [FINE[0], FINE[4]]) == 0.0


def test_an_empty_gold_span_cannot_be_constructed() -> None:
    """A label with no characters cannot be covered, so it is refused where it is
    made rather than scored as a zero where it is read."""
    with pytest.raises(ValueError, match="empty evidence span"):
        GoldSpan(
            pmcid="PMC1", char_start=200, char_end=200, section="Results",
            context_start=0, context_end=600,
        )


# --------------------------------------------------- derived per-arm relevance


def test_the_relevant_set_is_derived_per_arm() -> None:
    """No gold chunk id is ever stored; each arm's relevant set comes from its own
    boundaries. The counts differ, which is the whole reason recall is secondary."""
    assert [c.chunk_id for c in covering_chunks(GOLD, COARSE)] == ["PMC1-0000"]
    assert [c.chunk_id for c in covering_chunks(GOLD, FINE)] == ["PMC1-0001", "PMC1-0002"]


def test_minimum_cover_counts_what_each_arm_must_win() -> None:
    assert minimum_cover(GOLD, COARSE)["n_chunks_to_cover"] == 1
    assert minimum_cover(GOLD, FINE)["n_chunks_to_cover"] == 2
    assert minimum_cover(GOLD, COARSE)["max_coverage"] == 1.0
    assert minimum_cover(GOLD, FINE)["max_coverage"] == 1.0


def test_max_coverage_records_a_gap_between_chunks() -> None:
    """A span straddling a boundary loses the characters that belong to neither
    chunk. The ceiling is reported rather than rounded up to 1.0."""
    gapped = [chunk(0, 100, 199), chunk(1, 200, 300)]
    assert minimum_cover(GOLD, gapped)["max_coverage"] == pytest.approx(139 / 140)


# ------------------------------------------------------------ rank metrics


def test_recall_penalises_the_finer_arm_for_being_finer() -> None:
    """The documented reason span coverage is primary, asserted so it stays true.

    Both arms put the same 140 characters in front of the generator. Coverage
    agrees; recall does not.
    """
    coarse_ranked = [COARSE[0]]
    fine_ranked = [FINE[1]]
    assert span_coverage(GOLD, coarse_ranked) == 1.0
    assert recall_at_k(GOLD, coarse_ranked, COARSE, 10) == 1.0
    assert recall_at_k(GOLD, fine_ranked, FINE, 10) == 0.5


def test_recall_counts_only_the_top_k() -> None:
    ranked = [FINE[5], FINE[4], FINE[1], FINE[2]]
    assert recall_at_k(GOLD, ranked, FINE, 2) == 0.0
    assert recall_at_k(GOLD, ranked, FINE, 3) == 0.5
    assert recall_at_k(GOLD, ranked, FINE, 4) == 1.0


def test_ndcg_rewards_ranking_the_relevant_chunks_first() -> None:
    best = ndcg_at_k(GOLD, [FINE[1], FINE[2], FINE[0]], FINE, 10)
    worse = ndcg_at_k(GOLD, [FINE[0], FINE[1], FINE[2]], FINE, 10)
    assert best == 1.0
    assert 0.0 < worse < best


def test_ndcg_is_zero_when_nothing_relevant_is_retrieved() -> None:
    assert ndcg_at_k(GOLD, [FINE[0], FINE[4], FINE[5]], FINE, 10) == 0.0


def test_rank_metrics_are_zero_when_the_arm_has_no_relevant_chunk() -> None:
    """A gold span in a paper the chunk set does not contain."""
    missing = gold(0, 10, pmcid="PMC404")
    assert recall_at_k(missing, FINE, FINE, 10) == 0.0
    assert ndcg_at_k(missing, FINE, FINE, 10) == 0.0
