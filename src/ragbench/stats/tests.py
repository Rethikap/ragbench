"""Paired tests, computed exactly, on twenty differences.

Everything here takes **one difference per question** and nothing else. That
shape is not incidental: it is what keeps the 8 configurations from being
counted as 8 independent samples when they are 8 measurements of the same 20
questions (see :mod:`ragbench.stats.design`).

The tests are exact rather than approximate, and that is the whole reason they
are written here instead of imported. At n=20 an exact test is cheap: the
signed-rank null is a sign-flip distribution over 20 ranks, which a dynamic
program computes in a few hundred additions, and the sign test is a binomial
tail. A normal approximation at n=20 is a needless loss of accuracy for
arithmetic this small. A test in ``tests/stats`` cross-checks every function
against scipy when scipy is importable, so the in-house arithmetic is validated
against the standard implementation without depending on it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import comb
from typing import Any

import numpy as np

#: Above this many pairs the exact signed-rank distribution stops being worth
#: computing and the normal approximation is used instead. The gold set has 20.
EXACT_LIMIT = 50


@dataclass(frozen=True, slots=True)
class TestResult:
    """One comparison. Every field is reported; none is optional."""

    name: str
    n: int
    mean_difference: float | None
    ci_low: float | None
    ci_high: float | None
    p_value: float | None
    effect_size: float | None
    test: str
    #: Questions whose difference was exactly zero. Dropped by both tests, and
    #: reported because "no difference on 14 of 20" is a finding that a p-value
    #: computed over the other 6 does not carry.
    n_ties: int = 0
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "n": self.n,
            "mean_difference": self.mean_difference,
            "ci_low": self.ci_low,
            "ci_high": self.ci_high,
            "p_value": self.p_value,
            "effect_size": self.effect_size,
            "test": self.test,
            "n_ties": self.n_ties,
            "note": self.note,
        }


def _clean(differences: Sequence[float | None]) -> np.ndarray:
    return np.array([d for d in differences if d is not None], dtype=float)


def average_ranks(values: np.ndarray) -> np.ndarray:
    """Ranks of ``values``, ties sharing their average rank.

    Average ranks are what make the signed-rank statistic well defined when two
    differences are the same size, which on a 1-5 scale is the normal case
    rather than an edge case.
    """
    order = values.argsort(kind="mergesort")
    ranks = np.empty(values.size, dtype=float)
    ranks[order] = np.arange(1, values.size + 1, dtype=float)
    unique, inverse, counts = np.unique(values, return_inverse=True, return_counts=True)
    sums = np.zeros(unique.size, dtype=float)
    np.add.at(sums, inverse, ranks)
    return (sums / counts)[inverse]


def _signed_rank_null(scaled_ranks: np.ndarray) -> np.ndarray:
    """Exact distribution of W+ under the null, as probabilities.

    Under H0 the differences are symmetric about zero, so each rank joins W+ or
    W- with probability one half, independently. The distribution of the sum is
    therefore a convolution -- one pass per rank over an array indexed by the
    achievable totals. Ranks are doubled before this is called so that averaged
    (half-integer) ranks index an integer array exactly.
    """
    total = int(scaled_ranks.sum())
    distribution = np.zeros(total + 1, dtype=float)
    distribution[0] = 1.0
    for rank in scaled_ranks.astype(int):
        shifted = np.zeros_like(distribution)
        shifted[rank:] = distribution[: distribution.size - rank]
        distribution = 0.5 * distribution + 0.5 * shifted
    return distribution


def wilcoxon_signed_rank(differences: Sequence[float | None]) -> tuple[float | None, float | None]:
    """Two-sided exact Wilcoxon signed-rank test. Returns ``(p, rank_biserial)``.

    Zero differences are dropped and n reduced -- the ``wilcox`` convention.
    They carry no evidence about direction, and keeping them would shrink every
    rank toward the middle and understate an effect that is real on the
    questions where anything happened at all.
    """
    values = _clean(differences)
    values = values[values != 0.0]
    n = values.size
    if n == 0:
        return None, None

    ranks = average_ranks(np.abs(values))
    positive = float(ranks[values > 0].sum())
    negative = float(ranks[values < 0].sum())
    # Matched-pairs rank-biserial: +1 when every difference favours b, -1 when
    # every one favours a, 0 when the ranks balance.
    effect = (positive - negative) / (positive + negative) if positive + negative else 0.0

    if n <= EXACT_LIMIT:
        scaled = np.rint(ranks * 2).astype(int)
        distribution = _signed_rank_null(scaled)
        statistic = int(round(positive * 2))
        lower = float(distribution[: statistic + 1].sum())
        upper = float(distribution[statistic:].sum())
        return float(min(1.0, 2.0 * min(lower, upper))), effect

    mean = n * (n + 1) / 4.0
    variance = n * (n + 1) * (2 * n + 1) / 24.0
    z = (positive - mean) / float(np.sqrt(variance))
    from math import erfc, sqrt

    return float(min(1.0, erfc(abs(z) / sqrt(2.0)))), effect


def binomial_two_sided(successes: int, trials: int) -> float:
    """Exact two-sided binomial tail at p=0.5, by summing outcomes no more likely."""
    if trials <= 0:
        return 1.0
    observed = comb(trials, successes)
    total = sum(comb(trials, k) for k in range(trials + 1) if comb(trials, k) <= observed)
    return min(1.0, total / 2.0**trials)


def sign_test(differences: Sequence[float | None]) -> tuple[float | None, float | None, int]:
    """Exact sign test. Returns ``(p, effect, n_ties)``.

    For a 0/1 outcome measured once per condition this *is* McNemar's exact
    test: the discordant pairs are the non-zero differences, and the test asks
    whether they split evenly. Here each difference is averaged over the other
    two factors first, so it takes values on a grid rather than in {-1, 0, 1};
    the sign test generalises to that unchanged, while McNemar's 2x2 table does
    not. See :func:`mcnemar_exact` for the single-cell case.
    """
    values = _clean(differences)
    ties = int((values == 0.0).sum())
    values = values[values != 0.0]
    n = values.size
    if n == 0:
        return None, None, ties
    positive = int((values > 0).sum())
    # Effect on the same scale as the rank-biserial: the share favouring b,
    # rescaled to [-1, 1].
    effect = 2.0 * positive / n - 1.0
    return binomial_two_sided(positive, n), effect, ties


def mcnemar_exact(favouring_b: int, favouring_a: int) -> float:
    """McNemar's exact test on discordant counts. The sign test, named for its use."""
    return binomial_two_sided(favouring_b, favouring_b + favouring_a)


