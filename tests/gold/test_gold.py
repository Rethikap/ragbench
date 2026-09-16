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
    STAND_IN,
    AuthoredDrafter,
    StandInDrafter,
    build_drafter,
    build_prompt,
    parse_reply,
)
from ragbench.gold.evidence import EvidenceError, contiguity_note, resolve, sentence_count
from ragbench.gold.freeze import (
    GoldSetError,
    gold_set_sha,
    read_gold_set,
    verify_frozen,
    write_gold_set,
)
from ragbench.gold.passages import Passage, blocks, candidates, deepest_section, sample
from ragbench.gold.pipeline import build_candidates, freeze_gold_set, selected_queries
from ragbench.gold.relevance import corpus_drift, section_kind, topic_score
from ragbench.gold.validate import (
    check,
    content_tokens,
    corpus_tokens,
    document_frequency,
    elsewhere_in_corpus,
    input_counts,
    longest_shared_ngram,
    provenance_markers,
)
from ragbench.ingest.jats import parse_article
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
    "section_kinds": {
        "results": ["results"],
        "discussion": ["discussion"],
        "methods": ["method"],
        "introduction": ["introduction"],
    },
    "preferred_section_kinds": ["results", "discussion"],
    "topic_terms": ["biomarker", "plasma", "amyloid"],
    "min_topic_terms": 1,
}

VALIDATION: dict[str, Any] = {
    "min_answer_grounding": 0.45,
    "max_question_leakage": 0.8,
    "max_other_papers_with_answer": 3,
    "corpus_coverage": 0.85,
    "max_abstract_overlap": 0.8,
    "max_shared_ngram": 10,
    "methods_section_kinds": ["methods"],
    "provenance_markers": {
        "vendor": ["sigma-aldrich", "hitachi"],
        "artefact": ["kit", "microscope", "package", "housed"],
        "equipment_unit": [" kv", "w/v"],
    },
    "result_markers": ["significant", "correlat", "lower", "higher", "associat"],
    "input_count_units": ["samples", "individuals", "cohort", "nerves", "rats", "participants"],
}

SECTION_PATTERNS = {
    "results": ["results"],
    "discussion": ["discussion", "conclusion"],
    "methods": ["method", "statistical analysis", "staining"],
    "introduction": ["introduction"],
}


def verdict(
    question: str,
    answer: str,
    span: str,
    abstract: str = "",
    others: dict[str, str] | None = None,
    section: str = "results",
    **overrides: Any,
) -> dict[str, Any]:
    """Run `check` against a one-paper corpus unless more papers are supplied."""
    corpus = {"PMC1": span, **(others or {})}
    return check(
        question,
        answer,
        span,
        abstract,
        "PMC1",
        corpus_tokens(corpus.items()),
        section,
        {**VALIDATION, **overrides},
    )


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


def test_an_off_topic_paper_is_not_sampled_at_all(paper: ParsedPaper) -> None:
    """A gate, not a tier. The topic rule used to be the first half of a tier key,
    which meant an off-topic paper was still drawn once the on-topic pool ran
    short -- and a soft preference expressed as ordering is only a preference."""
    params = {**GOLD_PARAMS, "topic_terms": ["glioma"], "min_topic_terms": 1}
    assert sample([paper], TOKENIZER, params, seed=1, n_passages=10) == []


def test_a_pinned_passage_bypasses_the_gate_and_says_so(paper: ParsedPaper) -> None:
    """Its record carries decisions that must stay readable; selection stops it
    instead, which is why the flag is carried through."""
    params = {**GOLD_PARAMS, "topic_terms": ["glioma"], "min_topic_terms": 1}
    first = candidates(paper, TOKENIZER, GOLD_PARAMS)[0]
    drawn = sample([paper], TOKENIZER, params, seed=1, n_passages=10, pinned=[first.passage_id])
    assert [p.passage_id for p in drawn] == [first.passage_id]
    assert drawn[0].pinned is True


