"""Parse policy and body extraction.

The policy, recorded per paper in ``ParsedPaper.parse_metadata``:

===================  ==========================================================
references           dropped entirely (``<ref-list>``)
figure captions      dropped entirely (``<fig>``)
bibliographic xrefs  dropped, surrounding sentence text preserved
tables               replaced with ``[TABLE: <label>]``
display equations    replaced with ``[EQUATION]``
inline math          kept as plain-text / LaTeX source, in place
===================  ==========================================================

Inline math is deliberately not placeholdered: it carries meaning mid-sentence,
and blanking it would corrupt the surrounding text that a chunk is made of.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from lxml import etree

from ..types import SectionSpan

#: Element used to stand in for replaced content, so ordinary text extraction
#: picks the placeholder up in the right position.
PLACEHOLDER_TAG = "ragbench-placeholder"

_WHITESPACE = re.compile(r"\s+")
_SPACE_BEFORE_PUNCTUATION = re.compile(r"\s+([,.;:!?)\]])")
_URL = re.compile(r"https?://[^\s)>\]]+")

#: Brackets left holding nothing but separators once the citations inside them
#: are gone. JATS marks a citation two ways, and only one of them takes its
#: punctuation with it: ``<xref>[1]</xref>`` disappears cleanly, while
#: ``[<xref>1</xref>]`` and ``(<xref/>;<xref/>;<xref/>)`` leave ``[]`` and
#: ``(;;;)`` sitting in the prose. 3,863 of them survived the first parse, in 80
#: of the 100 papers.
#:
#: Periods and dashes are deliberately NOT in the character class. ``(...)`` is
#: an editorial ellipsis and ``(-)`` is a stereochemistry prefix -- both are
#: content, and a cleanup that eats them is worse than the residue it removes.
_EMPTY_CITATION = re.compile(r"\s*[\[(][\s,;]*[\])]")


def normalise(text: str) -> str:
    """Collapse whitespace, and close both gaps a dropped citation leaves behind.

    Removing ``<xref>[1]</xref>`` from "... with age [1], as shown" would
    otherwise leave "... with age , as shown" -- a space before the comma in
    every sentence that cited anything.

    Removing the ``<xref>`` from ``[<xref>1</xref>]`` leaves the brackets, which
    is the same defect wearing different punctuation: "human APP in flies []."
    The empty brackets go, then whitespace is collapsed again because removing
    them can leave a double space, then the space-before-punctuation rule runs
    last so "flies ." closes to "flies.".
    """
    text = _EMPTY_CITATION.sub("", text)
    collapsed = _WHITESPACE.sub(" ", text)
    return _SPACE_BEFORE_PUNCTUATION.sub(r"\1", collapsed).strip()


def count_empty_citations(text: str) -> int:
    """Residues still present. Reported per paper; the parse policy says zero."""
    return len(_EMPTY_CITATION.findall(text))


def text_of(element: etree._Element | None) -> str:
    if element is None:
        return ""
    return normalise("".join(element.itertext()))


def find_url(text: str) -> str:
    match = _URL.search(text)
    return match.group(0).rstrip(").,;") if match else ""


def _detach(element: etree._Element) -> None:
    """Remove an element, splicing its tail text onto whatever preceded it.

    Without this, dropping an ``<xref>`` would also swallow the space and
    punctuation that followed it, silently corrupting the sentence.
    """
    parent = element.getparent()
    if parent is None:
        return
    if element.tail:
        previous = element.getprevious()
        if previous is not None:
            previous.tail = (previous.tail or "") + element.tail
        else:
            parent.text = (parent.text or "") + element.tail
    parent.remove(element)


def _replace_with_text(element: etree._Element, text: str) -> None:
    parent = element.getparent()
    if parent is None:
        return
    placeholder = etree.Element(PLACEHOLDER_TAG)
    placeholder.text = text
    placeholder.tail = element.tail
    parent.replace(element, placeholder)


def apply_policy(article: etree._Element, policy: Mapping[str, Any]) -> dict[str, int]:
    """Rewrite the tree in place; return the counts that go into parse metadata."""
    # Counts are document-wide. PMC often parks tables in <floats-group>, outside
    # <body>, where they are replaced here but never rendered into the text
    # stream -- so these are NOT the number of placeholders a reader will see.
    # parse_article derives the retained counts from the rendered body.
    stats = {
        "sections_dropped": 0,
        "figures_dropped": 0,
        "xrefs_dropped": 0,
        "tables_replaced": 0,
        "equations_replaced": 0,
        "inline_math_kept": 0,
    }

    if policy.get("drop_references", True):
        for element in article.findall(".//ref-list"):
            _detach(element)
            stats["sections_dropped"] += 1

    if policy.get("drop_figure_captions", True):
        for element in article.findall(".//fig"):
            _detach(element)
            stats["figures_dropped"] += 1

    if policy.get("drop_bibliographic_xrefs", True):
        for element in article.findall(".//xref"):
            if element.get("ref-type") == "bibr":
                _detach(element)
                stats["xrefs_dropped"] += 1

    if policy.get("table_policy", "placeholder") == "placeholder":
        for element in article.findall(".//table-wrap"):
            label = text_of(element.find("label")) or "Table"
            _replace_with_text(element, f"[TABLE: {label}]")
            stats["tables_replaced"] += 1
    elif policy.get("table_policy") == "drop":
        for element in article.findall(".//table-wrap"):
            _detach(element)

    if policy.get("equation_policy", "placeholder") == "placeholder":
        for element in article.findall(".//disp-formula"):
            _replace_with_text(element, "[EQUATION]")
            stats["equations_replaced"] += 1
    elif policy.get("equation_policy") == "drop":
        for element in article.findall(".//disp-formula"):
            _detach(element)

    # Inline math survives as source text: prefer the TeX if the article carries
    # it, else fall back to the element's own text content.
    for element in article.findall(".//inline-formula"):
        tex = element.find(".//tex-math")
        _replace_with_text(element, text_of(tex) if tex is not None else text_of(element))
        stats["inline_math_kept"] += 1

    return stats


def render_body(body: etree._Element) -> tuple[str, tuple[SectionSpan, ...]]:
    """Flatten ``<body>`` into one text stream plus spans that index into it.

    Both chunkers operate on the single stream, so section spans are recorded as
    character offsets rather than as separate text.
    """
    parts: list[str] = []
    spans: list[SectionSpan] = []
    length = 0

    def emit(text: str) -> None:
        nonlocal length
        if text:
            parts.append(text)
            length += len(text)

    def walk(section: etree._Element, depth: int) -> None:
        title_element = section.find("title")
        start = length
        title = text_of(title_element)
        if title:
            emit(title + "\n\n")
        for child in section:
            if child is title_element:
                continue
            if child.tag == "sec":
                walk(child, depth + 1)
            else:
                emit_block(child)
        spans.append(
            SectionSpan(
                title=title,
                sec_type=section.get("sec-type") or "",
                depth=depth,
                char_start=start,
                char_end=length,
            )
        )

    def emit_block(element: etree._Element) -> None:
        text = text_of(element)
        if text:
            emit(text + "\n\n")

    for child in body:
        if child.tag == "sec":
            walk(child, 0)
        else:
            emit_block(child)

    return "".join(parts), tuple(spans)
