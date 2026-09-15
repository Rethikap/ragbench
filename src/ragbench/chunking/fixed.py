"""Fixed-size chunking: contiguous windows of the canonical tokenizer's tokens.

The simplest possible boundary rule, and the control arm of the chunking factor:
it ignores document structure entirely and cuts every ``target_tokens`` tokens,
wherever that lands.

"Wherever that lands" includes the middle of a word, and a window cut mid-word
re-tokenizes to more tokens than it contains -- see :func:`~.base.fit_window`.
Each window is therefore trimmed until the text it emits fits, and the next
window resumes from the trim point, so the arm both respects the target and
still tiles the body.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..tokenizers import DocumentTokens, Tokenizer
from .base import Piece, fit_window


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
        pieces: list[Piece] = []
        index = 0
        while index < len(spans):
            take = fit_window(
                document.text,
                spans,
                index,
                min(self.target, len(spans) - index),
                self.target,
                self.tokenizer,
            )
            window = spans[index : index + take]
            # separator_level is None throughout: this strategy never consults
            # the separator hierarchy, which is what makes it the control arm.
            pieces.append(Piece(window[0][0], window[-1][1], None))
            # Advance by what was emitted, not by the untrimmed target: the
            # overlap stays exactly overlap_tokens and no token is skipped.
            index += max(1, take - self.overlap)
        return pieces