def test_a_paper_may_offer_more_candidates_than_it_may_have_questions(
    paper: ParsedPaper,
) -> None:
    """The independence argument is about the gold set, not the pool: a second
    candidate from a paper whose first was rejected costs nothing, and once the
    gate has excluded half the corpus it is often the only material left."""
    params = {**GOLD_PARAMS, "max_per_paper": 1, "candidate_passages_per_paper": 2}
    assert len(candidates(paper, TOKENIZER, params)) >= 2
    assert len(sample([paper], TOKENIZER, params, seed=1, n_passages=10)) == 2


def test_the_draw_runs_short_rather_than_reaching_past_the_gate(paper: ParsedPaper) -> None:
    """Fewer candidates is a reportable shortfall; an off-topic one is a defect."""
    params = {**GOLD_PARAMS, "candidate_passages_per_paper": 2}
    assert len(sample([paper], TOKENIZER, params, seed=1, n_passages=50)) == 2


def test_length_bounds_are_enforced(paper: ParsedPaper) -> None:
    params = {**GOLD_PARAMS, "min_passage_tokens": 8, "max_passage_tokens": 12}
    for passage in candidates(paper, TOKENIZER, params):
        assert 8 <= TOKENIZER.count(passage.text) <= 12


# ---------------------------------------------------------------- validation


def test_content_tokens_drop_stopwords() -> None:
    assert content_tokens("The ratio of A to B is 42") == ["ratio", "b", "42"]


def test_document_frequency_counts_papers_not_occurrences() -> None:
    token_sets = corpus_tokens(
        [("PMC1", "amyloid amyloid amyloid"), ("PMC2", "amyloid tau")]
    )
    frequency = document_frequency(token_sets)
    assert frequency["amyloid"] == 2
    assert frequency["tau"] == 1


def test_longest_shared_ngram_finds_repeated_phrasing() -> None:
    first = content_tokens("plasma biomarker levels rose sharply in the treated cohort")
    second = content_tokens("we found plasma biomarker levels rose sharply overall")
    # "plasma biomarker levels rose sharply" -- the stopwords are already gone.
    assert longest_shared_ngram(first, second) == 5
    assert longest_shared_ngram(first, []) == 0


SPAN_TEXT = (
    "Plasma NfL was 24.8 pg/mL in carriers and was significantly higher than in "
    "non-carriers, and correlated with hippocampal atrophy."
)


def test_a_grounded_specific_finding_passes_every_check() -> None:
    result = verdict(
        "How did plasma NfL in carriers compare with non-carriers?",
        "It was significantly higher in carriers, at 24.8 pg/mL, and correlated with "
        "hippocampal atrophy.",
        SPAN_TEXT,
        abstract="This paper studies biomarkers of neurodegeneration.",
    )
    assert result["auto_rejected"] is False
    assert result["reasons"] == []


# ---- 1. answerable without the span


def test_a_question_that_states_its_own_answer_is_rejected() -> None:
    """The most direct form of "answerable without the span"."""
    result = verdict(
        "Was plasma NfL significantly higher in carriers, correlating with hippocampal "
        "atrophy, at 24.8 pg/mL?",
        "Plasma NfL was significantly higher, 24.8 pg/mL, correlating with hippocampal "
        "atrophy.",
        SPAN_TEXT,
    )
    assert result["flags"]["answerable_without_span"] is True
    assert result["signals"]["question_leakage"] >= 0.8


def test_an_answer_the_rest_of_the_corpus_already_states_is_rejected() -> None:
    """Scored as a conjunction over other papers, not as a bag of rarities: what
    matters is whether this answer is already in the literature."""
    common = "Amyloid beta and tau are biomarkers of Alzheimer disease."
    result = verdict(
        "Which proteins are biomarkers of Alzheimer disease?",
        "Amyloid beta and tau.",
        common,
        others={f"PMC{n}": common for n in range(2, 10)},
    )
    assert result["flags"]["answerable_without_span"] is True
    assert result["signals"]["other_papers_with_answer"] >= 4


def test_an_answer_of_ordinary_words_passes_if_its_combination_is_novel() -> None:
    """The property the old rare-token rule did not have, and the reason it
    steered nine questions into Methods: a finding made entirely of common words
    must be able to pass."""
    result = verdict(
        "How did carrier and non-carrier levels compare?",
        "Levels were significantly higher in carriers and correlated with hippocampal "
        "atrophy.",
        SPAN_TEXT,
        others={
            f"PMC{n}": "An unrelated paper about something else entirely."
            for n in range(2, 20)
        },
    )
    assert result["flags"]["answerable_without_span"] is False
    assert result["signals"]["other_papers_with_answer"] == 0


