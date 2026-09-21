"""How many questions a FUTURE study would need. Never how much this one had.

**This module does not compute observed power, and must not be made to.**
Post-hoc power -- the power of the study you just ran, evaluated at the effect
you just observed -- is a monotone function of the p-value and carries no
information the p-value did not. A non-significant result always has low
observed power, so reporting it says only "this was not significant" a second
time, with a number attached that looks like evidence. A reviewer will name the
fallacy, and they will be right.

What is useful, and what is computed here, is **prospective**: given an effect
of the size this study saw, how many questions would a *new* study need to
detect it at 80% power? That is a planning quantity for future work, it makes no
claim about this study's result, and it is what turns "underpowered at n=20"
into a number someone can act on.

Estimated by simulation rather than a closed-form approximation, so that the
answer is about the tests actually used. The closed forms assume normal
differences and a t-test; this resamples the observed per-question differences
and runs the same exact sign or signed-rank test the report runs, so any
peculiarity of the data -- ties, a heavy tail, a handful of questions carrying
the effect -- is carried through rather than assumed away.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from .tests import binomial_two_sided, wilcoxon_signed_rank

#: Beyond this the answer is "more than a thesis can collect" and the exact
#: figure stops mattering.
MAX_N = 4000
#: An effect indistinguishable from zero needs an unbounded sample. Reported as
#: not estimable rather than as a very large number that looks like a plan.
NEGLIGIBLE = 1e-9


def _p_values(
    values: np.ndarray, n: int, effect: float, kind: str, trials: int, seed: int
) -> np.ndarray:
    """Simulated p-values for `trials` studies of size `n` at a given true effect.

    The observed differences are shifted to have mean ``effect`` and then
    resampled with replacement. Shifting rather than rescaling keeps the shape
    of the distribution -- its spread, its skew, which questions are extreme --
    and moves only the quantity being planned for.
    """
    shifted = values - float(values.mean()) + float(effect)
    rng = np.random.default_rng(seed)
    draws = shifted[rng.integers(0, shifted.size, size=(trials, n))]

    if kind == "binary":
        positives = (draws > 0).sum(axis=1)
        non_zero = (draws != 0).sum(axis=1)
        return np.array(
            [binomial_two_sided(int(p), int(m)) for p, m in zip(positives, non_zero, strict=True)]
        )
    return np.array(
        [wilcoxon_signed_rank(list(row))[0] or 1.0 for row in draws]
    )


class _Curve:
    """Power at each candidate n, simulated once and reused.

    Both alpha levels and both ends of the confidence interval search over the
    same candidate sizes, so simulating a size twice would only spend time
    disagreeing with itself by sampling noise.
    """

    def __init__(
        self, values: np.ndarray, effect: float, kind: str, trials: int, seed: int
    ) -> None:
        self._values = values
        self._effect = effect
        self._kind = kind
        self._trials = trials
        self._seed = seed
        self._cache: dict[int, np.ndarray] = {}

    def power(self, n: int, alpha: float) -> float:
        if n not in self._cache:
            self._cache[n] = _p_values(
                self._values, n, self._effect, self._kind, self._trials, self._seed + n
            )
        return float((self._cache[n] <= alpha).mean())


def required_n(
    values: Sequence[float],
    effect: float,
    kind: str,
    alpha: float,
    target_power: float = 0.80,
    trials: int = 400,
    seed: int = 0,
    max_n: int = MAX_N,
    curve: _Curve | None = None,
) -> dict[str, Any]:
    """Smallest n reaching ``target_power``, by doubling then bisecting.

    Power rises with n but the simulation makes it rise *noisily*, so the
    bisection is on a curve with a little jitter in it. That is acceptable for a
    planning figure and the answer is reported rounded and with a range around
    it; it would not be acceptable for a claim, which is why none is made from
    it.
    """
    array = np.asarray([value for value in values if value is not None], dtype=float)
    if array.size < 2:
        return {"n": None, "reason": "not enough questions to resample from"}
    if abs(effect) < NEGLIGIBLE:
        return {"n": None, "reason": "not estimable: the effect is indistinguishable from zero"}

    shape = curve or _Curve(array, effect, kind, trials, seed)
    low, high = 0, 0
    candidate = 10
    while candidate <= max_n:
        if shape.power(candidate, alpha) >= target_power:
            high = candidate
            break
        low = candidate
        candidate *= 2
    if not high:
        return {"n": None, "reason": f"not estimable: below {target_power:.0%} power at n={max_n}"}

    while high - low > 1:
        middle = (low + high) // 2
        if shape.power(middle, alpha) >= target_power:
            high = middle
        else:
            low = middle
    return {"n": int(high), "power_at_n": round(shape.power(high, alpha), 3), "reason": ""}


def sample_size(
    values: Sequence[float],
    mean_difference: float | None,
    ci_low: float | None,
    ci_high: float | None,
    kind: str,
    alpha: float,
    holm_alpha: float,
    target_power: float = 0.80,
    trials: int = 400,
    seed: int = 0,
) -> dict[str, Any]:
    """The planning estimate: n at the observed effect, and across its interval.

    Three effect sizes, because the observed one is itself a noisy estimate from
    twenty questions and a single n would claim a precision the data has not
    got. Two alpha levels, because a follow-up carrying the same
    pre-specification would face the same Holm correction, and planning against
    the uncorrected 0.05 would under-size it.
    """
    array = np.asarray([value for value in values if value is not None], dtype=float)
    out: dict[str, Any] = {
        "target_power": target_power,
        "alpha": alpha,
        "holm_alpha": holm_alpha,
        "trials": trials,
        "kind": kind,
        "estimates": {},
    }
    if array.size < 2 or mean_difference is None:
        out["estimates"] = {}
        out["note"] = "no data"
        return out

    targets = {
        "observed": mean_difference,
        "ci_low": ci_low,
        "ci_high": ci_high,
    }
    for label, effect in targets.items():
        if effect is None:
            out["estimates"][label] = {"effect": None, "at_alpha": {"n": None,
                                       "reason": "no interval"}, "at_holm_alpha": {"n": None,
                                       "reason": "no interval"}}
            continue
        shape = _Curve(array, float(effect), kind, trials, seed)
        out["estimates"][label] = {
            "effect": float(effect),
            "at_alpha": required_n(array, float(effect), kind, alpha, target_power,
                                   trials, seed, curve=shape),
            "at_holm_alpha": required_n(array, float(effect), kind, holm_alpha, target_power,
                                        trials, seed, curve=shape),
        }

    # Which end of the interval is the pessimistic one: the smaller effect needs
    # the larger sample. An interval spanning zero has no worst case at all,
    # which is a fact about the evidence rather than a number to print.
    if ci_low is not None and ci_high is not None:
        spans_zero = ci_low <= 0.0 <= ci_high
        out["interval_spans_zero"] = bool(spans_zero)
        out["pessimistic_end"] = (
            None if spans_zero else ("ci_low" if abs(ci_low) < abs(ci_high) else "ci_high")
        )
    return out


def holm_alpha(alpha: float, family_size: int) -> float:
    """The strictest threshold in a Holm family: alpha / m.

    Holm tests the smallest p against alpha/m and relaxes from there, so a study
    planned to clear its first hurdle is planned against alpha/m. Using the
    relaxed end would be planning for the easiest case and calling it the design.
    """
    return alpha / max(1, family_size)


def power_curve(
    values: Sequence[float],
    effect: float,
    kind: str,
    alpha: float,
    sizes: Sequence[int],
    trials: int = 400,
    seed: int = 0,
) -> list[dict[str, float]]:
    """Power at each of ``sizes``, for the figure.

    The same simulation the search uses, evaluated on a stated ladder instead of
    a bisection, so the plotted curve and the reported number come from one
    procedure rather than two that might disagree.
    """
    array = np.asarray([value for value in values if value is not None], dtype=float)
    if array.size < 2 or abs(effect) < NEGLIGIBLE:
        return []
    shape = _Curve(array, float(effect), kind, trials, seed)
    return [{"n": int(n), "power": round(shape.power(int(n), alpha), 4)} for n in sizes]


def curve_sizes(largest_n: int | None, cap: int = 600) -> list[int]:
    """A ladder that covers the answer without running off the page."""
    top = min(cap, max(60, int((largest_n or 40) * 1.6)))
    steps = [10, 15, 20, 30, 40, 60, 80, 120, 160, 240, 320, 480, 640, 960, 1600]
    inside = [step for step in steps if step <= top]
    return inside or [10, 20, 40]
