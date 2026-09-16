"""The budget fill. This is invariant I1, so these are the load-bearing tests.

What they hold down: the number of chunks in the context is an OUTPUT. No
function in the retrieval package accepts a count of chunks to return, and the
fill stops at the first candidate that will not fit rather than truncating it or
skipping past it.
"""

from __future__ import annotations

import inspect
import re

import pytest

from ragbench import retrieval
from ragbench.retrieval.budget import (
    STOPPED_EMPTY,
    STOPPED_EXHAUSTED,
    STOPPED_OVERFLOW,
    fill_to_budget,
)

#: Names that would express "give me N chunks". Mirrors the guard on the CLI:
#: the concept must be inexpressible at the interface, not merely unused.
BANNED = re.compile(
    r"^(top_?k|k|n|num_?\w*|n_\w*chunks?|max_?chunks?|limit|count|first)$|"
    r"^(top|num|n|max|first)_?(k|chunks?|docs?|documents?|passages?|results?|hits?)$"
)


def cost_of(item: tuple[str, int]) -> int:
    return item[1]


def items(*costs: int) -> list[tuple[str, int]]:
    return [(f"c{i}", cost) for i, cost in enumerate(costs)]


# --------------------------------------------------------------- invariant I1


def test_no_function_in_the_retrieval_package_takes_a_chunk_count() -> None:
    """The structural guard. A `top_k` parameter anywhere here would make the
    wrong experiment expressible, and holding k constant instead of the budget
    would confound chunk size with context size -- which is the whole point of
    the design."""
    offenders: list[str] = []
    for name in retrieval.__all__:
        attribute = getattr(retrieval, name)
        if not callable(attribute):
            continue
        for parameter in inspect.signature(attribute).parameters:
            if BANNED.match(parameter):
                offenders.append(f"{name}({parameter})")
    assert offenders == []


def test_the_chunk_count_is_whatever_fitted() -> None:
    """Same budget, different chunk sizes, different counts -- and the count was
    never asked for."""
    coarse = fill_to_budget(items(500, 500, 500, 500), cost_of, budget=1000)
    fine = fill_to_budget(items(100, 100, 100, 100, 100, 100, 100, 100), cost_of, budget=1000)
    assert len(coarse.selected) == 2
    assert len(fine.selected) == 8
    assert coarse.tokens_used == 1000
    assert fine.tokens_used == 800


# ------------------------------------------------------------- stop_at_overflow


def test_the_fill_stops_at_the_first_chunk_that_does_not_fit() -> None:
    """Not skip-and-continue: packing a smaller chunk in behind an over-large one
    would make the context a function of the size distribution rather than of the
    ranking."""
    filled = fill_to_budget(items(400, 400, 900, 100), cost_of, budget=1000)
    assert [identifier for identifier, _ in filled.selected] == ["c0", "c1"]
    assert filled.stopped_reason == STOPPED_OVERFLOW
    assert filled.tokens_used == 800


def test_no_chunk_is_ever_truncated_to_make_it_fit() -> None:
    """A half-chunk is not the unit either chunker produced."""
    filled = fill_to_budget(items(1500), cost_of, budget=1000)
    assert filled.selected == []
    assert filled.tokens_used == 0
    assert filled.stopped_reason == STOPPED_OVERFLOW


def test_a_chunk_that_exactly_fills_the_budget_is_taken() -> None:
    filled = fill_to_budget(items(1000), cost_of, budget=1000)
    assert len(filled.selected) == 1
    assert filled.tokens_used == 1000


def test_running_out_of_candidates_is_a_different_reason_from_overflowing() -> None:
    """The distribution of these across a run says whether the budget or the
    candidate pool was the binding constraint, and those are different
    experiments."""
    assert fill_to_budget(items(10, 10), cost_of, 1000).stopped_reason == STOPPED_EXHAUSTED
    assert fill_to_budget(items(10, 2000), cost_of, 1000).stopped_reason == STOPPED_OVERFLOW
    assert fill_to_budget([], cost_of, 1000).stopped_reason == STOPPED_EMPTY


def test_the_fill_never_exceeds_the_budget() -> None:
    for budget in (0, 1, 99, 100, 101, 1000):
        filled = fill_to_budget(items(30, 70, 50, 200, 10), cost_of, budget)
        assert filled.tokens_used <= budget


def test_rank_order_is_preserved() -> None:
    """The fill walks the ranked list; it does not reorder it to pack better."""
    filled = fill_to_budget(items(300, 300, 300), cost_of, budget=1000)
    assert [identifier for identifier, _ in filled.selected] == ["c0", "c1", "c2"]


def test_an_unknown_fill_policy_is_refused() -> None:
    with pytest.raises(ValueError, match="fill_policy"):
        fill_to_budget(items(10), cost_of, 100, policy="truncate_to_fit")


def test_the_result_carries_why_it_stopped() -> None:
    selected, tokens, reason = fill_to_budget(items(400, 900), cost_of, 1000)
    assert len(selected) == 1
    assert tokens == 400
    assert reason == STOPPED_OVERFLOW