def test_an_answer_not_drawn_from_the_span_is_rejected() -> None:
    """The signature of a mislabelled span: the answer's tokens are not there."""
    result = verdict(
        "Which endonuclease cut the APOE amplicon?",
        "A 227 bp region cut by the CFo1 restriction endonuclease.",
        SPAN_TEXT,
    )
    assert result["flags"]["answerable_without_span"] is True
    assert result["signals"]["answer_grounding"] == 0.0


# ---- 2. methods provenance


def test_an_answer_naming_apparatus_is_rejected() -> None:
    """A provenance answer is retrieved by near-verbatim match under every
    configuration, so it discriminates between no two arms."""
    result = verdict(
        "How were the exosomes imaged?",
        "On a Hitachi H7600 transmission electron microscope, operated at 80 kV.",
        "Imaging was performed on a Hitachi H7600 transmission electron microscope, "
        "operated at 80 kV.",
    )
    assert result["flags"]["methods_provenance"] is True
    assert "vendor:hitachi" in result["signals"]["provenance_markers"]


def test_a_software_version_is_provenance() -> None:
    result = verdict(
        "How were the samples classified?",
        "With XGBoost version 0.90.",
        "The XGBoost package version 0.90 was used to classify the samples.",
    )
    assert result["flags"]["methods_provenance"] is True
    assert "version-string" in result["signals"]["provenance_markers"]


def test_provenance_markers_do_not_fire_on_findings_vocabulary() -> None:
    """Kept tight on purpose: "database" and "samples" occur in real findings."""
    assert provenance_markers(
        "49 samples were enriched across the database.", VALIDATION["provenance_markers"]
    ) == []


def test_a_p_value_is_not_read_as_a_software_version() -> None:
    result = verdict(
        "How strong was the association?",
        "It was significant, p = 0.0342, and correlated with atrophy.",
        "The association was significant, p = 0.0342, and correlated with atrophy.",
    )
    assert result["flags"]["methods_provenance"] is False


def test_a_methods_passage_without_result_language_warns_rather_than_rejects() -> None:
    """A positivity threshold is a design choice worth asking about and carries no
    result language either, so this is the verifier's call, not the checks'."""
    result = verdict(
        "What threshold defined tau positivity?",
        "Tau positivity was defined as a value above 24.8 pg/mL.",
        "Models tested associations with tau positivity (> 24.8 pg/mL).",
        section="methods",
    )
    assert result["flags"]["methods_provenance"] is False
    assert result["auto_rejected"] is False
    assert result["warnings"]


# ---- 3. placeholders


def test_a_question_about_a_dropped_artefact_is_rejected() -> None:
    result = verdict("What value does Table 3 report?", "24.8 pg/mL.", SPAN_TEXT)
    assert result["flags"]["needs_placeholder"] is True


def test_a_span_holding_a_placeholder_is_rejected() -> None:
    result = verdict(
        "What was the level?",
        "It was significantly higher, at 24.8 pg/mL.",
        "[TABLE: Table 3] Levels were significantly higher, at 24.8 pg/mL.",
    )
    assert result["flags"]["needs_placeholder"] is True


# ---- 4. the abstract


def test_an_answer_restated_in_the_abstract_is_rejected() -> None:
    result = verdict(
        "How did the levels compare?",
        "Plasma NfL was significantly higher in carriers at 24.8 pg/mL.",
        SPAN_TEXT,
        abstract="Plasma NfL was significantly higher in carriers at 24.8 pg/mL.",
    )
    assert result["flags"]["in_abstract"] is True


def test_a_span_near_duplicated_in_the_abstract_is_rejected() -> None:
    """Caught by shared phrasing, which vocabulary overlap alone cannot see:
    two paragraphs of one paper always share vocabulary."""
    result = verdict(
        "What was the cohort?",
        "The carriers.",
        SPAN_TEXT,
        abstract=SPAN_TEXT,
        max_abstract_overlap=0.99,
        max_shared_ngram=5,
    )
    assert result["flags"]["in_abstract"] is True
    assert result["signals"]["span_abstract_shared_ngram"] >= 5


