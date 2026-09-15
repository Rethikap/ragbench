"""Gold-set construction: sampling, the three checks, and the freeze.

Everything here runs offline against the committed JATS fixture and the
whitespace tokenizer. The stand-in drafter is exercised too, because the thing
being tested is the pipeline, not the quality of any model's questions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ragbench.gold.draft import (
    ReplayDrafter,
    StandInDrafter,
    build_drafter,
    build_prompt,
    parse_reply,
)
from ragbench.gold.freeze import (
    GoldSetError,
    gold_set_sha,
    read_gold_set,
    verify_frozen,
    write_gold_set,
)
from ragbench.gold.passages import Passage, blocks, candidates, deepest_section
from ragbench.gold.pipeline import build_candidates, freeze_gold_set
from ragbench.gold.validate import check, content_tokens, document_frequency, longest_shared_ngram
from ragbench.ingest.jats import parse_article
from ragbench.jsonl import write_jsonl
from ragbench.tokenizers import WhitespaceTokenizer
from ragbench.types import GoldSpan, ParsedPaper, Query

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "sample_article.xml"
POLICY = {
    "drop_references": True,
    "drop_figure_captions": True,
    "drop_bibliographic_xrefs": True,
    "table_policy": "placeholder",
    "equation_policy": "placeholder",
    "keep_abstract": True,
}
TOKENIZER = WhitespaceTokenizer()

GOLD_PARAMS: dict[str, Any] = {
    "min_passage_tokens": 3,
    "max_passage_tokens": 200,
    "max_per_paper": 1,
    "excluded_section_patterns": ["acknowledg"],
}

VALIDATION = {
    "min_answer_grounding": 0.45,
    "max_anchor_df": 25,
    "max_abstract_overlap": 0.8,
    "max_shared_ngram": 10,
}


@pytest.fixture
def paper() -> ParsedPaper:
    return parse_article(FIXTURE.read_bytes(), POLICY)


# ---------------------------------------------------------------- passages


def test_blocks_index_the_body_exactly(paper: ParsedPaper) -> None:
    for start, end in blocks(paper.body):
        text = paper.body[start:end]
        assert text == text.strip()
        assert text


def test_section_headings_are_not_passages(paper: ParsedPaper) -> None:
    """render_body emits a section's title as its own block; a title is not prose
    anyone can ask a question about."""
    titles = {section.title for section in paper.sections if section.title}
    found = {passage.text for passage in candidates(paper, TOKENIZER, GOLD_PARAMS)}
    assert found
    assert not (found & titles)


def test_passages_never_contain_a_placeholder(paper: ParsedPaper) -> None:
    """A question whose answer sits behind [TABLE: ...] is unanswerable from the
    corpus as parsed, so such a paragraph may not be sampled at all."""
    assert "[TABLE:" in paper.body
    for passage in candidates(paper, TOKENIZER, GOLD_PARAMS):
        assert "[TABLE:" not in passage.text
        assert "[EQUATION]" not in passage.text


def test_excluded_sections_are_not_sampled(paper: ParsedPaper) -> None:
    sections = {passage.section for passage in candidates(paper, TOKENIZER, GOLD_PARAMS)}
    assert not any("acknowledg" in section.lower() for section in sections)


def test_deepest_section_wins(paper: ParsedPaper) -> None:
    """A Methods sub-section is inside Methods; the sub-section is what places
    the passage for a reader."""
    nested = [s for s in paper.sections if s.depth > 0]
    if not nested:
        pytest.skip("fixture has no nested sections")
        return
    section = nested[0]
    assert deepest_section(paper, section.char_start, section.char_end) == section.title


def test_length_bounds_are_enforced(paper: ParsedPaper) -> None:
    params = {**GOLD_PARAMS, "min_passage_tokens": 8, "max_passage_tokens": 12}
    for passage in candidates(paper, TOKENIZER, params):
        assert 8 <= TOKENIZER.count(passage.text) <= 12


# ---------------------------------------------------------------- validation


def test_content_tokens_drop_stopwords() -> None:
    assert content_tokens("The ratio of A to B is 42") == ["ratio", "b", "42"]


def test_document_frequency_counts_papers_not_occurrences() -> None:
    frequency = document_frequency(["amyloid amyloid amyloid", "amyloid tau"])
    assert frequency["amyloid"] == 2
    assert frequency["tau"] == 1


def test_longest_shared_ngram_finds_repeated_phrasing() -> None:
    first = content_tokens("plasma biomarker levels rose sharply in the treated cohort")
    second = content_tokens("we found plasma biomarker levels rose sharply overall")
    # "plasma biomarker levels rose sharply" -- the stopwords are already gone.
    assert longest_shared_ngram(first, second) == 5
    assert longest_shared_ngram(first, []) == 0


PASSAGE_TEXT = "Plasma NfL was measured at 24.8 pg/mL in the WT161 cohort using a Simoa assay."


def test_a_grounded_specific_answer_passes_every_check() -> None:
    verdict = check(
        "At what concentration was plasma NfL measured in the WT161 cohort?",
        "Plasma NfL was 24.8 pg/mL, measured with a Simoa assay.",
        PASSAGE_TEXT,
        abstract="This paper studies biomarkers of neurodegeneration.",
        frequency={"plasma": 90, "nfl": 40, "24.8": 1, "simoa": 3, "wt161": 1},
        params=VALIDATION,
    )
    assert verdict["auto_rejected"] is False
    assert verdict["reasons"] == []


def test_an_answer_of_only_common_words_is_general_knowledge() -> None:
    """Nothing in it distinguishes this paper from the other 99."""
    verdict = check(
        "What was measured?",
        "Plasma NfL was measured.",
        PASSAGE_TEXT,
        abstract="",
        frequency={"plasma": 90, "nfl": 40, "measured": 95},
        params=VALIDATION,
    )
    assert verdict["flags"]["general_knowledge"] is True
    assert verdict["evidence"]["n_rare_anchors"] == 0


def test_an_answer_not_drawn_from_the_passage_is_rejected() -> None:
    """The signature of a mislabelled span: the answer's tokens are not there."""
    verdict = check(
        "Which endonuclease cut the APOE amplicon?",
        "A 227 bp region cut by the CFo1 restriction endonuclease.",
        PASSAGE_TEXT,
        abstract="",
        frequency={"cfo1": 1, "227": 2},
        params=VALIDATION,
    )
    assert verdict["flags"]["general_knowledge"] is True
    assert verdict["evidence"]["answer_grounding"] == 0.0


