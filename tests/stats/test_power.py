"""The sample-size estimate: a planning number for future work, and nothing else.

The load-bearing test here is the one that checks the simulation lands near a
value that can be computed independently from a textbook formula. The rest guard
the boundary conditions that make a planning figure honest -- an effect that
cannot be planned for, and an interval that spans zero.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from ragbench.stats.power import NEGLIGIBLE, holm_alpha, required_n, sample_size


def _normal(effect: float, sd: float, size: int = 400, seed: int = 0) -> list[float]:
    """A differences vector with a known effect and spread to resample from."""
    rng = np.random.default_rng(seed)
    values = rng.normal(0.0, sd, size)
    return list(values - values.mean() + effect)


def _textbook_n(effect: float, sd: float, alpha: float = 0.05, power: float = 0.80) -> float:
    """One-sample two-sided test: n = ((z_a/2 + z_b) * sd / effect)^2.

    The normal-theory answer, computed here so the simulation is checked against
    arithmetic from outside it rather than against its own previous output.
    """
    z_alpha = _normal_quantile(1.0 - alpha / 2.0)
    z_beta = _normal_quantile(power)
    return ((z_alpha + z_beta) * sd / effect) ** 2


def _normal_quantile(p: float) -> float:
    """Inverse standard normal CDF by bisection on erf. No scipy needed."""
    low, high = -10.0, 10.0
    for _ in range(200):
        middle = (low + high) / 2.0
        if 0.5 * (1.0 + math.erf(middle / math.sqrt(2.0))) < p:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


# ------------------------------------------------------- the known-answer case


def test_the_simulated_n_lands_near_the_textbook_value() -> None:
    """A constructed effect of 0.5 with sd 1.0 needs about 34 by normal theory.

    The signed-rank test is slightly less powerful than the t-test on exactly
    normal data -- about 95% efficient -- so the simulated answer should sit a
    little above the formula, not below it and not wildly away from it. A band
    rather than a point, because the simulation is stochastic and the formula
    assumes a test this is not.
    """
    expected = _textbook_n(effect=0.5, sd=1.0)
    assert 30 <= expected <= 36  # the formula itself, pinned

    found = required_n(
        _normal(effect=0.5, sd=1.0), effect=0.5, kind="continuous", alpha=0.05,
        trials=400, seed=3,
    )
    assert found["n"] is not None
    assert expected * 0.8 <= found["n"] <= expected * 1.4
    assert found["power_at_n"] >= 0.78


def test_a_smaller_effect_needs_a_larger_sample_at_the_documented_rate() -> None:
    """Halving the effect quadruples the sample, which the formula says exactly
    and the simulation should reproduce to within its own noise."""
    big = required_n(_normal(0.5, 1.0), 0.5, "continuous", 0.05, trials=250, seed=4)
    small = required_n(_normal(0.25, 1.0), 0.25, "continuous", 0.05, trials=250, seed=4)
    assert 2.5 <= small["n"] / big["n"] <= 6.0


def test_a_stricter_alpha_needs_a_larger_sample() -> None:
    values = _normal(0.5, 1.0)
    relaxed = required_n(values, 0.5, "continuous", 0.05, trials=250, seed=6)
    strict = required_n(values, 0.5, "continuous", holm_alpha(0.05, 6), trials=250, seed=6)
    assert strict["n"] > relaxed["n"]


def test_the_binary_path_uses_the_sign_test_and_needs_more() -> None:
    """The sign test throws away magnitude, so it buys significance with sample
    size. Same data, more questions needed."""
    values = _normal(0.5, 1.0)
    continuous = required_n(values, 0.5, "continuous", 0.05, trials=250, seed=8)
    binary = required_n(values, 0.5, "binary", 0.05, trials=250, seed=8)
    assert binary["n"] > continuous["n"]


# ----------------------------------------------------- when it is not estimable


def test_an_effect_of_zero_is_not_estimable_rather_than_infinite() -> None:
    """Printing a very large number would look like a plan someone could follow."""
    result = required_n(_normal(0.0, 1.0), 0.0, "continuous", 0.05, trials=100, seed=1)
    assert result["n"] is None
    assert "not estimable" in result["reason"]


def test_a_negligible_effect_is_caught_before_any_simulation_runs() -> None:
    result = required_n([0.1, -0.1, 0.2], NEGLIGIBLE / 2, "continuous", 0.05, trials=10)
    assert result["n"] is None
    assert "indistinguishable from zero" in result["reason"]


def test_an_effect_too_small_for_the_cap_says_so_with_the_cap() -> None:
    result = required_n(
        _normal(0.002, 1.0), 0.002, "continuous", 0.05, trials=100, seed=2, max_n=200
    )
    assert result["n"] is None
    assert "n=200" in result["reason"]


def test_too_few_questions_to_resample_from_is_refused() -> None:
    assert required_n([0.5], 0.5, "continuous", 0.05)["n"] is None


# --------------------------------------------------------- the reported shape


def test_the_estimate_covers_the_interval_as_well_as_the_point() -> None:
    """A single n would claim a precision twenty questions has not got."""
    values = _normal(0.5, 1.0, size=20, seed=9)
    result = sample_size(
        values, mean_difference=0.5, ci_low=0.3, ci_high=0.7, kind="continuous",
        alpha=0.05, holm_alpha=holm_alpha(0.05, 6), trials=150, seed=2,
    )
    assert set(result["estimates"]) == {"observed", "ci_low", "ci_high"}
    # The smaller effect needs the larger sample, at both alpha levels.
    assert result["estimates"]["ci_low"]["at_alpha"]["n"] > (
        result["estimates"]["ci_high"]["at_alpha"]["n"]
    )
    assert result["estimates"]["observed"]["at_holm_alpha"]["n"] > (
        result["estimates"]["observed"]["at_alpha"]["n"]
    )
    assert result["pessimistic_end"] == "ci_low"
    assert result["interval_spans_zero"] is False


def test_an_interval_spanning_zero_has_no_worst_case(
) -> None:
    """And saying so is more useful than printing the number for whichever end
    happens to be nearer zero."""
    values = _normal(0.1, 1.0, size=20, seed=11)
    result = sample_size(
        values, mean_difference=0.1, ci_low=-0.2, ci_high=0.4, kind="continuous",
        alpha=0.05, holm_alpha=holm_alpha(0.05, 6), trials=120, seed=1,
    )
    assert result["interval_spans_zero"] is True
    assert result["pessimistic_end"] is None


def test_holm_alpha_is_the_strictest_threshold_in_the_family() -> None:
    """Holm tests the smallest p against alpha/m; planning against the relaxed
    end would be designing for the easiest case."""
    assert holm_alpha(0.05, 6) == pytest.approx(0.05 / 6)
    assert holm_alpha(0.05, 1) == pytest.approx(0.05)


def test_nothing_here_reports_the_power_of_the_study_that_was_run() -> None:
    """Post-hoc observed power is a function of the p-value and adds nothing.
    The module must offer no way to ask for it."""
    import ragbench.stats.power as module

    names = [name for name in dir(module) if not name.startswith("_")]
    assert "observed_power" not in names
    assert "post_hoc_power" not in names
    assert "achieved_power" not in names
    # Every public entry point takes an effect size to plan FOR, rather than
    # reading one off the study.
    assert "effect" in required_n.__code__.co_varnames
