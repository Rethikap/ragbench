"""The paired tests, against arithmetic that can be checked by hand.

The point of writing these tests in-house rather than importing them is that at
n=20 an exact answer is cheap, so every claim here is checked against a number
worked out independently: a binomial tail from `math.comb`, a permutation
distribution small enough to enumerate, or scipy where scipy is exact.
"""

from __future__ import annotations

import numpy as np
import pytest

from ragbench.stats.tests import (
    average_ranks,
    binomial_two_sided,
    bootstrap_ci,
    holm,
    mcnemar_exact,
    sign_test,
    wilcoxon_signed_rank,
)

# ------------------------------------------------------- hand-computable cases


def test_all_positive_differences_give_the_binomial_tail() -> None:
    """Three differences, all positive. Under the null each sign is a coin
    flip, so the largest possible W+ has probability 1/8 and the two-sided
    p is 2/8 = 0.25. No table needed."""
    p, effect = wilcoxon_signed_rank([1.0, 2.0, 3.0])
    assert p == pytest.approx(0.25)
    assert effect == pytest.approx(1.0)


def test_the_sign_test_is_an_exact_binomial_tail() -> None:
    """Five of five in one direction: 2 * (1/2)^5 = 0.0625."""
    p, effect, ties = sign_test([1.0] * 5)
    assert p == pytest.approx(0.0625)
    assert effect == pytest.approx(1.0)
    assert ties == 0


def test_a_perfectly_even_split_is_not_evidence() -> None:
    assert binomial_two_sided(3, 6) == pytest.approx(1.0)
    p, effect, _ = sign_test([1.0, 1.0, 1.0, -1.0, -1.0, -1.0])
    assert p == pytest.approx(1.0)
    assert effect == pytest.approx(0.0)


def test_mcnemar_is_the_sign_test_under_another_name() -> None:
    """For a 0/1 outcome the discordant pairs ARE the non-zero differences."""
    assert mcnemar_exact(8, 2) == pytest.approx(binomial_two_sided(8, 10))
    p, _, _ = sign_test([1.0] * 8 + [-1.0] * 2)
    assert p == pytest.approx(mcnemar_exact(8, 2))


def test_zero_differences_are_dropped_and_reported_not_silently_kept() -> None:
    """A question where nothing changed carries no evidence about direction.
    Keeping it would drag every rank toward the middle; dropping it without
    saying so would hide that the effect rests on four questions."""
    p_with, _ = wilcoxon_signed_rank([1.0, 2.0, 3.0, 0.0, 0.0])
    p_without, _ = wilcoxon_signed_rank([1.0, 2.0, 3.0])
    assert p_with == pytest.approx(p_without)

    _, _, ties = sign_test([1.0, 2.0, 3.0, 0.0, 0.0])
    assert ties == 2


def test_ties_share_an_average_rank() -> None:
    assert list(average_ranks(np.array([1.0, 2.0, 2.0, 4.0]))) == [1.0, 2.5, 2.5, 4.0]


def test_nothing_to_test_returns_none_rather_than_a_p_value() -> None:
    assert wilcoxon_signed_rank([]) == (None, None)
    assert wilcoxon_signed_rank([0.0, 0.0]) == (None, None)
    assert sign_test([])[0] is None


# --------------------------------------------- against scipy, where it is exact


def test_matches_scipy_exactly_when_scipy_computes_exactly() -> None:
    """With no ties scipy uses its own exact method, and the two must agree to
    the last digit -- they are computing the same permutation distribution."""
    scipy_stats = pytest.importorskip("scipy.stats")
    rng = np.random.default_rng(1)
    for _ in range(5):
        while True:
            values = rng.normal(0.3, 1.0, 20)
            if len(set(np.abs(values))) == 20 and not (values == 0).any():
                break
        mine, _ = wilcoxon_signed_rank(list(values))
        theirs = scipy_stats.wilcoxon(values, alternative="two-sided", method="exact").pvalue
        assert mine == pytest.approx(theirs, abs=1e-12)


def test_the_sign_test_matches_scipy_binomtest() -> None:
    scipy_stats = pytest.importorskip("scipy.stats")
    for successes, trials in ((8, 10), (3, 5), (15, 20), (10, 20)):
        expected = scipy_stats.binomtest(successes, trials, 0.5).pvalue
        assert binomial_two_sided(successes, trials) == pytest.approx(expected)


