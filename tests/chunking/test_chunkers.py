"""Chunker boundary correctness, offline against the whitespace stand-in.

The stand-in makes token counts predictable (one token per word), so these tests
assert the boundary *rules* rather than any particular vocabulary's behaviour.
"""

from __future__ import annotations

import re

import pytest

from ragbench.chunking.base import Piece, build_chunker, sections_for
from ragbench.chunking.fixed import FixedChunker
from ragbench.chunking.recursive import RecursiveChunker
from ragbench.tokenizers import DocumentTokens, WhitespaceTokenizer
from ragbench.types import ParsedPaper, SectionSpan

SEPARATORS = ["\n\n", "\n", ". ", " ", ""]
TOKENIZER = WhitespaceTokenizer()


def params(**overrides):
    base = {
        "strategy": "fixed",
        "target_tokens": 10,
        "overlap_tokens": 0,
        "tokenizer_id": "whitespace",
        "min_chunk_tokens": 0,
        "separators": SEPARATORS,
    }
    return {**base, **overrides}


def document(text: str) -> DocumentTokens:
    return DocumentTokens(text, TOKENIZER)


def words(count: int, stem: str = "w") -> str:
    return " ".join(f"{stem}{i}" for i in range(count))


PARAGRAPHS = "\n\n".join([words(7, "a"), words(7, "b"), words(7, "c")])


def chunk_texts(text: str, pieces: list[Piece]) -> list[str]:
    return [text[p.char_start : p.char_end].strip() for p in pieces]


# ------------------------------------------------------------------- shared


@pytest.mark.parametrize("strategy", ["fixed", "recursive"])
def test_no_chunk_exceeds_the_target(strategy: str) -> None:
    text = PARAGRAPHS + "\n\n" + words(50, "d")
    chunker = build_chunker(strategy, params(strategy=strategy, target_tokens=10), TOKENIZER)
    for piece in chunker.split(document(text)):
        assert TOKENIZER.count(text[piece.char_start : piece.char_end]) <= 10


@pytest.mark.parametrize("strategy", ["fixed", "recursive"])
def test_offsets_index_the_source_exactly(strategy: str) -> None:
    text = PARAGRAPHS
    chunker = build_chunker(strategy, params(strategy=strategy, target_tokens=10), TOKENIZER)
    for piece in chunker.split(document(text)):
        assert 0 <= piece.char_start < piece.char_end <= len(text)


@pytest.mark.parametrize("strategy", ["fixed", "recursive"])
def test_no_content_is_lost(strategy: str) -> None:
    """Chunks must tile the body: every non-whitespace character survives."""
    text = PARAGRAPHS + "\n\n" + words(37, "e")
    chunker = build_chunker(strategy, params(strategy=strategy, target_tokens=8), TOKENIZER)
    pieces = chunker.split(document(text))
    rebuilt = "".join(text[p.char_start : p.char_end] for p in pieces)
    assert re.sub(r"\s+", "", rebuilt) == re.sub(r"\s+", "", text)


@pytest.mark.parametrize("strategy", ["fixed", "recursive"])
def test_splitting_is_deterministic(strategy: str) -> None:
    chunker = build_chunker(strategy, params(strategy=strategy), TOKENIZER)
    assert chunker.split(document(PARAGRAPHS)) == chunker.split(document(PARAGRAPHS))


def test_unknown_strategy_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown chunking strategy"):
        build_chunker("semantic", params(), TOKENIZER)


# -------------------------------------------------------------------- fixed


def test_fixed_fills_every_window_but_the_last() -> None:
    text = words(25)
    pieces = FixedChunker(params(target_tokens=10), TOKENIZER).split(document(text))
    counts = [TOKENIZER.count(text[p.char_start : p.char_end]) for p in pieces]
    assert counts == [10, 10, 5]


def test_fixed_ignores_structure() -> None:
    """The control arm: paragraph boundaries must not influence the cut."""
    pieces = FixedChunker(params(target_tokens=10), TOKENIZER).split(document(PARAGRAPHS))
    assert all(piece.separator_level is None for piece in pieces)
    assert chunk_texts(PARAGRAPHS, pieces)[0].endswith("b2")


