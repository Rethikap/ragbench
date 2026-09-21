"""Turning 8 configurations x 20 questions into 20 paired differences.

**The 4 configuration pairs are not 80 observations.** For a factor with two
levels there are four ways to hold the other two factors fixed, so four paired
comparisons per question -- but all four are measured on the *same* question.
Pooling them into 80 rows treats one question's four comparisons as four
independent pieces of evidence.

How badly that misleads depends on how much of a difference is shared within a
question, and it is worth being exact about it rather than waving at "n=80".
If the four differences for a question varied only by independent per-cell
noise, pooling would be harmless -- averaging four and dividing by sqrt(20) is
the same arithmetic as dividing by sqrt(80). The damage comes from the part
that does *not* average away: a real effect is heterogeneous, helping some
questions and not others, and that per-question component is identical in all
four pairs. Pooling then counts it four times, and the interval comes out about
half the width it should be. Since effect heterogeneity is exactly what a
20-question gold set has most of, that is the case to design for.
`tests/stats/test_design.py` measures the gap on constructed data.

So each factor's effect on a question is the **average of its four paired
differences**, giving one number per question and twenty in total. That average
is the main effect of the factorial design: it is what "averaging over the other
factors" means, and the questions -- not the configurations -- are the
independent unit throughout.

A question contributes only when **every** cell it needs is present. A partially
judged run would otherwise average over four cells for one question and one cell
for another, which are different estimators wearing one name. `n` is reported
per comparison and the missing configurations are named.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from itertools import product
from typing import Any

from ..retrieval.pipeline import config_name

#: The order `config_name` takes its arguments in. Everything here addresses a
#: cell by a {factor: level} mapping rather than by position, so adding a factor
#: does not silently transpose two of them.
FACTOR_ORDER: tuple[str, ...] = ("chunking", "embedding", "rerank")


def factor_levels(resolved: Mapping[str, Any], factor: str) -> tuple[str, ...]:
    """Levels of one factor, in the order `factors.yaml` declares them.

    Order decides the sign of every difference reported for that factor, so it
    is taken from config rather than sorted: `b - a` is stated in the label.
    """
    try:
        return tuple(str(level) for level in resolved["factors"][factor])
    except KeyError:
        known = ", ".join(sorted(resolved["factors"]))
        raise ValueError(f"unknown factor {factor!r}; known: {known}") from None


def cell_name(levels: Mapping[str, str]) -> str:
    """The configuration named by one level of every factor."""
    return config_name(*(levels[factor] for factor in FACTOR_ORDER))


def _other_factors(factor: str) -> tuple[str, ...]:
    return tuple(name for name in FACTOR_ORDER if name != factor)


def _combinations(
    resolved: Mapping[str, Any], factors: Sequence[str]
) -> list[dict[str, str]]:
    levels = [factor_levels(resolved, name) for name in factors]
    return [dict(zip(factors, combo, strict=True)) for combo in product(*levels)]


class Differences:
    """One factor's paired differences, and an honest account of what is missing."""

    __slots__ = ("factor", "metric", "label", "pairs", "missing", "n_cells")

    def __init__(
        self,
        factor: str,
        metric: str,
        label: str,
        pairs: list[tuple[str, float]],
        missing: dict[str, list[str]],
        n_cells: int,
    ) -> None:
        self.factor = factor
        self.metric = metric
        self.label = label
        self.pairs = pairs
        self.missing = missing
        self.n_cells = n_cells

    @property
    def values(self) -> list[float]:
        return [value for _, value in self.pairs]

    @property
    def query_ids(self) -> list[str]:
        return [query_id for query_id, _ in self.pairs]

    @property
    def complete(self) -> bool:
        return not self.missing

    def to_dict(self) -> dict[str, Any]:
        return {
            "factor": self.factor,
            "metric": self.metric,
            "label": self.label,
            "n": len(self.pairs),
            "cells_averaged": self.n_cells,
            "complete": self.complete,
            "missing_configs": sorted(self.missing),
            "n_questions_dropped": len({q for ids in self.missing.values() for q in ids}),
        }


Table = Mapping[tuple[str, str], Mapping[str, float | None]]