def test_a_question_about_a_dropped_artefact_is_rejected() -> None:
    verdict = check(
        "What value does Table 3 report for plasma NfL?",
        "24.8 pg/mL.",
        PASSAGE_TEXT,
        abstract="",
        frequency={"24.8": 1},
        params=VALIDATION,
    )
    assert verdict["flags"]["needs_placeholder"] is True


def test_a_passage_holding_a_placeholder_is_rejected() -> None:
    verdict = check(
        "What was the assay?",
        "A Simoa assay measuring 24.8 pg/mL.",
        "[TABLE: Table 3] Plasma NfL was 24.8 pg/mL using a Simoa assay.",
        abstract="",
        frequency={"24.8": 1, "simoa": 3},
        params=VALIDATION,
    )
    assert verdict["flags"]["needs_placeholder"] is True


def test_an_answer_restated_in_the_abstract_is_rejected() -> None:
    verdict = check(
        "At what concentration was plasma NfL measured?",
        "Plasma NfL was 24.8 pg/mL using a Simoa assay.",
        PASSAGE_TEXT,
        abstract="Plasma NfL was 24.8 pg/mL using a Simoa assay in the WT161 cohort.",
        frequency={"24.8": 1, "simoa": 3},
        params=VALIDATION,
    )
    assert verdict["flags"]["in_abstract"] is True


def test_a_passage_near_duplicated_in_the_abstract_is_rejected() -> None:
    """Caught by shared phrasing, which vocabulary overlap alone cannot see:
    two paragraphs of one paper always share vocabulary."""
    verdict = check(
        "What was the cohort?",
        "The WT161 cohort, measured by Simoa.",
        PASSAGE_TEXT,
        abstract=PASSAGE_TEXT,
        frequency={"wt161": 1, "simoa": 3},
        params={**VALIDATION, "max_abstract_overlap": 0.99, "max_shared_ngram": 5},
    )
    assert verdict["flags"]["in_abstract"] is True
    assert verdict["evidence"]["passage_abstract_shared_ngram"] >= 5