def test_fixed_rejects_impossible_overlap() -> None:
    with pytest.raises(ValueError, match="overlap_tokens"):
        FixedChunker(params(target_tokens=10, overlap_tokens=10), TOKENIZER)


def test_fixed_overlap_repeats_tokens() -> None:
    text = words(20)
    pieces = FixedChunker(params(target_tokens=10, overlap_tokens=4), TOKENIZER).split(
        document(text)
    )
    first, second = chunk_texts(text, pieces)[:2]
    assert first.split()[-4:] == second.split()[:4]


# ---------------------------------------------------------------- recursive


def test_recursive_respects_paragraph_boundaries() -> None:
    pieces = RecursiveChunker(params(target_tokens=10), TOKENIZER).split(document(PARAGRAPHS))
    assert chunk_texts(PARAGRAPHS, pieces) == [words(7, "a"), words(7, "b"), words(7, "c")]
    assert {piece.separator_level for piece in pieces} == {0}


def test_recursive_packs_small_paragraphs_together() -> None:
    text = "\n\n".join([words(3, "a"), words(3, "b"), words(3, "c")])
    pieces = RecursiveChunker(params(target_tokens=10), TOKENIZER).split(document(text))
    assert len(pieces) == 1
    assert pieces[0].separator_level is None


def test_recursive_descends_when_a_paragraph_is_too_big() -> None:
    """One oversized paragraph, no blank lines: level 0 cannot fire."""
    text = words(6, "a") + "\n" + words(6, "b") + "\n" + words(6, "c")
    pieces = RecursiveChunker(params(target_tokens=8), TOKENIZER).split(document(text))
    assert {piece.separator_level for piece in pieces} == {1}


def test_recursive_reaches_sentence_then_word_levels() -> None:
    sentences = ". ".join(words(9, f"s{i}") for i in range(4))
    pieces = RecursiveChunker(params(target_tokens=10), TOKENIZER).split(document(sentences))
    assert {piece.separator_level for piece in pieces} <= {2, 3}


def test_recursive_falls_back_to_token_windows() -> None:
    """With no usable separator left, the empty one cuts on token boundaries."""
    text = words(9)
    chunker = RecursiveChunker(params(target_tokens=3, separators=["\n\n", ""]), TOKENIZER)
    pieces = chunker.split(document(text))
    assert [piece.separator_level for piece in pieces] == [1, 1, 1]
    assert chunk_texts(text, pieces) == ["w0 w1 w2", "w3 w4 w5", "w6 w7 w8"]


def test_recursive_separators_come_from_config_not_code() -> None:
    """A hierarchy the code has never heard of must work identically."""
    text = "a1 a2|b1 b2|c1 c2"
    piped = RecursiveChunker(params(target_tokens=2, separators=["|", ""]), TOKENIZER)
    assert chunk_texts(text, piped.split(document(text))) == ["a1 a2|", "b1 b2|", "c1 c2"]


def test_recursive_requires_separators() -> None:
    with pytest.raises(ValueError, match="separators"):
        RecursiveChunker(params(separators=[]), TOKENIZER)


def test_recursive_refuses_overlap_rather_than_ignoring_it() -> None:
    with pytest.raises(ValueError, match="overlap"):
        RecursiveChunker(params(overlap_tokens=4), TOKENIZER)


# ----------------------------------------------------------------- sections


def _paper(body: str, sections: tuple[SectionSpan, ...]) -> ParsedPaper:
    return ParsedPaper(
        pmcid="PMC1",
        doi=None,
        title="t",
        journal=None,
        year=2021,
        article_type="research-article",
        license_url="",
        license_text="",
        abstract="",
        body=body,
        sections=sections,
        source_sha256="0" * 64,
        parser_version="1",
    )


def test_sections_are_attributed_by_overlap() -> None:
    body = words(10, "a") + "\n\n" + words(10, "b")
    boundary = len(words(10, "a"))
    paper = _paper(
        body,
        (
            SectionSpan("Intro", "intro", 0, 0, boundary),
            SectionSpan("Methods", "methods", 0, boundary + 2, len(body)),
        ),
    )
    assert sections_for(paper, 0, 5) == ("Intro",)
    assert sections_for(paper, boundary + 3, len(body)) == ("Methods",)
    assert sections_for(paper, boundary - 2, boundary + 5) == ("Intro", "Methods")