def _lookup(table: Table, config: str, query_id: str, metric: str) -> float | None:
    row = table.get((config, query_id))
    if row is None:
        return None
    value = row.get(metric)
    return None if value is None else float(value)


def main_effect(
    resolved: Mapping[str, Any],
    table: Table,
    factor: str,
    metric: str,
    query_ids: Sequence[str],
) -> Differences:
    """One difference per question: level b minus level a, averaged over the rest."""
    levels = factor_levels(resolved, factor)
    if len(levels) != 2:
        raise ValueError(
            f"factor {factor!r} has {len(levels)} levels; a paired difference needs two"
        )
    low, high = levels
    others = _other_factors(factor)
    combinations = _combinations(resolved, others)

    pairs: list[tuple[str, float]] = []
    missing: dict[str, list[str]] = {}
    for query_id in query_ids:
        # Every cell is inspected before anything is decided. Stopping at the
        # first gap would name one absent configuration and stay silent about
        # the rest, and "which comparisons are incomplete" is the question this
        # bookkeeping exists to answer.
        values: dict[tuple[int, str], float] = {}
        absent = False
        for index, combo in enumerate(combinations):
            for level in (low, high):
                name = cell_name({**combo, factor: level})
                value = _lookup(table, name, query_id, metric)
                if value is None:
                    missing.setdefault(name, []).append(query_id)
                    absent = True
                else:
                    values[(index, level)] = value
        if absent:
            continue
        differences = [
            values[(index, high)] - values[(index, low)]
            for index in range(len(combinations))
        ]
        pairs.append((query_id, sum(differences) / len(differences)))
    return Differences(
        factor=factor,
        metric=metric,
        label=f"{high} - {low}",
        pairs=pairs,
        missing=missing,
        n_cells=len(combinations),
    )


def interaction(
    resolved: Mapping[str, Any],
    table: Table,
    first_factor: str,
    second_factor: str,
    metric: str,
    query_ids: Sequence[str],
) -> Differences:
    """The 2x2 interaction contrast, averaged over the remaining factor.

    ``(b|B - a|B) - (b|A - a|A)``: how much the effect of one factor changes
    when the other is switched. Reported with an interval and **labelled
    exploratory**: twenty questions cannot support an interaction claim, because
    an interaction contrast is a difference of differences and carries roughly
    twice the variance of either main effect it is built from. It is here so the
    write-up can say the data do not settle it, which is a different statement
    from not having looked.
    """
    first_levels = factor_levels(resolved, first_factor)
    second_levels = factor_levels(resolved, second_factor)
    if len(first_levels) != 2 or len(second_levels) != 2:
        raise ValueError("an interaction contrast needs two levels of each factor")
    remaining = tuple(
        name for name in FACTOR_ORDER if name not in (first_factor, second_factor)
    )
    combinations = _combinations(resolved, remaining)

    low_first, high_first = first_levels
    low_second, high_second = second_levels
    pairs: list[tuple[str, float]] = []
    missing: dict[str, list[str]] = {}
    for query_id in query_ids:
        # As in `main_effect`: inspect every cell before deciding anything, so
        # the missing list names all of them rather than only the first.
        corners: dict[tuple[int, str, str], float] = {}
        absent = False
        for index, combo in enumerate(combinations):
            for one in first_levels:
                for two in second_levels:
                    name = cell_name({**combo, first_factor: one, second_factor: two})
                    value = _lookup(table, name, query_id, metric)
                    if value is None:
                        missing.setdefault(name, []).append(query_id)
                        absent = True
                    else:
                        corners[(index, one, two)] = value
        if absent:
            continue
        contrasts = [
            (corners[(index, high_first, high_second)] - corners[(index, low_first, high_second)])
            - (corners[(index, high_first, low_second)] - corners[(index, low_first, low_second)])
            for index in range(len(combinations))
        ]
        pairs.append((query_id, sum(contrasts) / len(contrasts)))
    return Differences(
        factor=f"{first_factor} x {second_factor}",
        metric=metric,
        label=(
            f"effect of {first_factor} under {second_levels[1]}"
            f" minus under {second_levels[0]}"
        ),
        pairs=pairs,
        missing=missing,
        n_cells=len(combinations),
    )