def test_ties_are_handled_exactly_where_scipy_falls_back_to_an_approximation() -> None:
    """On a 1-5 scale ties are the normal case, and scipy's exact mode silently
    becomes a normal approximation when it meets them. The exact permutation
    value over averaged ranks is a different -- and better -- number, so this
    pins that they are close without asserting they are equal."""
    scipy_stats = pytest.importorskip("scipy.stats")
    values = [0.5, 0.5, 0.5, -0.5, 1.0, 1.0, -1.0, 2.0, 2.0, 2.0,
              -2.0, 0.3, 0.3, -0.3, 1.5, 1.5, -1.5, 0.8, 0.8, -0.8]
    mine, _ = wilcoxon_signed_rank(values)
    approximate = scipy_stats.wilcoxon(values, alternative="two-sided").pvalue
    assert mine == pytest.approx(approximate, abs=0.02)
    assert mine != approximate


# ------------------------------------------------------- the bootstrap interval


def test_the_interval_covers_a_known_effect() -> None:
    """A constructed dataset whose true effect is 0.20 by construction."""
    rng = np.random.default_rng(7)
    differences = list(0.20 + rng.normal(0.0, 0.10, 20))
    mean, low, high = bootstrap_ci(differences, resamples=4000, seed=11)
    assert low < 0.20 < high
    assert mean == pytest.approx(float(np.mean(differences)))


def test_the_interval_has_about_its_nominal_coverage() -> None:
    """The property a confidence interval is *for*. 200 constructed datasets,
    each with a true effect of 0.20; the interval should miss about 5% of the
    time. A band rather than a point, because 200 replicates is itself noisy."""
    rng = np.random.default_rng(3)
    covered = 0
    trials = 200
    for _ in range(trials):
        differences = list(0.20 + rng.normal(0.0, 0.25, 20))
        _, low, high = bootstrap_ci(differences, resamples=400, seed=5)
        covered += int(low <= 0.20 <= high)
    assert 0.86 <= covered / trials <= 0.99


def test_the_interval_is_the_same_number_every_time() -> None:
    differences = [0.1, -0.2, 0.3, 0.0, 0.5]
    assert bootstrap_ci(differences, resamples=500, seed=4) == bootstrap_ci(
        differences, resamples=500, seed=4
    )


def test_one_observation_gives_a_mean_but_no_interval() -> None:
    """Reporting an interval from a single question would be an invention."""
    mean, low, high = bootstrap_ci([0.4])
    assert mean == pytest.approx(0.4)
    assert low is None and high is None


# --------------------------------------------------------------- Holm


def test_holm_is_a_step_down_and_stays_monotone() -> None:
    """Worked by hand for 4 tests: 0.01*4=0.04, 0.02*3=0.06, 0.03*2=0.06 (held
    at the running maximum), 0.04*1=0.06."""
    result = holm({"a": 0.01, "b": 0.02, "c": 0.03, "d": 0.04}, alpha=0.05)
    assert result["a"]["p_holm"] == pytest.approx(0.04)
    assert result["b"]["p_holm"] == pytest.approx(0.06)
    assert result["c"]["p_holm"] == pytest.approx(0.06)
    assert result["d"]["p_holm"] == pytest.approx(0.06)
    assert result["a"]["significant"] and not result["b"]["significant"]


def test_holm_is_never_harsher_than_bonferroni() -> None:
    values = {"a": 0.001, "b": 0.02, "c": 0.3, "d": 0.5, "e": 0.9, "f": 0.95}
    result = holm(values)
    for name, p in values.items():
        assert result[name]["p_holm"] <= min(1.0, p * len(values)) + 1e-12


def test_an_uncomputable_test_still_counts_toward_the_family() -> None:
    """The correction must not move as the run progresses.

    Judging arrives one configuration at a time, so half the pre-specified
    family has no data yet. Correcting against only what is computable would
    give a retrieval p of 0.01 a p_holm of 0.02 today (family of 2) and 0.06
    once judging finished (family of 6) -- significant, then not, from the same
    measurement. The family is the one that was written down in advance.
    """
    partial = holm({"a": 0.01, "b": 0.02, "c": None, "d": None, "e": None, "f": None})
    complete = holm({"a": 0.01, "b": 0.02, "c": 0.3, "d": 0.4, "e": 0.5, "f": 0.6})
    assert partial["a"]["p_holm"] == pytest.approx(complete["a"]["p_holm"])
    assert partial["a"]["p_holm"] == pytest.approx(0.06)
    assert partial["c"]["p_holm"] is None
    assert not partial["c"]["significant"]


def test_the_family_size_can_be_stated_explicitly() -> None:
    """For a family whose members are not all passed in at once."""
    assert holm({"a": 0.01}, family_size=6)["a"]["p_holm"] == pytest.approx(0.06)
    assert holm({"a": 0.01})["a"]["p_holm"] == pytest.approx(0.01)