# ---- corpus recoverability, directly


def test_elsewhere_in_corpus_scores_the_answer_as_a_conjunction() -> None:
    token_sets = corpus_tokens(
        [
            ("PMC1", "alpha beta gamma delta"),
            ("PMC2", "alpha beta gamma delta"),
            ("PMC3", "alpha beta"),
        ]
    )
    tokens = ["alpha", "beta", "gamma", "delta"]
    # PMC2 holds all four; PMC3 holds half, which is below the coverage bar.
    assert elsewhere_in_corpus(tokens, "PMC1", token_sets, 0.85) == 1
    assert elsewhere_in_corpus(tokens, "PMC1", token_sets, 0.4) == 2


# --------------------------------------------------------- sections and topics


def test_declared_section_type_beats_the_title() -> None:
    assert section_kind("2. Materials and Methods", "methods", SECTION_PATTERNS) == "methods"
    assert section_kind("Anything at all", "results", SECTION_PATTERNS) == "results"


def test_a_numbered_heading_falls_back_to_its_title() -> None:
    """Numbered headings usually carry no sec-type, which is why the fallback is
    not optional."""
    assert section_kind("2.4. Statistical Analysis", "", SECTION_PATTERNS) == "methods"
    assert section_kind("3. Results", "", SECTION_PATTERNS) == "results"
    assert section_kind("Cresyl Violet Staining", "", SECTION_PATTERNS) == "methods"
    assert section_kind("SM-RR coupling", "", SECTION_PATTERNS) == "other"


def test_topic_score_reads_the_front_matter_only(paper: ParsedPaper) -> None:
    """A paper about something else still uses the vocabulary in its discussion;
    what it is *about* is what it says in the title and abstract."""
    assert topic_score(paper, ["biomarker", "plasma"]) >= 1
    assert topic_score(paper, ["glioma", "sciatic"]) == 0


def test_corpus_drift_is_quantified(paper: ParsedPaper) -> None:
    """A limitation is only a limitation if it carries a number."""
    drift = corpus_drift([paper], {"topic_terms": ["glioma"], "min_topic_terms": 1})
    assert drift["n_off_topic"] == 1
    assert drift["off_topic_pmcids"] == [paper.pmcid]
    assert drift["off_topic_share"] == 1.0


# ------------------------------------------------------------------ drafters


def test_the_prompt_is_pinned_by_id() -> None:
    passage = Passage("p1", "PMC1", 0, 10, "Results", "Plasma NfL was 24.8 pg/mL.")
    assert "24.8" in build_prompt(passage, "v1")
    assert "24.8" in build_prompt(passage, "v2")
    with pytest.raises(ValueError, match="draft_prompt_id"):
        build_prompt(passage, "v3")


def test_v2_is_the_prompt_that_asks_for_a_finding() -> None:
    """v1 did not, and nine of the twenty questions it produced asked which
    instrument or reagent was used."""
    passage = Passage("p1", "PMC1", 0, 10, "Results", "Plasma NfL was 24.8 pg/mL.")
    assert "MUST BE A FINDING" in build_prompt(passage, "v2")
    assert "MUST BE A FINDING" not in build_prompt(passage, "v1")


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


def test_the_authored_drafter_refuses_a_passage_it_has_no_question_for() -> None:
    """A silent miss would drop a sampled passage and change what the rejection
    counts are measured against."""
    drafter = AuthoredDrafter({"p1": {"question": "q", "answer": "a", "drafted_by": "someone"}})
    assert drafter.draft(Passage("p1", "PMC1", 0, 1, "", "x")) == ("q", "a")
    assert drafter.drafted_by(Passage("p1", "PMC1", 0, 1, "", "x")) == "someone"
    with pytest.raises(ValueError, match="no authored question"):
        drafter.draft(Passage("p2", "PMC1", 0, 1, "", "x"))


