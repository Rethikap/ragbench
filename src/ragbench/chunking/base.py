"""Chunker interface and chunk assembly.

A chunker's only job is to decide *boundaries*: it returns character spans over
the paper body, plus which separator level produced each one. Turning spans into
:class:`~ragbench.types.Chunk` records -- ids, exact token counts, section
attribution, content digests -- happens once, here, so both strategies produce
records built identically.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, NamedTuple, Protocol

from ..hashing import sha256_text
from ..tokenizers import DocumentTokens, Offsets, Tokenizer
from ..types import Chunk, ParsedPaper


class Piece(NamedTuple):
    """A boundary decision. Internal to chunking; never persisted as-is."""

    char_start: int
    char_end: int
    #: Index into the configured separator list, or None when the text fitted
    #: whole and no separator was needed.
    separator_level: int | None


class Chunker(Protocol):
    name: str

    def split(self, document: DocumentTokens) -> list[Piece]:
        """Boundaries over ``document.text``, in document order."""


def fit_window(
    text: str, spans: Offsets, index: int, take: int, target: int, tokenizer: Tokenizer
) -> int:
    """Largest width <= ``take`` whose emitted text costs at most ``target`` tokens.

    A span of N document tokens does not necessarily cost N tokens once it is
    sliced out and tokenized on its own. A subword tokenizer charges by where a
    string *starts*: BAAI/bge-base-en-v1.5 segments "informatics" as
    ``inform`` + ``##atics``, but the substring "atics" -- the same characters as
    that second token -- costs ``at`` + ``##ics`` standing alone. So a window cut
    mid-word re-tokenizes to more tokens than it contains, and a window of
    exactly ``target`` document tokens can emit ``target + 1``.

    Only a chunker that cuts without consulting a separator can start a window
    mid-word, which made this an asymmetry between the arms rather than a shared
    offset: 54 of the fixed arm's 1,586 chunks were 513-514 canonical tokens
    against a 512 target, and none of the recursive arm's were.

    Callers must resume from the returned width rather than from ``take``, or the
    trimmed tokens belong to no chunk at all.
    """
    start = spans[index][0]
    while take > 1:
        emitted = text[start : spans[index + take - 1][1]].strip()
        excess = tokenizer.count(emitted) - target
        if excess <= 0:
            break
        # Drop at least the overshoot. Overshoot is one or two tokens in
        # practice, so this converges immediately; undershooting only ever
        # yields a slightly smaller chunk, never a lost character.
        take -= max(1, excess)
    return max(take, 1)


def sections_for(paper: ParsedPaper, start: int, end: int) -> tuple[str, ...]:
    """Titles of every section the span overlaps, in document order.

    A chunk may straddle a section boundary, so this is a tuple rather than a
    single title; deduplicated because nested sections repeat their parent.
    """
    titles: list[str] = []
    for section in paper.sections:
        if section.char_start < end and section.char_end > start and section.title:
            if section.title not in titles:
                titles.append(section.title)
    return tuple(titles)


def keep_nonempty(text: str, pieces: Sequence[Piece]) -> list[Piece]:
    """Drop spans that are whitespace-only.

    Consecutive separators produce empty segments. Filtering before both counting
    and assembly keeps separator-level statistics equal to the number of chunks
    they actually produced, rather than to the number of boundary decisions made.
    """
    return [piece for piece in pieces if text[piece.char_start : piece.char_end].strip()]


def assemble(
    paper: ParsedPaper, pieces: Sequence[Piece], tokenizer: Tokenizer
) -> list[Chunk]:
    """Turn boundaries into records, discarding spans that are empty after strip."""
    chunks: list[Chunk] = []
    for piece in pieces:
        raw = paper.body[piece.char_start : piece.char_end]
        stripped = raw.strip()
        if not stripped:
            continue
        # Re-derive the span so offsets point at the retained text, not at the
        # whitespace a separator split happened to leave on either side.
        lead = len(raw) - len(raw.lstrip())
        start = piece.char_start + lead
        end = start + len(stripped)
        index = len(chunks)
        chunks.append(
            Chunk(
                chunk_id=f"{paper.pmcid}-{index:04d}",
                pmcid=paper.pmcid,
                chunk_index=index,
                text=stripped,
                n_tokens=tokenizer.count(stripped),
                char_start=start,
                char_end=end,
                sections=sections_for(paper, start, end),
                content_sha256=sha256_text(stripped),
            )
        )
    return chunks


def build_chunker(strategy: str, params: Mapping[str, Any], tokenizer: Tokenizer) -> Chunker:
    try:
        factory = CHUNKERS[strategy]
    except KeyError:
        raise ValueError(
            f"unknown chunking strategy {strategy!r}; known: {', '.join(sorted(CHUNKERS))}"
        ) from None
    return factory(params, tokenizer)


def _fixed(params: Mapping[str, Any], tokenizer: Tokenizer) -> Chunker:
    from .fixed import FixedChunker

    return FixedChunker(params, tokenizer)


def _recursive(params: Mapping[str, Any], tokenizer: Tokenizer) -> Chunker:
    from .recursive import RecursiveChunker

    return RecursiveChunker(params, tokenizer)


CHUNKERS = {"fixed": _fixed, "recursive": _recursive}
