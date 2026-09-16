"""Filling the context to a constant token budget. This is invariant I1.

Every configuration puts the same number of *generator tokens* in front of the
model. It does not put the same number of chunks there. A coarse chunker fills
the budget with fewer, larger chunks; a fine one with more, smaller ones — and
how many it took is a **result**, recorded on the way out, never a parameter
handed in.

So there is no `k` in this module, and there must never be one. The signature
takes a ranked list, a cost function and a budget; what comes back is however
much of that list fitted. A function here that took a count and returned that
many chunks would make the wrong experiment expressible, and the CLI would not
be able to stop someone calling it.

The budget is measured with the **generator's** tokenizer, because it is the
generator's context that is being controlled. The cost function is passed in so
this module cannot reach for the wrong one.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeVar

#: Why the fill stopped. Recorded per query: the distribution of these across a
#: run says whether the budget or the candidate pool was the binding constraint,
#: and those are very different experiments.
STOPPED_OVERFLOW = "overflow"
STOPPED_EXHAUSTED = "candidates_exhausted"
STOPPED_EMPTY = "no_candidates"

FILL_POLICIES = ("stop_at_overflow",)

Item = TypeVar("Item")


class Filled(tuple):
    """What the fill produced: the items taken, the tokens they cost, and why it
    stopped. A tuple subclass so it unpacks, with names so it reads."""

    __slots__ = ()

    def __new__(cls, selected: list, tokens_used: int, stopped_reason: str) -> Filled:
        return super().__new__(cls, (selected, tokens_used, stopped_reason))

    @property
    def selected(self) -> list:
        return self[0]

    @property
    def tokens_used(self) -> int:
        return self[1]

    @property
    def stopped_reason(self) -> str:
        return self[2]


def fill_to_budget(
    candidates: Sequence[Item],
    cost: Callable[[Item], int],
    budget: int,
    policy: str = "stop_at_overflow",
) -> Filled:
    """Walk the ranked list, taking chunks until the next one will not fit.

    ``stop_at_overflow`` is the configured policy and the only one implemented:
    the first candidate that does not fit ends the fill, and **no chunk is ever
    truncated to make it fit**. Truncating would quietly change what the
    experiment is comparing — a half-chunk is not the unit either chunker
    produced — and skipping past an over-large chunk to pack a smaller one
    behind it would make the context a function of the size distribution rather
    than of the ranking.

    Returns the items taken, their cost, and why it stopped. The number of items
    is not an argument and is not checked against one; it is the answer.
    """
    if policy not in FILL_POLICIES:
        raise ValueError(
            f"retrieval.fill_policy is {policy!r}; known: {', '.join(FILL_POLICIES)}. "
            "stop_at_overflow is what the design specifies (I1)."
        )
    if not candidates:
        return Filled([], 0, STOPPED_EMPTY)

    selected: list[Item] = []
    used = 0
    for item in candidates:
        price = cost(item)
        if used + price > budget:
            return Filled(selected, used, STOPPED_OVERFLOW)
        selected.append(item)
        used += price
    return Filled(selected, used, STOPPED_EXHAUSTED)
