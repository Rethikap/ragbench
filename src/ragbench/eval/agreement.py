"""Agreement between two sets of ratings: kappa, and Spearman.

Used for two different comparisons that need the same arithmetic -- the judge
against itself across its two passes, and the judge against a human on the blind
calibration sample.

**Raw percentage agreement is not reported alone, and that is the point of this
module.** On a 5-point scale where most answers are good, two raters who never
looked at anything would still agree a third of the time, and on a verdict
distribution as skewed as this one they would agree more often than that. Cohen's
kappa subtracts the agreement expected from the marginals; the quadratic
weighting makes a 4-against-5 disagreement count for far less than a 1-against-5,
which is what an ordinal scale means. A reviewer will ask for exactly this.

Spearman is reported beside kappa because they can disagree in a way that
matters: a judge scoring everything one point lower than the human ranks the
answers identically (high rho) while agreeing with almost none of them (low
kappa). That is a calibration offset, not a disagreement about quality, and the
fix for it is different.

numpy only. No new dependency for two textbook formulas.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def _paired(left: Sequence[float | None], right: Sequence[float | None]) -> tuple:
    """Rows where both raters produced a score. Anything else is not a disagreement."""
    if len(left) != len(right):
        raise ValueError(f"unequal lengths: {len(left)} and {len(right)}")
    pairs = [(a, b) for a, b in zip(left, right, strict=True) if a is not None and b is not None]
    if not pairs:
        return np.array([]), np.array([])
    first, second = zip(*pairs, strict=True)
    return np.array(first, dtype=float), np.array(second, dtype=float)


def cohens_kappa(
    left: Sequence[float | None],
    right: Sequence[float | None],
    categories: Sequence[float] | None = None,
    weights: str = "quadratic",
) -> float | None:
    """Cohen's kappa. ``weights`` is ``quadratic``, ``linear`` or ``none``.

    Returns ``None`` when there is nothing to compare, and ``1.0`` when both
    raters were constant and identical -- a degenerate case where the formula is
    0/0 because the expected agreement is also total.
    """
    first, second = _paired(left, right)
    if first.size == 0:
        return None

    levels = sorted({float(v) for v in categories} if categories else set(first) | set(second))
    index = {value: position for position, value in enumerate(levels)}
    size = len(levels)
    if size == 1:
        return 1.0

    observed = np.zeros((size, size), dtype=float)
    for a, b in zip(first, second, strict=True):
        observed[index[float(a)], index[float(b)]] += 1
    observed /= observed.sum()

    rows = observed.sum(axis=1)
    columns = observed.sum(axis=0)
    expected = np.outer(rows, columns)

    grid = np.array(levels, dtype=float)
    if weights == "none":
        penalty = 1.0 - np.eye(size)
    else:
        difference = np.abs(grid[:, None] - grid[None, :])
        span = grid[-1] - grid[0]
        penalty = (difference / span) ** 2 if weights == "quadratic" else difference / span

    numerator = float((penalty * observed).sum())
    denominator = float((penalty * expected).sum())
    if denominator == 0:
        # Both raters constant. Either they agree (kappa 1) or the penalty
        # matrix could not be built, which the size==1 branch already handled.
        return 1.0 if numerator == 0 else 0.0
    return round(1.0 - numerator / denominator, 4)


def _ranks(values: np.ndarray) -> np.ndarray:
    """Average ranks, so ties do not distort rho. Ties are the normal case here."""
    order = values.argsort(kind="mergesort")
    ranks = np.empty(values.size, dtype=float)
    ranks[order] = np.arange(1, values.size + 1, dtype=float)
    _, inverse, counts = np.unique(values, return_inverse=True, return_counts=True)
    sums = np.zeros(counts.size, dtype=float)
    np.add.at(sums, inverse, ranks)
    return (sums / counts)[inverse]


def spearman(left: Sequence[float | None], right: Sequence[float | None]) -> float | None:
    """Spearman's rho: Pearson on average ranks. ``None`` if either side is constant."""
    first, second = _paired(left, right)
    if first.size < 2:
        return None
    a, b = _ranks(first), _ranks(second)
    a_centred, b_centred = a - a.mean(), b - b.mean()
    denominator = float(np.sqrt((a_centred**2).sum() * (b_centred**2).sum()))
    if denominator == 0:
        return None
    return round(float((a_centred * b_centred).sum()) / denominator, 4)


def exact_agreement(left: Sequence[float | None], right: Sequence[float | None]) -> float | None:
    """Share of pairs that match exactly. Reported only beside kappa."""
    first, second = _paired(left, right)
    if first.size == 0:
        return None
    return round(float((first == second).mean()), 4)


def within_one(left: Sequence[float | None], right: Sequence[float | None]) -> float | None:
    """Share of pairs within one point. The looser reading of an ordinal scale."""
    first, second = _paired(left, right)
    if first.size == 0:
        return None
    return round(float((np.abs(first - second) <= 1).mean()), 4)


def agreement_summary(
    left: Sequence[float | None],
    right: Sequence[float | None],
    categories: Sequence[float] | None = None,
    ordinal: bool = True,
) -> dict[str, float | None]:
    """Every figure at once, for one scale or for the verdict.

    ``ordinal=False`` for the verdict, where the four categories have no order
    and a weighted kappa would invent one.
    """
    return {
        "n": int(_paired(left, right)[0].size),
        "exact_agreement": exact_agreement(left, right),
        "within_one": within_one(left, right) if ordinal else None,
        "kappa": cohens_kappa(
            left, right, categories, weights="quadratic" if ordinal else "none"
        ),
        "spearman": spearman(left, right) if ordinal else None,
    }
