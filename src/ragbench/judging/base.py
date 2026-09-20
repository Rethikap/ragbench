"""The judge, behind an interface: one hosted model, one CPU stand-in.

Same shape as the embedders and the generator. `requests` is imported inside the
real client's module, the stand-in is selected by ``model_id``, and the whole
stage is exercisable offline.

**The judge is not the generator, and that is a requirement rather than a
preference.** Qwen2.5-7B produced these answers; asking it to grade them would
stack self-preference bias -- models score their own output higher -- on top of
the unreliability the LLM-as-judge literature reports for small judges. The two
are not separable after the fact, so the judge is a different family and an
order of magnitude larger, pinned by its full slug.

What this module owns is the *shape* of a verdict: which scales exist, which
verdicts are permitted, and what an abstention means. Everything about wording
lives in config, so editing the rubric moves the run id.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

#: The system declined to answer. Recorded, never scored -- see `Verdict`.
ABSTAINED = "abstained"
#: The judge returned something that was not the schema, twice.
UNPARSED = "unparsed"


class JudgeError(Exception):
    """The judge could not be reached, or refused the request outright."""


@dataclass(frozen=True, slots=True)
class Verdict:
    """One parsed judgement: three scales, a category, and why.

    ``scores`` is empty for an abstention. An abstention asserts nothing, so it
    cannot be unfaithful; giving it 5s would reward a configuration for failing
    to retrieve. It is counted separately instead.
    """

    verdict: str
    scores: dict[str, float] = field(default_factory=dict)
    rationale: str = ""
    n_parse_retries: int = 0

    @property
    def scored(self) -> bool:
        return bool(self.scores)


class Judge(Protocol):
    name: str

    def score(self, prompt: Any) -> Verdict:
        """Grade one answer from a rendered :class:`~ragbench.judging.prompt.JudgePrompt`.

        Raises :class:`JudgeError` if the judge is unreachable or refuses the
        request outright; a reply that is merely not the schema is retried once
        inside the implementation and then raises ``ValueError``.
        """


def judge_params(resolved: Mapping[str, Any]) -> dict[str, Any]:
    """Judge settings: ``base.judge``, whole.

    Judging is not a factor, for the reason generation is not: one judge, one
    rubric, one temperature across all 8 cells. What varies is the answers.
    """
    return dict(resolved["base"]["judge"])


def scales(params: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(str(name) for name in params["scales"])


def verdicts(params: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(str(name) for name in params["verdicts"])


def parse_verdict(payload: Mapping[str, Any], params: Mapping[str, Any]) -> Verdict:
    """Validate one decoded JSON object against the rubric's own vocabulary.

    Strict on purpose. A judge that returns ``"verdict": "good"`` or a 7 on a
    five-point scale has not followed the rubric, and quietly coercing it would
    put a number in the results that no rubric defines. The caller retries once
    and then records the item as unparsed and counts it.
    """
    found = str(payload.get("verdict", "")).strip().lower().replace(" ", "_")
    permitted = verdicts(params)
    if found not in permitted:
        raise ValueError(f"verdict {found!r} is not one of {', '.join(permitted)}")

    if found == ABSTAINED:
        # Scales are ignored rather than rejected: a judge that fills them in
        # anyway has still classified the item correctly, and the rubric says
        # an abstention is not scored.
        return Verdict(verdict=found, rationale=str(payload.get("rationale", "")).strip())

    scored: dict[str, float] = {}
    for name in scales(params):
        value = payload.get(name)
        if value is None:
            raise ValueError(f"{name} is null for verdict {found!r}; only an abstention may be")
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{name} is {value!r}, not a number") from None
        if not 1 <= number <= 5:
            raise ValueError(f"{name} is {number}, outside the 1-5 scale")
        scored[name] = number
    return Verdict(
        verdict=found, scores=scored, rationale=str(payload.get("rationale", "")).strip()
    )


def build_judge(params: Mapping[str, Any], **runtime: Any) -> Judge:
    """Construct the judge named by ``model_id``, or the offline stand-in.

    Selected by id, never by a flag, so a config naming the real judge cannot
    quietly fall back to a stand-in whose scores mean nothing.
    """
    if str(params["model_id"]) == "stand-in":
        from .standin import StandInJudge

        return StandInJudge(params)
    provider = str(params.get("provider", "openrouter"))
    if provider != "openrouter":
        raise JudgeError(f"unknown judge provider {provider!r}; only 'openrouter' is built")
    from .openrouter import OpenRouterJudge

    return OpenRouterJudge(params, **runtime)


class LazyJudge:
    """One judge, built on first use, shared across all 8 configurations.

    Two reasons it is lazy rather than eager. The rate limiter lives on the
    client, so building one per configuration would reset the pacing clock eight
    times and let eight requests through unspaced. And constructing the real
    judge reads the API key, which must not be required to re-run a stage that
    has nothing left to do -- a finished run should not fail for want of a
    credential it will never use.
    """

    def __init__(self, params: dict[str, Any]) -> None:
        self._params = params
        self._judge: Any = None

    @property
    def name(self) -> str:
        return getattr(self._judge, "name", "not built (nothing needed judging)")

    def score(self, prompt: Any) -> Verdict:
        if self._judge is None:
            self._judge = build_judge(self._params)
        return self._judge.score(prompt)


def mean_scores(rows: Sequence[Mapping[str, Any]], names: Sequence[str]) -> dict[str, float]:
    """Means over the judged rows only. Abstentions carry no scores and so drop out."""
    result: dict[str, float] = {}
    for name in names:
        values = [float(row[name]) for row in rows if row.get(name) is not None]
        result[name] = round(sum(values) / len(values), 3) if values else 0.0
    return result