def test_there_is_no_generator_drafted_option() -> None:
    """The system under test does not write the questions it will be scored on.

    A model asked to draft its own eval writes in its own idiom and then scores
    well partly because the questions sound like it. This is a design decision,
    not a gap: the error message says so rather than implying a TODO.
    """
    with pytest.raises(ValueError, match="no generator-drafted option"):
        build_drafter("qwen", {}, {})
    with pytest.raises(ValueError, match="unknown gold.drafter"):
        build_drafter("gpt", {}, {})


# --------------------------------------------------------------------- freeze


def _query(index: int, pmcid: str = "PMC1") -> Query:
    return Query(
        query_id=f"q{index:03d}",
        question=f"question {index}?",
        reference_answer=f"answer {index}",
        gold=GoldSpan(
            pmcid=pmcid,
            char_start=10 * index,
            char_end=10 * index + 50,
            section="R",
            context_start=10 * index - 10,
            context_end=10 * index + 200,
        ),
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
        gold=GoldSpan(
            pmcid="PMC1",
            char_start=11,
            char_end=60,
            section="R",
            context_start=0,
            context_end=210,
        ),
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


def _candidate(index: int, pmcid: str = "PMC1", **overrides: Any) -> dict[str, Any]:
    return {
        "query_id": f"q{index:03d}",
        "pmcid": pmcid,
        "char_start": 10,
        "char_end": 60,
        "context_start": 0,
        "context_end": 200,
        "section": "Results",
        "question": "question?",
        "answer": "answer",
        "evidence": "evidence text",
        "context": "context text",
        "evidence_sentences": 1,
        "contiguity_note": "",
        "drafted_by": "a human",
        "section_kind": "results",
        "topic_score": 5,
        "on_topic": True,
        "off_topic_override": False,
        "pinned": False,
        "warnings": [],
        "selected": True,
        "rejection_reason": "",
        "note": "",
        "verified": True,
        "auto_rejected": False,
        "reasons": [],
        **overrides,
    }


def _resolved(n_questions: int = 2) -> dict[str, Any]:
    return {"gold": {"n_questions": n_questions}}


def test_selecting_a_question_from_an_off_topic_paper_is_refused(tmp_path: Path) -> None:
    """The gate keeps off-topic papers out of the sample, but a paper already
    written about is exempt so its record stays readable -- so the gate has to
    exist again at selection, or an off-topic question reaches the set the way
    four of them did."""
    off = _candidate(2, pmcid="PMC2", on_topic=False)
    with pytest.raises(ValueError, match="below\ngold.min_topic_terms|min_topic_terms"):
        freeze_gold_set(_resolved(2), [_candidate(1), off], tmp_path)


def test_an_off_topic_override_needs_a_written_reason(tmp_path: Path) -> None:
    """An override with no stated reason is indistinguishable from an oversight,
    which is the failure it exists to prevent."""
    silent = _candidate(2, pmcid="PMC2", on_topic=False, off_topic_override=True, note="")
    with pytest.raises(ValueError, match="no note"):
        freeze_gold_set(_resolved(2), [_candidate(1), silent], tmp_path)

    spoken = _candidate(
        2, pmcid="PMC2", on_topic=False, off_topic_override=True,
        note="the topic score understates the paper; its subject is AD",
    )
    result = freeze_gold_set(_resolved(2), [_candidate(1), spoken], tmp_path)
    assert result["n_questions"] == 2


def test_two_selected_questions_from_one_paper_are_refused(tmp_path: Path) -> None:
    """Two questions from one paper share its abstract, its vocabulary and its
    distractors, so they are not two independent measurements of retrieval."""
    with pytest.raises(ValueError, match="more than one selected question"):
        freeze_gold_set(_resolved(2), [_candidate(1), _candidate(2)], tmp_path)


def test_freezing_writes_only_the_selected_candidates(tmp_path: Path) -> None:
    candidates_list = [
        _candidate(1),
        _candidate(2, pmcid="PMC2"),
        _candidate(3, pmcid="PMC3", selected=False),
    ]
    result = freeze_gold_set(_resolved(2), candidates_list, tmp_path)
    queries = read_gold_set(result["path"])
    assert [query.query_id for query in queries] == ["q001", "q002"]
    assert all(query.verified for query in queries)
    assert result["gold_set_sha"] == gold_set_sha(queries)


def test_the_candidate_trail_is_written_beside_the_gold_set(tmp_path: Path) -> None:
    """A rejection rate quoted without the rejections is not evidence."""
    candidates_list = [
        _candidate(1),
        _candidate(2, pmcid="PMC2"),
        _candidate(3, pmcid="PMC3", selected=False),
    ]
    result = freeze_gold_set(_resolved(2), candidates_list, tmp_path)
    assert result["candidates_path"].is_file()
    assert len(result["candidates_path"].read_text(encoding="utf-8").splitlines()) == 3


def test_freezing_a_stand_in_draft_is_refused(tmp_path: Path) -> None:
    candidates_list = [_candidate(1, drafted_by=STAND_IN), _candidate(2, pmcid="PMC2")]
    with pytest.raises(ValueError, match="stand-in"):
        freeze_gold_set(_resolved(2), candidates_list, tmp_path)


def test_freezing_an_unverified_question_is_refused(tmp_path: Path) -> None:
    """The guard that matters most.

    Selection is editorial and cheap; verification is a claim that a human read
    the question, the answer and the span and found them right. Freezing stamps
    a digest over that claim, so an unverified record must stop it -- the same
    way a stand-in draft does.
    """
    candidates_list = [_candidate(1), _candidate(2, pmcid="PMC2", verified=False)]
    with pytest.raises(ValueError, match="not verified"):
        freeze_gold_set(_resolved(2), candidates_list, tmp_path)


def test_the_refusal_names_every_unverified_question(tmp_path: Path) -> None:
    """So the author knows what is left to read, not just that something is."""
    candidates_list = [_candidate(1, verified=False), _candidate(2, pmcid="PMC2", verified=False)]
    with pytest.raises(ValueError) as caught:
        freeze_gold_set(_resolved(2), candidates_list, tmp_path)
    assert "q001" in str(caught.value)
    assert "q002" in str(caught.value)


def test_selection_alone_does_not_make_a_question_verified() -> None:
    """The two flags are separate fields and must stay separate."""
    queries = selected_queries(
        [_candidate(1, verified=False), _candidate(2, pmcid="PMC2", selected=False)]
    )
    assert [query.query_id for query in queries] == ["q001"]
    assert queries[0].verified is False


def test_selecting_a_candidate_that_failed_a_check_is_refused(tmp_path: Path) -> None:
    """Hand verification may override taste, not the three checks."""
    failed = _candidate(2, pmcid="PMC2", auto_rejected=True, reasons=["in_abstract"])
    with pytest.raises(ValueError, match="failed a mechanical check"):
        freeze_gold_set(_resolved(2), [_candidate(1), failed], tmp_path)


def test_the_wrong_number_of_questions_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="n_questions"):
        freeze_gold_set(_resolved(20), [_candidate(1), _candidate(2, pmcid="PMC2")], tmp_path)


