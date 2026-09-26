"""Kappa and Spearman, checked against values worked out by hand.

These two numbers decide whether the judge's scores can be believed, so they are
pinned against arithmetic rather than against whatever the implementation
happened to produce first.
"""

from __future__ import annotations

from ragbench.eval.agreement import (
    agreement_summary,
    cohens_kappa,
    exact_agreement,
    spearman,
    within_one,
)

FIVE = [1.0, 2.0, 3.0, 4.0, 5.0]


def test_perfect_agreement_is_one() -> None:
    scores = [1.0, 3.0, 5.0, 2.0, 4.0]
    assert cohens_kappa(scores, scores, FIVE) == 1.0
    assert spearman(scores, scores) == 1.0


def test_two_raters_who_never_agree_score_at_or_below_zero() -> None:
    assert (cohens_kappa([1.0, 1.0, 1.0, 1.0], [5.0, 5.0, 5.0, 5.0], FIVE) or 0) <= 0


def test_weighting_credits_near_misses_that_the_unweighted_form_throws_away() -> None:
    """What makes the scale ordinal rather than nominal.

    Compared on the SAME data, not across two datasets: kappa divides by the
    disagreement its marginals predict, so two symmetric all-disagree sets both
    land at -1 however far apart their categories are. The property that
    actually holds is that, given disagreements which are all adjacent, the
    weighted form scores higher than the unweighted one, which counts a
    4-against-5 exactly as heavily as a 1-against-5.
    """
    human = [5.0, 5.0, 4.0, 4.0, 3.0, 3.0, 2.0, 2.0]
    judge = [5.0, 4.0, 4.0, 3.0, 3.0, 2.0, 2.0, 1.0]
    weighted = cohens_kappa(human, judge, FIVE, weights="quadratic")
    linear = cohens_kappa(human, judge, FIVE, weights="linear")
    unweighted = cohens_kappa(human, judge, FIVE, weights="none")
    assert weighted is not None and linear is not None and unweighted is not None
    assert weighted > linear > unweighted


def test_unweighted_kappa_is_the_textbook_value() -> None:
    """Worked by hand. 40 items: 20 agree on A, 10 agree on B, 5 and 5 split.
    po = 0.75, pe = (25/40)(25/40) + (15/40)(15/40) = 0.53125,
    kappa = (0.75 - 0.53125) / (1 - 0.53125) = 0.4667.
    """
    left = [0.0] * 25 + [1.0] * 15
    right = [0.0] * 20 + [1.0] * 5 + [0.0] * 5 + [1.0] * 10
    assert cohens_kappa(left, right, [0.0, 1.0], weights="none") == 0.4667


def test_raw_agreement_flatters_a_skewed_distribution() -> None:
    """The reason percentage agreement is never reported alone. Here two raters
    agree on 18 of 20 -- 90% -- while agreeing barely more than chance predicts
    from marginals this lopsided."""
    left = [5.0] * 19 + [1.0]
    right = [5.0] * 18 + [1.0] + [5.0]
    assert exact_agreement(left, right) == 0.9
    kappa = cohens_kappa(left, right, FIVE, weights="none")
    assert kappa is not None and kappa < 0.5


def test_a_rater_one_point_harsher_ranks_identically() -> None:
    """The distinction the calibration table exists to make: a consistent offset
    is a calibration difference, not a disagreement about which answers are
    better. Spearman sees through it; exact agreement does not."""
    human = [1.0, 2.0, 3.0, 4.0, 4.0, 2.0, 5.0]
    judge = [2.0, 3.0, 4.0, 5.0, 5.0, 3.0, 5.0]
    assert spearman(human, judge) is not None
    assert spearman(human, judge) > 0.95
    assert exact_agreement(human, judge) < 0.2
    assert within_one(human, judge) == 1.0


def test_ties_do_not_distort_spearman() -> None:
    """Ties are the normal case on a 5-point scale, so average ranks are not an
    optional refinement."""
    assert spearman([3.0, 3.0, 3.0, 5.0], [2.0, 2.0, 2.0, 4.0]) == 1.0


def test_unscored_items_are_not_disagreement() -> None:
    """An abstention carries no scores. Pairing a None against a number would
    count the abstention as a maximal disagreement, which is the opposite of
    what it is."""
    summary = agreement_summary([4.0, None, 5.0], [4.0, 3.0, 5.0], FIVE)
    assert summary["n"] == 2
    assert summary["exact_agreement"] == 1.0


def test_nothing_to_compare_returns_none_rather_than_zero() -> None:
    """Zero would read as total disagreement; None reads as no evidence."""
    summary = agreement_summary([None, None], [1.0, 2.0], FIVE)
    assert summary["n"] == 0
    assert summary["kappa"] is None
    assert summary["spearman"] is None


def test_both_raters_constant_and_identical_is_agreement_not_a_crash() -> None:
    """Degenerate but real: a sample where every answer was judged 5."""
    assert cohens_kappa([5.0] * 6, [5.0] * 6, FIVE) == 1.0


def test_the_verdict_is_compared_without_an_invented_order() -> None:
    """Four nominal categories. Weighting them would say incorrect is closer to
    abstained than to correct, which is a claim the rubric does not make."""
    summary = agreement_summary(
        [0.0, 1.0, 2.0, 3.0], [0.0, 1.0, 3.0, 2.0], [0.0, 1.0, 2.0, 3.0], ordinal=False
    )
    assert summary["spearman"] is None
    assert summary["within_one"] is None
    assert summary["kappa"] is not None


def test_mismatched_lengths_are_an_error() -> None:
    import pytest

    with pytest.raises(ValueError, match="unequal lengths"):
        exact_agreement([1.0, 2.0], [1.0])


def test_a_value_outside_the_declared_categories_is_a_level_not_a_crash() -> None:
    """The bug that killed `report judge --calibration` with the message "1.5".

    Each judge score is the mean of its two passes, so a scale the passes
    disagreed on lands on a half-point. Passed alongside an integer category
    list, that value had no row in the contingency table and raised a bare
    KeyError naming the float and nothing else. `categories` is a MINIMUM level
    set -- it exists so unused levels still shape the expected agreement -- and
    anything observed has to be a level too.
    """
    human = [4.0, 5.0, 3.0, 4.0]
    judge = [4.5, 5.0, 3.0, 4.0]
    result = cohens_kappa(human, judge, [1.0, 2.0, 3.0, 4.0, 5.0])
    assert result is not None
    assert -1.0 <= result <= 1.0


def test_a_half_point_counts_as_a_near_miss_not_a_disagreement() -> None:
    """Quadratic weights are defined on the values, so 4.5 against 4 costs far
    less than 1 against 5 -- which is the whole reason the scale is ordinal."""
    near = cohens_kappa([4.0] * 6 + [5.0], [4.5] * 6 + [5.0], FIVE)
    far = cohens_kappa([4.0] * 6 + [5.0], [1.0] * 6 + [5.0], FIVE)
    assert near is not None and far is not None
    assert near > far


def test_exact_agreement_cannot_match_a_half_point_and_that_is_reported() -> None:
    """The figure itself is right; what would be wrong is printing it without
    saying three of the rows could never have matched."""
    human = [4.0, 4.0, 5.0]
    judge = [4.5, 4.0, 5.0]
    assert exact_agreement(human, judge) == round(2 / 3, 4)
    assert within_one(human, judge) == 1.0
