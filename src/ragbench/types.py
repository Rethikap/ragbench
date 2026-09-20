"""Core record types passed between stages.

All records are frozen dataclasses with a JSON round-trip, because every stage
writes JSONL to disk for resumability and the files must be byte-stable.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any


def _as_dict(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: _as_dict(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, (list, tuple)):
        return [_as_dict(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _as_dict(v) for k, v in obj.items()}
    return obj


class JsonRecord:
    """Mixin giving frozen dataclasses a dict round-trip."""

    def to_dict(self) -> dict[str, Any]:
        return _as_dict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        fields = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in fields})


# --------------------------------------------------------------------------- corpus


@dataclass(frozen=True, slots=True)
class SectionSpan(JsonRecord):
    """A section's extent within the concatenated body stream."""

    title: str
    sec_type: str
    depth: int
    char_start: int
    char_end: int


@dataclass(frozen=True, slots=True)
class ManifestEntry(JsonRecord):
    """One selected paper, frozen at corpus-selection time.

    `article_type` and `license_text` are audit fields: they make the manifest
    self-evidencing, so the two hard filters (research-article, CC-BY) can be
    verified from the manifest alone without re-fetching anything from NCBI.
    """

    pmcid: str
    doi: str | None
    title: str
    journal: str | None
    pub_date: str
    license_url: str
    source_url: str
    article_type: str
    license_text: str


@dataclass(frozen=True, slots=True)
class ParsedPaper(JsonRecord):
    """A PMC paper after JATS extraction. `body` is the single concatenated stream
    that both chunkers operate on; `sections` maps back into it."""

    pmcid: str
    doi: str | None
    title: str
    journal: str | None
    year: int | None
    article_type: str
    license_url: str
    license_text: str
    abstract: str
    body: str
    sections: tuple[SectionSpan, ...]
    source_sha256: str
    parser_version: str
    parse_metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ParsedPaper:
        data = dict(data)
        data["sections"] = tuple(SectionSpan(**s) for s in data.get("sections", ()))
        fields = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in fields})


# --------------------------------------------------------------------------- chunks


@dataclass(frozen=True, slots=True)
class Chunk(JsonRecord):
    chunk_id: str
    pmcid: str
    chunk_index: int
    text: str
    n_tokens: int
    char_start: int
    char_end: int
    sections: tuple[str, ...]
    content_sha256: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Chunk:
        data = dict(data)
        data["sections"] = tuple(data.get("sections", ()))
        fields = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in fields})


# --------------------------------------------------------------------------- queries


@dataclass(frozen=True, slots=True)
class GoldSpan(JsonRecord):
    """Where the answer lives: a character range in ``ParsedPaper.body``.

    A character span, never a chunk id. Chunk ids are arm-specific -- the same id
    names different text in the fixed and recursive chunk sets -- so a gold set
    labelled with them would be two incomparable gold sets wearing one name, and
    the across-arm comparison the experiment exists to make would be comparing
    each arm against its own private notion of correct. The body stream is the
    one representation both arms share. See invariant I5.

    Two ranges, and only one of them is the label:

    ``char_start``/``char_end``
        The **minimal evidence span**: the sentence or two that actually answer
        the question. This is the only range any metric may read.
    ``context_start``/``context_end``
        The paragraph the question was drafted from. Provenance only -- it says
        where the span came from, and lets a reader check the span in context.

    The distinction is a correction, not a refinement. Labelling the paragraph
    made the gold set an artefact of one arm's boundaries: paragraphs are
    exactly what the recursive chunker splits on, so it covered every span in
    one chunk by construction and the chunking effect could not be separated
    from the sampling unit. A minimal span belongs to no chunker's vocabulary.

    Per-arm relevant chunks are derived at eval time by offset overlap; nothing
    persists them.
    """

    pmcid: str
    char_start: int
    char_end: int
    section: str
    context_start: int
    context_end: int

    def __len__(self) -> int:
        """Length of the *evidence* span. Nothing measures the context."""
        return max(0, self.char_end - self.char_start)

    def __post_init__(self) -> None:
        if self.char_end <= self.char_start:
            raise ValueError(
                f"{self.pmcid}: empty evidence span ({self.char_start}..{self.char_end})"
            )
        if not (self.context_start <= self.char_start and self.char_end <= self.context_end):
            raise ValueError(
                f"{self.pmcid}: evidence span ({self.char_start}..{self.char_end}) is not "
                f"inside its context ({self.context_start}..{self.context_end})"
            )


@dataclass(frozen=True, slots=True)
class Query(JsonRecord):
    """One evaluation item: a question, its reference answer, and the passage the
    question was written from.

    ``reference_answer`` rather than ``answer`` because ``GeneratedAnswer.answer``
    is the other thing in this file, and the judge stage holds both at once.
    """

    query_id: str
    question: str
    reference_answer: str
    gold: GoldSpan
    #: What the judge must not penalise on this item: a source sentence the paper
    #: got wrong, a span that is one clause of a sentence a model will see whole.
    #: Frozen WITH the item rather than kept beside it, so the rubric cannot drift
    #: away from the label it applies to.
    judge_note: str = ""
    #: Set only by the author, having read the question, the answer and the span.
    #: `ragbench gold freeze` refuses to run while any selected record is False.
    verified: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Query:
        data = dict(data)
        data["gold"] = GoldSpan(**data["gold"])
        fields = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in fields})