# ------------------------------------------------------------ evidence spans


def test_anchors_resolve_to_the_minimal_span(paper: ParsedPaper) -> None:
    start, end = blocks(paper.body)[1]
    text = paper.body[start:end]
    words = text.split()
    prefix, suffix = words[0], words[-1]
    found = resolve(paper, start, end, prefix, suffix, "q001")
    assert paper.body[found[0] : found[1]].startswith(prefix)
    assert paper.body[found[0] : found[1]].endswith(suffix)
    assert start <= found[0] < found[1] <= end


def test_an_anchor_outside_the_paragraph_is_not_found(paper: ParsedPaper) -> None:
    """Anchors match inside the context only, so a phrase occurring elsewhere in
    the paper cannot drag the span out of the paragraph it belongs to."""
    start, end = blocks(paper.body)[0]
    with pytest.raises(EvidenceError, match="occurs 0 times"):
        resolve(paper, start, end, "definitely not in this paragraph", "either", "q001")


def test_an_ambiguous_anchor_is_refused(paper: ParsedPaper) -> None:
    """A human writing "the" cannot have meant all four occurrences."""
    body = paper.body
    start = body.index("Amyloid")
    end = start + 200
    with pytest.raises(EvidenceError, match="occurs .* times"):
        resolve(paper, start, end, " ", "e", "q001")


