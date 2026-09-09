"""JATS XML -> ParsedPaper. Pure: no network, no filesystem, no clock.

PMC's efetch returns ``<pmc-articleset>`` wrapping one ``<article>``. The core
JATS vocabulary is unnamespaced; only the licence reference carries a namespace.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from lxml import etree

from ..constants import PARSER_VERSION
from ..hashing import sha256_bytes
from ..types import ParsedPaper
from .jats_body import apply_policy, find_url, normalise, render_body, text_of

ALI = "http://www.niso.org/schemas/ali/1.0/"
XLINK = "http://www.w3.org/1999/xlink"

#: Which ``<pub-date>`` to believe when an article carries several. Electronic
#: publication first: it is the date the paper actually became available.
PUB_DATE_PRIORITY = ("epub", "ppub", "collection", "pub")


class JatsError(Exception):
    """The XML is not a usable PMC article."""


def _first_article(xml: bytes) -> etree._Element:
    try:
        root = etree.fromstring(xml)
    except etree.XMLSyntaxError as exc:
        raise JatsError(f"malformed XML: {exc}") from exc
    if root.tag == "article":
        return root
    article = root.find("article")
    if article is None:
        message = text_of(root.find(".//Error")) or text_of(root)
        raise JatsError(f"no <article> in response ({message[:120] or 'empty'})")
    return article


def _article_ids(article: etree._Element) -> dict[str, str]:
    """First occurrence wins: PMC repeats ids, sometimes for other versions."""
    ids: dict[str, str] = {}
    for element in article.iter("article-id"):
        kind = element.get("pub-id-type")
        if kind:
            ids.setdefault(kind, normalise(element.text or ""))
    return ids


def _pub_date(article: etree._Element) -> str:
    front = article.find("front")
    if front is None:
        return ""
    by_type: dict[str, etree._Element] = {}
    for element in front.iter("pub-date"):
        key = element.get("pub-type") or element.get("date-type") or "pub"
        by_type.setdefault(key, element)
    for key in PUB_DATE_PRIORITY:
        if key in by_type:
            return _iso_date(by_type[key])
    return _iso_date(next(iter(by_type.values()))) if by_type else ""


def _iso_date(element: etree._Element) -> str:
    """As much of yyyy-mm-dd as the article actually states.

    Many PMC articles carry only month and year; inventing a day would put a
    fact in the manifest that the source does not support.
    """
    parts: list[str] = []
    for tag, width in (("year", 4), ("month", 2), ("day", 2)):
        child = element.find(tag)
        value = normalise(child.text or "") if child is not None else ""
        if not value.isdigit():
            break
        parts.append(value.zfill(width))
    return "-".join(parts)


def _licence(article: etree._Element) -> tuple[str, str]:
    licence = article.find(".//permissions/license")
    if licence is None:
        return "", ""
    url = licence.get(f"{{{XLINK}}}href") or ""
    if not url:
        reference = licence.find(f"{{{ALI}}}license_ref")
        url = normalise(reference.text or "") if reference is not None else ""
    text = text_of(licence)
    return (url or find_url(text)), text


def read_metadata(xml: bytes) -> dict[str, Any]:
    """Front-matter only. Used by selection, which must filter before parsing."""
    article = _first_article(xml)
    ids = _article_ids(article)
    pmcid = ids.get("pmcid", "")
    if not pmcid:
        raise JatsError("article has no pmcid")
    if not pmcid.startswith("PMC"):
        pmcid = f"PMC{pmcid}"
    licence_url, licence_text = _licence(article)
    front = article.find("front")
    return {
        "pmcid": pmcid,
        "doi": ids.get("doi") or None,
        "title": text_of(None if front is None else front.find(".//title-group/article-title")),
        "journal": text_of(None if front is None else front.find(".//journal-title")) or None,
        "pub_date": _pub_date(article),
        "license_url": licence_url,
        "license_text": licence_text,
        "article_type": article.get("article-type") or "",
    }


def parse_article(xml: bytes, policy: Mapping[str, Any]) -> ParsedPaper:
    """Full parse under the corpus parse policy."""
    article = _first_article(xml)
    metadata = read_metadata(xml)

    abstract_element = article.find(".//front//abstract")
    stats = apply_policy(article, policy)

    body_element = article.find("body")
    if body_element is None:
        raise JatsError("article has no <body>")
    body, sections = render_body(body_element)
    if not body.strip():
        raise JatsError("article body is empty after applying the parse policy")

    abstract = text_of(abstract_element) if policy.get("keep_abstract", True) else ""
    year = int(metadata["pub_date"][:4]) if metadata["pub_date"][:4].isdigit() else None

    return ParsedPaper(
        pmcid=metadata["pmcid"],
        doi=metadata["doi"],
        title=metadata["title"],
        journal=metadata["journal"],
        year=year,
        article_type=metadata["article_type"],
        license_url=metadata["license_url"],
        license_text=metadata["license_text"],
        abstract=abstract,
        body=body,
        sections=sections,
        source_sha256=sha256_bytes(xml),
        parser_version=PARSER_VERSION,
        parse_metadata={
            **stats,
            # Derived from the rendered stream, not from the replacements made:
            # placeholders created outside <body> (PMC's <floats-group>) never
            # reach the text and must not be counted as if they had.
            "tables_placeholdered": body.count("[TABLE:"),
            "equations_placeholdered": body.count("[EQUATION]"),
            "tables_outside_body": stats["tables_replaced"] - body.count("[TABLE:"),
            "retained_chars": len(body),
            "abstract_chars": len(abstract),
            "n_sections": len(sections),
            "policy": {
                key: policy.get(key)
                for key in (
                    "drop_references",
                    "drop_figure_captions",
                    "drop_bibliographic_xrefs",
                    "table_policy",
                    "equation_policy",
                    "keep_abstract",
                )
            },
        },
    )