# --------------------------------------------------------------------------- retrieval


@dataclass(frozen=True, slots=True)
class ScoredChunk(JsonRecord):
    chunk_id: str
    score: float
    rank: int
    n_budget_tokens: int = 0


@dataclass(frozen=True, slots=True)
class RetrievalResult(JsonRecord):
    """The record that carries the experiment's central measurement: how many
    chunks and how many tokens each configuration actually put in context."""

    query_id: str
    selected: tuple[ScoredChunk, ...]
    n_candidates: int
    n_chunks: int
    tokens_used: int
    token_budget: int
    budget_slack: int
    stopped_reason: str
    dense_latency_ms: float = 0.0
    rerank_latency_ms: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RetrievalResult:
        data = dict(data)
        data["selected"] = tuple(ScoredChunk(**s) for s in data.get("selected", ()))
        fields = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in fields})


# --------------------------------------------------------------------------- generation


@dataclass(frozen=True, slots=True)
class GeneratedAnswer(JsonRecord):
    """One answer, and enough about how it was produced to control for it later.

    ``prompt_sha256`` digests what the model actually saw -- the rendered system
    and user text, not the template it came from. It is what makes resumption
    safe: a record whose prompt no longer reproduces was generated under a
    different assembly, and the generate stage refuses to mix the two rather
    than leaving a run half-answered under each.

    ``finish_reason`` is the decode's own account of why it stopped, ``"stop"``
    for an end-of-turn token and ``"length"`` for the ``max_new_tokens`` ceiling.
    A ``"length"`` answer is cut off mid-sentence, which is a different object
    from a short answer -- the judge will mark it down for incompleteness that
    the generator never chose. Counting them is the only way to tell an arm that
    answers briefly from an arm that was truncated.

    ``n_completion_tokens`` is recorded for the same reason and is not a
    diagnostic: the judge literature reports a length bias, so answer length has
    to be measured per configuration if it is ever to be controlled for.
    """

    query_id: str
    answer: str
    prompt_sha256: str
    n_prompt_tokens: int
    n_completion_tokens: int
    latency_ms: float
    finish_reason: str = "stop"
    #: Chunks the context was assembled from, in the rank order they appeared.
    #: Retrieval already recorded these; repeating them here makes an answer
    #: readable on its own, which is what `report generation` needs to show a
    #: question's answers side by side without re-deriving the context.
    context_chunk_ids: tuple[str, ...] = ()
    n_context_chunks: int = 0
    from_cache: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GeneratedAnswer:
        data = dict(data)
        data["context_chunk_ids"] = tuple(data.get("context_chunk_ids", ()))
        fields = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in fields})


@dataclass(frozen=True, slots=True)
class Judgement(JsonRecord):
    """One judge pass over one answer.

    ``verdict`` sits beside ``scores`` rather than being derived from them,
    because one scale cannot separate the two failure modes in the output. A
    confident fabrication and a correct abstention are opposite outcomes that
    land in the same region of any single axis: the abstention makes no false
    claim, so it is faithful; the fabrication is fluent and on-topic, so it is
    relevant. The verdict carries the kind of failure and the scales carry the
    degree.

    ``scores`` is **empty for an abstention**, not full of fives. An abstention
    claims nothing and so cannot be unfaithful, and scoring it 5 would reward a
    configuration for retrieving badly. Means are taken over judged answers
    only, with the abstention rate reported separately and never folded in.

    ``pass_index`` numbers the repeated scorings of the same answer. Two passes
    at temperature 0 measure the judge against itself; a judge that disagrees
    with itself bounds how far any difference between configurations can be
    trusted, and that bound has to be measured rather than assumed.

    ``answer_sha256`` ties the judgement to the exact answer text it scored, the
    way ``GeneratedAnswer.prompt_sha256`` ties an answer to its prompt. The
    rubric lives in config and so moves the run id when edited; what that cannot
    catch is generation re-run underneath a directory that already holds
    judgements.
    """

    query_id: str
    scores: dict[str, float]
    rationale: str
    judge_model: str
    rubric_id: str
    verdict: str = ""
    pass_index: int = 0
    answer_sha256: str = ""
    #: Corrective retries spent before this parsed. >0 means the judge returned
    #: something that was not the schema at least once.
    n_parse_retries: int = 0
    #: Tokens this judgement cost, summed over every request it took -- so a
    #: judgement that needed a corrective retry shows the full price of both.
    #: Recorded because the daily cap is spent in these units, and the first
    #: real run had to have its per-call cost reconstructed from an aggregate.
    n_tokens: int = 0
    latency_ms: float = 0.0
    #: True when the abstention was recognised from the answer text and no API
    #: call was made. Those items cost nothing and contribute to no mean.
    from_refusal_match: bool = False
