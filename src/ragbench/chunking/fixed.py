"""Fixed-size chunking: contiguous windows of the canonical tokenizer's tokens.

The simplest possible boundary rule, and the control arm of the chunking factor:
it ignores document structure entirely and cuts every ``target_tokens`` tokens,
wherever that lands.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..tokenizers import DocumentTokens, Tokenizer
from .base import Piece


class FixedChunker:
    name = "fixed"

    def __init__(self, params: Mapping[str, Any], tokenizer: Tokenizer) -> None:
        self.target = int(params["target_tokens"])
        self.overlap = int(params.get("overlap_tokens", 0))
        if self.target <= 0:
            raise ValueError("chunking.target_tokens must be positive")
        if not 0 <= self.overlap < self.target:
            raise ValueError("chunking.overlap_tokens must be >= 0 and < target_tokens")
        self.tokenizer = tokenizer

    def split(self, document: DocumentTokens) -> list[Piece]:
        spans = document.spans
        if not spans:
            return []
        step = self.target - self.overlap
        pieces: list[Piece] = []
        for start_index in range(0, len(spans), step):
            window = spans[start_index : start_index + self.target]
            if not window:
                break
            # separator_level is None throughout: this strategy never consults
            # the separator hierarchy, which is what makes it the control arm.
            pieces.append(Piece(window[0][0], window[-1][1], None))
            if start_index + self.target >= len(spans):
                break
        return pieces
