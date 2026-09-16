"""The CPU stand-in: a deterministic lexical projection, and nothing more.

It exists so the index stage is smoke-testable end to end on a laptop with no
GPU and no download -- the same reason `WhitespaceTokenizer` exists. It is a
hashing projection of a bag of words, so texts sharing vocabulary land near each
other and the retrieval path can be exercised with results that are not
nonsense. It is not a semantic model and must never be mistaken for one: it has
no notion of meaning, word order, or anything a sentence encoder is for.

Deterministic across processes and machines because every feature index comes
from :mod:`ragbench.hashing`, never from Python's salted builtin `hash` (I3).
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from ..hashing import sha256_text
from .base import normalise_rows

WORD = re.compile(r"[A-Za-z0-9]+")


class HashingEmbedder:
    """Bag-of-words feature hashing into a fixed-width vector.

    ``dimension`` is small by default: the point is to exercise the pipeline,
    and a 64-wide vector makes the on-disk index tiny enough to build and throw
    away inside a test.
    """

    def __init__(self, params: Mapping[str, Any]) -> None:
        self.dimension = int(params.get("dimension", 64))
        self.max_seq_tokens = int(params["max_seq_tokens"])
        self.normalize = bool(params.get("normalize", True))
        self.query_instruction = str(params.get("query_instruction", ""))
        self.name = f"stand-in:{self.dimension}"

    def content_tokens(self, text: str) -> int:
        """One token per word. Not a vocabulary -- just something to count, so the
        truncation accounting has the same shape as it does for a real arm."""
        return len(WORD.findall(text))

    def _vector(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimension, dtype=np.float32)
        # Truncate the same way a real encoder would, so the stand-in cannot
        # quietly see more of a chunk than the arm it stands in for.
        words = WORD.findall(text.lower())[: self.max_seq_tokens]
        for word in words:
            digest = sha256_text(word)
            vector[int(digest[:8], 16) % self.dimension] += 1.0
            # A second, sign-carrying feature: without it every vector is
            # non-negative and everything looks similar to everything.
            vector[int(digest[8:16], 16) % self.dimension] -= 0.5
        return vector

    def _encode(self, texts: Sequence[str]) -> np.ndarray:
        if not len(texts):
            return np.zeros((0, self.dimension), dtype=np.float32)
        vectors = np.vstack([self._vector(text) for text in texts])
        return normalise_rows(vectors) if self.normalize else vectors

    def encode_documents(self, texts: Sequence[str]) -> np.ndarray:
        return self._encode(texts)

    def encode_queries(self, texts: Sequence[str]) -> np.ndarray:
        prefix = self.query_instruction
        return self._encode([f"{prefix}{text}" for text in texts] if prefix else list(texts))