def bootstrap_ci(
    differences: Sequence[float | None],
    resamples: int = 10000,
    seed: int = 0,
    confidence: float = 0.95,
) -> tuple[float | None, float | None, float | None]:
    """Percentile CI for the mean difference, resampling **questions**.

    Questions are the independent unit, so they are what gets resampled.
    Resampling the 8 configurations instead -- or the 160 answers -- would treat
    measurements of the same question as independent observations and produce an
    interval far too narrow.
    """
    values = _clean(differences)
    if values.size == 0:
        return None, None, None
    mean = float(values.mean())
    if values.size == 1:
        return mean, None, None
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, values.size, size=(resamples, values.size))
    means = values[draws].mean(axis=1)
    tail = (1.0 - confidence) / 2.0
    low, high = np.quantile(means, [tail, 1.0 - tail])
    return mean, float(low), float(high)


def holm(
    p_values: dict[str, float | None],
    alpha: float = 0.05,
    family_size: int | None = None,
) -> dict[str, dict[str, Any]]:
    """Holm-Bonferroni across a pre-specified family.

    Uniformly more powerful than Bonferroni and just as free of assumptions
    about dependence, which matters here because the primary metrics are
    measured on the same 20 questions and are certainly not independent.

    **The family is the one that was pre-specified, not the one that happens to
    be computable.** ``family_size`` defaults to every entry passed in,
    including those whose p-value is ``None`` because their data has not arrived
    yet. Correcting against only the computable tests would make the correction
    depend on how far the run has got: with judging a quarter done, a retrieval
    p of 0.01 in a family of six would be corrected against two and come out
    significant, then be corrected against six when judging finished and stop
    being significant -- the same measurement, two verdicts, decided by
    progress. That is precisely the data-dependent choice pre-specification
    exists to rule out, so the full family is used from the first report.
    """
    usable = {name: p for name, p in p_values.items() if p is not None}
    ordered = sorted(usable.items(), key=lambda item: item[1])
    size = family_size if family_size is not None else len(p_values)
    out: dict[str, dict[str, Any]] = {}
    running = 0.0
    for position, (name, p) in enumerate(ordered):
        adjusted = min(1.0, max(running, (size - position) * p))
        running = adjusted
        out[name] = {
            "p_value": p,
            "p_holm": adjusted,
            "significant": adjusted <= alpha,
            "rank": position + 1,
        }
    for name, p in p_values.items():
        if p is None:
            out[name] = {"p_value": None, "p_holm": None, "significant": False, "rank": None}
    return out
