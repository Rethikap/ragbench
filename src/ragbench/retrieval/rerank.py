"""The rerank factor: a cross-encoder, or nothing at all.

The `off` level is not a degenerate reranker that returns the dense order — it
is the absence of a stage, and :class:`NoReranker` exists so the pipeline has
one shape rather than two. What it must not do is cost anything or reorder
anything, and a test holds it to both.

`on` is `BAAI/bge-reranker-base` over the configured candidate depth. The depth
is a *candidate pool* size, not a context size: reranking 30 dense hits changes
their order, and how many of them reach the generator is still decided by the
token budget (I1).

Same shape as the embedders: torch is imported inside the constructor, and a
deterministic CPU stand-in keeps the whole pipeline runnable offline.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from typing import Any, Protocol

WORD = re.compile(r"[A-Za-z0-9]+")


class Reranker(Protocol):
    name: str
    enabled: bool

    def score(self, query: str, documents: Sequence[str]) -> list[float]:
        """Relevance of each document to the query, higher is better."""


class NoReranker:
    """The `off` level. Scores nothing and is never called by the pipeline."""

    name = "none"
    enabled = False

    def score(self, query: str, documents: Sequence[str]) -> list[float]:
        raise RuntimeError(
            "the rerank factor is off for this configuration; the pipeline must keep "
            "the dense order rather than ask a disabled reranker to reproduce it."
        )


class CrossEncoderReranker:
    """`BAAI/bge-reranker-base`, pinned. A cross-encoder: query and document are
    scored together, which is why it cannot be folded into the index."""

    enabled = True

    def __init__(self, params: Mapping[str, Any]) -> None:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        model_id = str(params["model_id"])
        revision = str(params.get("model_revision") or "")
        if not revision:
            raise ValueError(
                f"{model_id}: rerank.model_revision is required. A Hub id is a mutable "
                "pointer and the ranking is a function of the checkpoint behind it."
            )
        self._torch = torch
        self.name = f"{model_id}@{revision[:12]}"
        self.batch_size = int(params.get("batch_size", 16))
        self.max_seq_tokens = int(params.get("max_seq_tokens", 512))
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
        self._model = AutoModelForSequenceClassification.from_pretrained(
            model_id, revision=revision
        ).to(self._device)
        self._model.eval()

    def score(self, query: str, documents: Sequence[str]) -> list[float]:
        torch = self._torch
        scores: list[float] = []
        for start in range(0, len(documents), self.batch_size):
            batch = list(documents[start : start + self.batch_size])
            encoded = self._tokenizer(
                [query] * len(batch),
                batch,
                padding=True,
                truncation=True,
                max_length=self.max_seq_tokens,
                return_tensors="pt",
            ).to(self._device)
            with torch.no_grad():
                logits = self._model(**encoded).logits.view(-1).float()
            scores.extend(logits.cpu().tolist())
        return scores


class StandInReranker:
    """Offline stand-in: IDF-free lexical overlap, length-normalised.

    Deterministic, model-free, and it genuinely reorders — a stand-in that
    returned a constant would make the `on` and `off` arms indistinguishable and
    the rerank factor untestable offline. It is not a relevance model and must
    not be read as one.
    """

    name = "stand-in"
    enabled = True

    def __init__(self, params: Mapping[str, Any] | None = None) -> None:
        self._params = dict(params or {})

    def score(self, query: str, documents: Sequence[str]) -> list[float]:
        terms = set(WORD.findall(query.lower()))
        if not terms:
            return [0.0] * len(documents)
        scores: list[float] = []
        for document in documents:
            words = WORD.findall(document.lower())
            if not words:
                scores.append(0.0)
                continue
            hits = sum(1 for word in words if word in terms)
            # Divide by log length so a long chunk cannot win on volume alone.
            scores.append(hits / math.log(len(words) + math.e))
        return scores


def build_reranker(enabled: bool, params: Mapping[str, Any]) -> Reranker:
    """Construct the arm. ``model_id: stand-in`` selects the offline path."""
    if not enabled:
        return NoReranker()
    if str(params.get("model_id")) == "stand-in":
        return StandInReranker(params)
    return CrossEncoderReranker(params)
