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
class Query(JsonRecord):
    """One evaluation item. `gold_chunk_ids` is populated by the question-generation
    step, which records which passage the question was written from; it is what
    makes recall@budget computable."""

    query_id: str
    text: str
    reference_answer: str
    gold_pmcids: tuple[str, ...] = ()
    gold_chunk_ids: tuple[str, ...] = ()
    verified: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Query:
        data = dict(data)
        data["gold_pmcids"] = tuple(data.get("gold_pmcids", ()))
        data["gold_chunk_ids"] = tuple(data.get("gold_chunk_ids", ()))
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
    query_id: str
    answer: str
    prompt_sha256: str
    n_prompt_tokens: int
    n_completion_tokens: int
    latency_ms: float
    from_cache: bool = False


@dataclass(frozen=True, slots=True)
class Judgement(JsonRecord):
    query_id: str
    scores: dict[str, float]
    rationale: str
    judge_model: str
    rubric_id: str
