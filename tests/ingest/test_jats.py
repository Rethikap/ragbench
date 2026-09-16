"""Parse policy, offline, against a committed JATS fixture.

The fixture exercises every policy branch: a bibliographic xref, a figure, a
table with a label, a display equation, inline TeX, a nested section, a licence
carried in ali:license_ref, repeated article-ids, and competing pub-dates.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ragbench.constants import PARSER_VERSION
from ragbench.hashing import sha256_bytes
from ragbench.ingest.jats import JatsError, parse_article, read_metadata

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "sample_article.xml"

POLICY = {
    "drop_references": True,
    "drop_figure_captions": True,
    "drop_bibliographic_xrefs": True,
    "table_policy": "placeholder",
    "equation_policy": "placeholder",
    "keep_abstract": True,
}


@pytest.fixture
def xml() -> bytes:
    return FIXTURE.read_bytes()


# ------------------------------------------------------------------ metadata


def test_metadata_takes_the_first_of_repeated_ids(xml: bytes) -> None:
    assert read_metadata(xml)["pmcid"] == "PMC9999001"


def test_metadata_reads_the_licence_from_ali_license_ref(xml: bytes) -> None:
    metadata = read_metadata(xml)
    assert metadata["license_url"] == "https://creativecommons.org/licenses/by/4.0/"
    assert "CC BY 4.0" in metadata["license_text"]


def test_metadata_prefers_the_epub_date(xml: bytes) -> None:
    """The article carries both a collection date (2021-07) and an epub date."""
    assert read_metadata(xml)["pub_date"] == "2021-06-03"


def test_metadata_reads_type_title_journal_doi(xml: bytes) -> None:
    metadata = read_metadata(xml)
    assert metadata["article_type"] == "research-article"
    assert metadata["title"] == "A Controlled Study of Test Biomarkers"
    assert metadata["journal"] == "Journal of Test Biomarkers"
    assert metadata["doi"] == "10.1234/test.2021.001"


# -------------------------------------------------------------- parse policy


def test_references_and_figure_captions_are_dropped(xml: bytes) -> None:
    body = parse_article(xml, POLICY).body
    assert "prior study" not in body
    assert "References" not in body
    assert "must not reach the body" not in body
    assert "Figure 1" not in body


def test_tables_become_labelled_placeholders(xml: bytes) -> None:
    body = parse_article(xml, POLICY).body
    assert "[TABLE: Table 2]" in body
    assert "demographics" not in body.lower()


def test_display_equations_become_placeholders(xml: bytes) -> None:
    body = parse_article(xml, POLICY).body
    assert "[EQUATION]" in body
    assert "y = mx + b" not in body


def test_inline_math_is_kept_as_source(xml: bytes) -> None:
    body = parse_article(xml, POLICY).body
    assert r"A\beta_{42}/A\beta_{40}" in body
    assert "[EQUATION]" not in body.split("Methods")[0]


def test_dropping_a_citation_does_not_leave_a_gap(xml: bytes) -> None:
    body = parse_article(xml, POLICY).body
    assert "with age, as shown before." in body
    assert "[1]" not in body


def test_abstract_is_kept_and_can_be_disabled(xml: bytes) -> None:
    assert "biomarker in plasma" in parse_article(xml, POLICY).abstract
    assert parse_article(xml, {**POLICY, "keep_abstract": False}).abstract == ""


def test_table_and_equation_policies_can_drop_instead(xml: bytes) -> None:
    body = parse_article(xml, {**POLICY, "table_policy": "drop", "equation_policy": "drop"}).body
    assert "[TABLE:" not in body
    assert "[EQUATION]" not in body


# --------------------------------------------------------------- parse stats


def test_parse_metadata_counts_what_the_policy_did(xml: bytes) -> None:
    metadata = parse_article(xml, POLICY).parse_metadata
    assert metadata["tables_placeholdered"] == 1
    assert metadata["equations_placeholdered"] == 1
    assert metadata["sections_dropped"] == 1
    assert metadata["figures_dropped"] == 1
    # 1 in the first paragraph, 3 in the citation-residue paragraph.
    assert metadata["xrefs_dropped"] == 4
    assert metadata["inline_math_kept"] == 1


def test_placeholders_outside_the_body_are_not_counted_as_retained() -> None:
    """PMC parks tables in <floats-group>, which is never rendered. Counting the
    replacements made would overstate what is actually in the corpus text."""
    xml = FIXTURE.read_bytes().replace(
        b"</body>",
        b"</body><floats-group><table-wrap id='T9'><label>Table 9</label>"
        b"<table><tbody><tr><td>x</td></tr></tbody></table></table-wrap></floats-group>",
    )
    metadata = parse_article(xml, POLICY).parse_metadata
    assert metadata["tables_replaced"] == 2
    assert metadata["tables_placeholdered"] == 1
    assert metadata["tables_outside_body"] == 1
    assert "[TABLE: Table 9]" not in parse_article(xml, POLICY).body


def test_retained_chars_matches_the_body(xml: bytes) -> None:
    paper = parse_article(xml, POLICY)
    assert paper.parse_metadata["retained_chars"] == len(paper.body)
    assert paper.parse_metadata["policy"]["table_policy"] == "placeholder"


# ------------------------------------------------------------------ sections


def test_sections_are_recorded_with_depth_and_offsets(xml: bytes) -> None:
    paper = parse_article(xml, POLICY)
    by_title = {section.title: section for section in paper.sections}
    assert set(by_title) == {"Introduction", "Methods", "Participants"}
    assert by_title["Introduction"].depth == 0
    assert by_title["Participants"].depth == 1
    assert by_title["Introduction"].sec_type == "intro"


def test_section_spans_index_into_the_body(xml: bytes) -> None:
    paper = parse_article(xml, POLICY)
    for section in paper.sections:
        assert 0 <= section.char_start <= section.char_end <= len(paper.body)
        if section.title:
            assert paper.body[section.char_start :].startswith(section.title)


# ------------------------------------------------------------------ identity


def test_source_digest_and_parser_version_are_recorded(xml: bytes) -> None:
    paper = parse_article(xml, POLICY)
    assert paper.source_sha256 == sha256_bytes(xml)
    assert paper.parser_version == PARSER_VERSION


def test_parsing_is_deterministic(xml: bytes) -> None:
    assert parse_article(xml, POLICY).to_dict() == parse_article(xml, POLICY).to_dict()


def test_round_trips_through_json(xml: bytes) -> None:
    from ragbench.types import ParsedPaper

    paper = parse_article(xml, POLICY)
    assert ParsedPaper.from_dict(paper.to_dict()) == paper


# -------------------------------------------------------------------- errors


def test_malformed_xml_is_a_clean_error() -> None:
    with pytest.raises(JatsError, match="malformed XML"):
        read_metadata(b"<not-xml")


def test_missing_article_is_a_clean_error() -> None:
    with pytest.raises(JatsError, match="no <article>"):
        read_metadata(b"<pmc-articleset><Error>Invalid ID</Error></pmc-articleset>")


def test_article_without_body_is_a_clean_error() -> None:
    xml = b'<article article-type="research-article"><front><article-meta>'
    xml += b'<article-id pub-id-type="pmcid">PMC1</article-id>'
    xml += b"</article-meta></front></article>"
    with pytest.raises(JatsError, match="no <body>"):
        parse_article(xml, POLICY)


# ------------------------------------------------- brackets left by citations


def test_brackets_left_empty_by_a_citation_are_removed(xml: bytes) -> None:
    """JATS marks a citation two ways and only one takes its punctuation with it.

    ``<xref>[1]</xref>`` disappears cleanly; ``[<xref>1</xref>]`` and
    ``(<xref/>;<xref/>)`` leave "[]" and "(;)" sitting in the prose. 3,863 of
    those survived the first parse, in 80 of the 100 corpus papers.
    """
    paper = parse_article(xml, POLICY)
    assert "Tau aggregates appear early and spread widely." in paper.body
    assert "[]" not in paper.body
    assert "(;)" not in paper.body
    assert paper.parse_metadata["empty_citations_remaining"] == 0


def test_the_cleanup_leaves_no_space_before_the_punctuation_it_exposes(xml: bytes) -> None:
    """Removing " []" from "flies []." must close to "flies.", not "flies ."."""
    paper = parse_article(xml, POLICY)
    assert " ." not in paper.body
    assert " ," not in paper.body


def test_parentheses_carrying_content_are_not_touched(xml: bytes) -> None:
    """A cleanup that eats an editorial ellipsis or a stereochemistry prefix is
    worse than the residue it removes, so periods and dashes are deliberately
    outside the character class."""
    paper = parse_article(xml, POLICY)
    assert "The (-)-enantiomer bound tightly (...) at every dose." in paper.body


def test_count_empty_citations_is_the_check_not_the_cleanup() -> None:
    from ragbench.ingest.jats_body import count_empty_citations, normalise

    assert count_empty_citations("flies [] and rats (;;)") == 2
    assert count_empty_citations("the (-) form and (...) elsewhere") == 0
    assert normalise("human APP in flies [].") == "human APP in flies."
    assert normalise("works (;;;) and more [,,]") == "works and more"