# ------------------------------------------------------------------ drafters


def test_the_prompt_is_pinned_by_id() -> None:
    passage = Passage("p1", "PMC1", 0, 10, "Results", "Plasma NfL was 24.8 pg/mL.")
    assert "24.8" in build_prompt(passage, "v1")
    with pytest.raises(ValueError, match="draft_prompt_id"):
        build_prompt(passage, "v2")


def test_a_reply_without_the_two_fields_is_an_error() -> None:
    assert parse_reply("QUESTION: What?\nANSWER: This.") == ("What?", "This.")
    with pytest.raises(ValueError, match="QUESTION/ANSWER"):
        parse_reply("I'm afraid I can't do that.")


def test_the_stand_in_masks_the_rarest_token() -> None:
    passage = Passage("p1", "PMC1", 0, 40, "Results", "Plasma NfL was 24.8 pg/mL overall.")
    # document_frequency covers every token of the corpus, so every token a
    # passage contains has a count of at least 1; an absent key would be treated
    # as rarer than anything present.
    frequency = {"plasma": 90, "nfl": 40, "24.8": 1, "pg": 60, "ml": 60, "overall": 70}
    question, answer = StandInDrafter(frequency).draft(passage)
    assert answer == "24.8"
    assert "____" in question


def test_replay_refuses_a_passage_it_has_no_draft_for(tmp_path: Path) -> None:
    """A silent miss would drop a sampled passage and change what the rejection
    counts are measured against."""
    path = tmp_path / "drafts.jsonl"
    write_jsonl(path, [{"passage_id": "p1", "question": "q", "answer": "a"}])
    drafter = ReplayDrafter(str(path))
    assert drafter.draft(Passage("p1", "PMC1", 0, 1, "", "x")) == ("q", "a")
    with pytest.raises(ValueError, match="no recorded draft"):
        drafter.draft(Passage("p2", "PMC1", 0, 1, "", "x"))


def test_unknown_drafter_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown gold.drafter"):
        build_drafter("gpt", {}, "v1", {})


# --------------------------------------------------------------------- freeze


def _query(index: int, pmcid: str = "PMC1") -> Query:
    return Query(
        query_id=f"q{index:03d}",
        question=f"question {index}?",
        reference_answer=f"answer {index}",
        gold=GoldSpan(pmcid=pmcid, char_start=10 * index, char_end=10 * index + 50, section="R"),
        verified=True,
    )


def test_the_digest_is_order_independent() -> None:
    """Sampling order is seeded and deliberately not corpus order; the stored
    order must not decide the evaluation set's identity."""
    queries = [_query(3), _query(1), _query(2)]
    assert gold_set_sha(queries) == gold_set_sha(list(reversed(queries)))


def test_changing_a_span_changes_the_digest() -> None:
    before = gold_set_sha([_query(1)])
    moved = Query(
        query_id="q001",
        question="question 1?",
        reference_answer="answer 1",
        gold=GoldSpan(pmcid="PMC1", char_start=11, char_end=60, section="R"),
        verified=True,
    )
    assert gold_set_sha([moved]) != before


def test_gold_set_round_trips_through_jsonl(tmp_path: Path) -> None:
    queries = [_query(1), _query(2)]
    path = tmp_path / "gold_set.jsonl"
    write_gold_set(path, queries)
    loaded = read_gold_set(path)
    assert loaded == queries
    assert isinstance(loaded[0].gold, GoldSpan)


def test_an_altered_gold_set_is_caught(tmp_path: Path) -> None:
    path = tmp_path / "gold_set.jsonl"
    write_gold_set(path, [_query(1), _query(2)])
    digest = gold_set_sha([_query(1), _query(2)])
    assert verify_frozen(path, digest)
    write_gold_set(path, [_query(1), _query(2), _query(3)])
    with pytest.raises(GoldSetError, match="digest mismatch"):
        verify_frozen(path, digest)


