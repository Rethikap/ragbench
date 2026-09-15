"""Tokenizer access, behind an interface.

Chunking is the first stage that needs a real model artefact. Per CLAUDE.md every
model-dependent component sits behind an interface with a CPU stand-in, so the
pipeline stays smoke-testable with no download: tests use
:class:`WhitespaceTokenizer`, production uses :class:`HuggingFaceTokenizer`.

Two tokenizers exist in this project and they are never interchangeable. The
canonical chunk tokenizer draws chunk boundaries and is fixed across all 8 runs;
the budget tokenizer measures the generator's context window. They disagree
substantially -- the same sentence is 24 bge tokens and 31 Qwen tokens -- which
is exactly why the budget is measured with the generator's own tokenizer.

Both are addressed by ``model_id`` *and* a commit ``revision``. A Hub id is a
mutable pointer: the repo behind it can gain a new commit, and a tokenizer that
re-draws one boundary re-chunks the corpus. The revision is the thing that is
actually reproducible, and it is what reaches the chunk-set cache key -- so the
same config resolves to the same chunk boundaries on this laptop and on Kaggle.
"""

from __future__ import annotations

import bisect
import re
from functools import lru_cache
from typing import Protocol, runtime_checkable

Offsets = list[tuple[int, int]]


@runtime_checkable
class Tokenizer(Protocol):
    name: str

    def offsets(self, text: str) -> Offsets:
        """Character span of every token, in order."""

    def count(self, text: str) -> int:
        """Number of tokens in ``text``."""


class HuggingFaceTokenizer:
    """A fast HF tokenizer, used only for counting and for offset mapping.

    ``revision`` is required, not optional: an unpinned id is a moving target,
    and the whole chunk set is a function of how this tokenizer segments text.
    """

    def __init__(self, model_id: str, revision: str) -> None:
        from transformers import AutoTokenizer

        if not revision:
            raise ValueError(
                f"{model_id}: a commit revision is required. Hub ids are mutable; "
                "pin the 40-character commit sha from the model repo."
            )
        self.name = f"{model_id}@{revision}"
        tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
        if not tokenizer.is_fast:
            raise ValueError(f"{model_id} has no fast tokenizer, so offsets are unavailable")
        # Chunking tokenizes whole papers, which are far longer than the model's
        # sequence limit. That limit belongs to the embedding stage, not here;
        # raising it only silences a truncation warning we never act on.
        tokenizer.model_max_length = int(1e9)
        self._tokenizer = tokenizer

    def offsets(self, text: str) -> Offsets:
        encoded = self._tokenizer(
            text, add_special_tokens=False, return_offsets_mapping=True, truncation=False
        )
        return [(int(start), int(end)) for start, end in encoded["offset_mapping"]]

    def count(self, text: str) -> int:
        return len(self._tokenizer(text, add_special_tokens=False)["input_ids"])


class WhitespaceTokenizer:
    """Deterministic stand-in: one token per whitespace-delimited run.

    Not a model, and not meant to resemble one. It exists so the chunkers can be
    tested for boundary correctness offline, where what matters is that offsets
    and counts are consistent, not that they match any particular vocabulary.
    """

    name = "whitespace"
    _token = re.compile(r"\S+")

    def offsets(self, text: str) -> Offsets:
        return [(match.start(), match.end()) for match in self._token.finditer(text)]

    def count(self, text: str) -> int:
        return len(self._token.findall(text))


@lru_cache(maxsize=4)
def load_tokenizer(model_id: str, revision: str = "") -> Tokenizer:
    """Cached loader. ``whitespace`` selects the stand-in without any download."""
    if model_id == "whitespace":
        return WhitespaceTokenizer()
    return HuggingFaceTokenizer(model_id, revision)


class DocumentTokens:
    """One tokenization of a whole paper, queryable by character range.

    Both chunkers need token counts for many candidate spans of the same text.
    Tokenizing each candidate separately would be quadratic; this tokenizes once
    and answers range queries by binary search.
    """

    def __init__(self, text: str, tokenizer: Tokenizer) -> None:
        self.text = text
        self.tokenizer = tokenizer
        self.spans = tokenizer.offsets(text)
        self._starts = [start for start, _ in self.spans]
        self._ends = [end for _, end in self.spans]

    def __len__(self) -> int:
        return len(self.spans)

    def count_range(self, start: int, end: int) -> int:
        """Tokens overlapping ``[start, end)``.

        Counts a token that straddles a boundary, so the answer is never an
        undercount -- a chunker deciding "does this still fit" must err toward
        splitting, not toward emitting an over-long chunk.
        """
        if end <= start:
            return 0
        first = bisect.bisect_right(self._ends, start)
        last = bisect.bisect_left(self._starts, end)
        return max(0, last - first)

    def spans_in(self, start: int, end: int) -> Offsets:
        """Tokens lying wholly inside ``[start, end)``.

        Used when a chunker has run out of separators and must cut on token
        boundaries; wholly-contained is the right rule there, because the cut
        must not claim characters outside the span it was given.
        """
        first = bisect.bisect_left(self._starts, start)
        last = bisect.bisect_right(self._ends, end)
        return self.spans[first:last]