def test_a_span_must_be_inside_its_context() -> None:
    """The context is provenance for the span; a span outside it is incoherent."""
    with pytest.raises(ValueError, match="not inside its context"):
        GoldSpan(
            pmcid="PMC1", char_start=5, char_end=50, section="R",
            context_start=10, context_end=40,
        )


def test_an_empty_span_is_refused_at_construction() -> None:
    with pytest.raises(ValueError, match="empty evidence span"):
        GoldSpan(
            pmcid="PMC1", char_start=10, char_end=10, section="R",
            context_start=0, context_end=100,
        )


def test_a_multi_sentence_span_is_flagged_for_the_verifier() -> None:
    """A question whose answer is stated in two places forces a wider span. That
    is a signal about the question, and the author should see it while
    verifying rather than discover it afterwards."""
    assert sentence_count("One fact here.") == 1
    assert sentence_count("One fact here. And another there.") == 2
    assert contiguity_note("One fact here.") == ""
    assert "more than one place" in contiguity_note("One fact. Filler. Another fact.")


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
            "authored_filename": "gold_drafts.jsonl",
            "draft_prompt_id": "v2",
            "methods_section_kinds": ["methods"],
            "validation": VALIDATION,
        },
    }
    report = build_candidates(
        resolved, tmp_path / "manifest.jsonl", tmp_path, tmp_path / "out", tmp_path
    )
    assert report["n_drafted"] >= 1
    assert report["drafter"] == "stand-in"
    assert report["n_verified"] == 0
    for record in report["records"]:
        assert record["verified"] is False
        assert record["selected"] is False
        assert stored.body[record["char_start"] : record["char_end"]] == record["evidence"]
        assert stored.body[record["context_start"] : record["context_end"]] == record["context"]


# ---------------------------------------------- counts: inputs vs findings


INPUT_UNITS = ["samples", "individuals", "cohort", "nerves", "rats", "participants"]


def test_a_count_of_findings_is_a_finding() -> None:
    """The rule, on the case that makes it non-obvious. q044's answer counts what
    the study discovered, and is the paper's result."""
    answer = (
        "A core group of 48 proteins was consistently enriched in plaques compared with "
        "neighbouring non-plaque tissue in both conditions."
    )
    assert input_counts(answer, INPUT_UNITS) == []


def test_a_count_of_inputs_is_provenance() -> None:
    """q013: 171 miRNAs measured in 648 people describes what went in."""
    answer = (
        "171 plasma-circulating miRNAs, in a cohort of 648 individuals from the general "
        "population."
    )
    assert "648 individuals" in input_counts(answer, INPUT_UNITS)


def test_a_half_and_half_answer_is_provenance_on_the_input_half() -> None:
    """q021 counts both an input and a result; the input half is enough to reject,
    the same way q036's half-provenance was."""
    answer = (
        "49 samples, from which WGCNA identified 10 modules of highly coexpressed genes "
        "ranging from 32 to 708 nodes in size."
    )
    assert input_counts(answer, INPUT_UNITS) == ["49 samples"]


def test_an_input_count_rejects_through_methods_provenance() -> None:
    result = verdict(
        "How many people were studied?",
        "A cohort of 648 individuals from the general population.",
        "We studied a cohort of 648 individuals from the general population.",
    )
    assert result["flags"]["methods_provenance"] is True
    assert result["signals"]["input_counts"]


def test_a_number_and_a_unit_in_different_clauses_are_not_a_count() -> None:
    """q061 contains both a number and "rats" and is a finding; they are twelve
    words apart and in different clauses, which is what the proximity rule is for."""
    answer = (
        "At 10 months there were no differences in microglial numbers between transgenic "
        "and control rats; by 18-20 months the microglia showed extensive proliferation "
        "and an activated phenotype."
    )
    assert input_counts(answer, INPUT_UNITS) == []


def test_an_intervening_strain_name_does_not_hide_the_count() -> None:
    """q024: "56 Sprague-Dawley rats" is still a count of animals."""
    assert input_counts("112 nerves from 56 Sprague-Dawley rats", INPUT_UNITS) == [
        "112 nerves",
        "56 Sprague-Dawley rats",
        "nerves from 56",
    ]