def test_an_unfrozen_gold_set_refuses_to_load(tmp_path: Path) -> None:
    path = tmp_path / "gold_set.jsonl"
    write_gold_set(path, [_query(1)])
    with pytest.raises(GoldSetError, match="unfrozen"):
        verify_frozen(path, "unfrozen")


# ------------------------------------------------------------- freeze guards


def _candidate(index: int, **overrides: Any) -> dict[str, Any]:
    return {
        "query_id": f"q{index:03d}",
        "pmcid": "PMC1",
        "char_start": 0,
        "char_end": 50,
        "section": "Results",
        "question": "question?",
        "answer": "answer",
        "drafted_by": "replay:drafts.jsonl",
        "verified": True,
        "auto_rejected": False,
        "reasons": [],
        **overrides,
    }


def _resolved(n_questions: int = 2) -> dict[str, Any]:
    return {"gold": {"n_questions": n_questions}}


def test_freezing_writes_only_the_verified_candidates(tmp_path: Path) -> None:
    candidates_list = [_candidate(1), _candidate(2), _candidate(3, verified=False)]
    result = freeze_gold_set(_resolved(2), candidates_list, tmp_path)
    queries = read_gold_set(result["path"])
    assert [query.query_id for query in queries] == ["q001", "q002"]
    assert all(query.verified for query in queries)
    assert result["gold_set_sha"] == gold_set_sha(queries)


def test_the_candidate_trail_is_written_beside_the_gold_set(tmp_path: Path) -> None:
    """A rejection rate quoted without the rejections is not evidence."""
    candidates_list = [_candidate(1), _candidate(2), _candidate(3, verified=False)]
    result = freeze_gold_set(_resolved(2), candidates_list, tmp_path)
    assert result["candidates_path"].is_file()
    assert len(result["candidates_path"].read_text(encoding="utf-8").splitlines()) == 3


def test_freezing_a_stand_in_draft_is_refused(tmp_path: Path) -> None:
    candidates_list = [_candidate(1, drafted_by=StandInDrafter.name), _candidate(2)]
    with pytest.raises(ValueError, match="stand-in"):
        freeze_gold_set(_resolved(2), candidates_list, tmp_path)


def test_verifying_a_candidate_that_failed_a_check_is_refused(tmp_path: Path) -> None:
    """Hand verification may override taste, not the three checks."""
    failed = _candidate(2, auto_rejected=True, reasons=["in_abstract"])
    with pytest.raises(ValueError, match="failed a check"):
        freeze_gold_set(_resolved(2), [_candidate(1), failed], tmp_path)


def test_the_wrong_number_of_questions_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="n_questions"):
        freeze_gold_set(_resolved(20), [_candidate(1), _candidate(2)], tmp_path)


# ------------------------------------------------------------------ end to end


def test_the_whole_gold_path_runs_offline(tmp_path: Path, monkeypatch: Any) -> None:
    """Smoke test: sample, draft with the stand-in, check, and write candidates,
    with no GPU and no download."""
    from ragbench.gold import pipeline

    stored = parse_article(FIXTURE.read_bytes(), POLICY)
    monkeypatch.setattr(pipeline, "load_papers", lambda *a, **k: [stored])
    monkeypatch.setattr(pipeline, "load_tokenizer", lambda *a, **k: TOKENIZER)

    resolved = {
        "base": {
            "seed": 1,
            "chunking": {"tokenizer_id": "whitespace", "tokenizer_revision": "x"},
            "generation": {},
        },
        "corpus": {"manifest_sha": "0" * 12},
        "gold": {
            **GOLD_PARAMS,
            "n_questions": 1,
            "candidate_multiplier": 2,
            "drafter": "stand-in",
            "draft_prompt_id": "v1",
            "validation": VALIDATION,
        },
    }
    report = build_candidates(resolved, tmp_path / "manifest.jsonl", tmp_path, tmp_path / "out")
    assert report["n_drafted"] >= 1
    assert report["drafter"] == "stand-in"
    for record in report["records"]:
        assert record["verified"] is False
        assert stored.body[record["char_start"] : record["char_end"]] == record["passage"]
