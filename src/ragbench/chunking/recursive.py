"""Recursive chunking: split on the most structural separator that works.

The separator hierarchy comes from ``chunking.separators`` in base.yaml and is
never hardcoded here, so changing the hierarchy is a config edit that flows into
the chunk-set cache key automatically.

The algorithm tries each separator in turn. Segments that already fit are merged
greedily up to ``target_tokens``; segments still too large are re-split with the
next separator down; when the hierarchy is exhausted the span is cut on token
boundaries. Every emitted piece records which level produced it, which is what
makes it answerable whether "recursive" is really behaving recursively or has
degenerated into character splitting.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ..tokenizers import DocumentTokens, Tokenizer
from .base import Piece

Span = tuple[int, int]


class RecursiveChunker:
    name = "recursive"

    def __init__(self, params: Mapping[str, Any], tokenizer: Tokenizer) -> None:
        self.target = int(params["target_tokens"])
        if self.target <= 0:
            raise ValueError("chunking.target_tokens must be positive")
        if int(params.get("overlap_tokens", 0)):
            # Silently ignoring a configured overlap would make the chunk-set key
            # promise something the chunks do not have.
            raise ValueError(
                "recursive chunking with overlap_tokens > 0 is not implemented; "
                "base.yaml configures overlap_tokens: 0"
            )
        separators = list(params.get("separators") or [])
        if not separators:
            raise ValueError("chunking.separators must be a non-empty list")
        self.separators: Sequence[str] = separators
        self.tokenizer = tokenizer

    # ------------------------------------------------------------------ api

    def split(self, document: DocumentTokens) -> list[Piece]:
        end = len(document.text)
        if end == 0:
            return []
        if document.count_range(0, end) <= self.target:
            return [Piece(0, end, None)]
        return self._split(document, 0, end, 0)

    # -------------------------------------------------------------- internals

    def _split(self, document: DocumentTokens, start: int, end: int, level: int) -> list[Piece]:
        """Split ``[start, end)``, which is known not to fit, from ``level`` down."""
        if level >= len(self.separators):
            return self._token_split(document, start, end, len(self.separators) - 1)

        separator = self.separators[level]
        if separator == "":
            return self._token_split(document, start, end, level)

        segments = self._segments(document.text, start, end, separator)
        if len(segments) <= 1:
            # This separator does not occur here; drop to the next one without
            # recording it as having fired.
            return self._split(document, start, end, level + 1)

        return self._merge(document, segments, level)

    def _merge(self, document: DocumentTokens, segments: list[Span], level: int) -> list[Piece]:
        """Greedily pack segments up to the target; recurse on any that overflow."""
        pieces: list[Piece] = []
        open_start: int | None = None
        open_end = 0
        open_tokens = 0

        def flush() -> None:
            nonlocal open_start, open_tokens
            if open_start is not None:
                pieces.append(Piece(open_start, open_end, level))
                open_start = None
                open_tokens = 0

        for segment_start, segment_end in segments:
            tokens = document.count_range(segment_start, segment_end)
            if tokens > self.target:
                flush()
                pieces.extend(self._split(document, segment_start, segment_end, level + 1))
                continue
            if open_start is None:
                open_start, open_end, open_tokens = segment_start, segment_end, tokens
            elif open_tokens + tokens <= self.target:
                open_end = segment_end
                open_tokens += tokens
            else:
                flush()
                open_start, open_end, open_tokens = segment_start, segment_end, tokens

        flush()
        return pieces

    def _token_split(
        self, document: DocumentTokens, start: int, end: int, level: int
    ) -> list[Piece]:
        """Last resort: cut on token boundaries inside the span."""
        spans = document.spans_in(start, end)
        if not spans:
            return [Piece(start, end, level)]
        pieces: list[Piece] = []
        for index in range(0, len(spans), self.target):
            window = spans[index : index + self.target]
            pieces.append(Piece(window[0][0], window[-1][1], level))
        return pieces

    @staticmethod
    def _segments(text: str, start: int, end: int, separator: str) -> list[Span]:
        """Split a range on ``separator``, keeping it attached to the left segment.

        No character is dropped: the segments tile ``[start, end)`` exactly, so
        chunk offsets stay valid indices into the parsed body.
        """
        segments: list[Span] = []
        cursor = start
        while True:
            found = text.find(separator, cursor, end)
            if found == -1:
                break
            stop = found + len(separator)
            segments.append((cursor, stop))
            cursor = stop
        if cursor < end:
            segments.append((cursor, end))
        return segments
