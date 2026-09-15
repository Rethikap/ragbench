"""Window metrics: precision, position and noise at a constant token budget.

Written against the same synthetic two-arm chunking as test_spans.py, because
the point of these three is precisely what span coverage cannot see: both arms
hold the identical gold span, and the windows around it differ.
"""

from __future__ import annotations

import pytest

from ragbench.eval.context import (
    context_profile,
    distractor_count,
    evidence_density,
    gold_chunk_rank,
)
from ragbench.types import Chunk, GoldSpan


def chunk(
    index: int, start: int, end: int, pmcid: str = "PMC1", tokens: int | None = None
) -> Chunk:
    return Chunk(
        chunk_id=f"{pmcid}-{index:04d}",
        pmcid=pmcid,
        chunk_index=index,
        text="x" * (end - start),
        n_tokens=tokens if tokens is not None else (end - start),
        char_start=start,
        char_end=end,
        sections=(),
        content_sha256="0" * 64,
    )


def gold(start: int, end: int, pmcid: str = "PMC1") -> GoldSpan:
    return GoldSpan(
        pmcid=pmcid,
        char_start=start,
        char_end=end,
        section="Results",
        context_start=0,
        context_end=3000,
    )


#: One 100-character answer, held by a coarse arm in a 400-char chunk and by a
#: fine arm in a 100-char chunk. Coverage is 1.0 either way; nothing else is.
GOLD = gold(400, 500)
COARSE = [chunk(i, i * 400, i * 400 + 400) for i in range(6)]
FINE = [chunk(i, i * 100, i * 100 + 100) for i in range(24)]


# ------------------------------------------------------------ evidence density


def test_density_separates_arms_that_coverage_cannot() -> None:
    """The headline: identical coverage, different precision."""
    from ragbench.eval.spans import span_coverage

    coarse_window = COARSE[:2]
    fine_window = FINE[:8]
    assert span_coverage(GOLD, coarse_window) == 1.0
    assert span_coverage(GOLD, fine_window) == 1.0
    # Same 800 characters of context, but the coarse arm cannot hold less than
    # its own chunk, so the difference shows up only when the budget is smaller.
    assert evidence_density(GOLD, coarse_window) == pytest.approx(100 / 800)
    assert evidence_density(GOLD, [FINE[4]]) == pytest.approx(1.0)


def test_density_is_the_gold_share_of_everything_retrieved() -> None:
    assert evidence_density(GOLD, [COARSE[1]]) == pytest.approx(100 / 400)
    assert evidence_density(GOLD, [COARSE[1], COARSE[2]]) == pytest.approx(100 / 800)


def test_density_counts_only_the_covered_part_of_the_span() -> None:
    """Half the answer in the window is half the numerator."""
    partial = chunk(0, 450, 850)
    assert evidence_density(GOLD, [partial]) == pytest.approx(50 / 400)


def test_density_of_an_empty_context_is_zero() -> None:
    assert evidence_density(GOLD, []) == 0.0


def test_a_window_with_no_gold_has_zero_density() -> None:
    assert evidence_density(GOLD, [COARSE[4], COARSE[5]]) == 0.0


# ------------------------------------------------------------------- position


def test_rank_is_one_based_over_the_assembled_order() -> None:
    window = [COARSE[3], COARSE[1], COARSE[5]]
    assert gold_chunk_rank(GOLD, window)["rank"] == 2


def test_token_offset_is_what_position_effects_act_on() -> None:
    """Rank 3 of a coarse arm puts the evidence far deeper into the window than
    rank 3 of a fine arm, which is the whole reason rank alone is not enough."""
    coarse = [COARSE[4], COARSE[5], COARSE[1]]
    fine = [FINE[20], FINE[21], FINE[4]]
    assert gold_chunk_rank(GOLD, coarse)["rank"] == 3
    assert gold_chunk_rank(GOLD, fine)["rank"] == 3
    assert gold_chunk_rank(GOLD, coarse)["tokens_before"] == 800
    assert gold_chunk_rank(GOLD, fine)["tokens_before"] == 200


def test_an_absent_gold_chunk_ranks_none_not_zero() -> None:
    """Rank 0 would sort ahead of a first-place hit."""
    position = gold_chunk_rank(GOLD, [COARSE[4], COARSE[5]])
    assert position["rank"] is None
    assert position["tokens_before"] is None
    assert position["n_gold_chunks"] == 0


def test_the_first_gold_chunk_is_the_one_reported() -> None:
    span = gold(350, 550)
    window = [COARSE[0], COARSE[1]]
    assert gold_chunk_rank(span, window)["rank"] == 1
    assert gold_chunk_rank(span, window)["n_gold_chunks"] == 2


def test_token_cost_can_be_supplied_by_the_caller() -> None:
    """Retrieval measures the budget in generator tokens (I1) and records them;
    the default canonical count is only what a chunk set alone can offer."""
    window = [COARSE[4], COARSE[1]]
    assert gold_chunk_rank(GOLD, window)["tokens_before"] == 400
    assert gold_chunk_rank(GOLD, window, lambda c: 7)["tokens_before"] == 7


# ------------------------------------------------------------------ distractors


def test_distractors_are_the_chunks_that_miss_the_span() -> None:
    assert distractor_count(GOLD, [COARSE[1], COARSE[2], COARSE[3]]) == 2
    assert distractor_count(GOLD, [COARSE[1]]) == 0


def test_a_same_paper_chunk_that_misses_the_span_is_a_distractor() -> None:
    """Same vocabulary, same authors, wrong sentences -- the interesting kind."""
    assert distractor_count(GOLD, [COARSE[1], COARSE[0]]) == 1


def test_a_finer_arm_fits_more_distractors_in_the_same_budget() -> None:
    """The constant-token-budget consequence (I1): whether the extra chunks are
    more context or more noise is what RQ1 asks."""
    coarse_window = [COARSE[1]] + COARSE[2:4]        # 1200 chars
    fine_window = [FINE[4]] + FINE[8:19]             # 1200 chars
    assert sum(len(c.text) for c in coarse_window) == sum(len(c.text) for c in fine_window)
    assert distractor_count(GOLD, coarse_window) == 2
    assert distractor_count(GOLD, fine_window) == 11


# --------------------------------------------------------------------- profile


def test_the_profile_reports_every_measurement_at_once() -> None:
    window = [COARSE[0], COARSE[1], COARSE[2]]
    profile = context_profile(GOLD, window)
    assert profile["n_chunks"] == 3
    assert profile["context_chars"] == 1200
    assert profile["span_coverage"] == 1.0
    # The profile rounds for the JSON artefact; the metric itself does not.
    assert profile["evidence_density"] == pytest.approx(100 / 1200, abs=1e-6)
    assert profile["distractor_count"] == 2
    assert profile["rank"] == 2
    assert profile["tokens_before"] == 400


def test_the_profile_survives_an_empty_context() -> None:
    profile = context_profile(GOLD, [])
    assert profile["span_coverage"] == 0.0
    assert profile["evidence_density"] == 0.0
    assert profile["distractor_count"] == 0
    assert profile["rank"] is None
