"""The prompt: assembled from config, digested by what the model sees.

Everything here is about the two ways a prompt can be wrong without looking
wrong -- a template that silently drops the context, and a digest that fails to
notice the context changed.
"""

from __future__ import annotations

import pytest

from ragbench.generation.prompt import (
    Prompt,
    build_prompt,
    render_context,
    template_digest,
)

PARAMS = {
    "prompt_template_id": "v1",
    "system_prompt": "Answer from the passages only.",
    "prompt_template": "Passages:\n\n{context}\n\nQuestion: {question}",
    "context_separator": "\n\n",
}


def test_the_template_comes_from_config_and_both_fields_are_substituted() -> None:
    prompt = build_prompt(PARAMS, "amyloid accumulates in the hippocampus", "where?")
    assert "amyloid accumulates in the hippocampus" in prompt.user
    assert "where?" in prompt.user
    assert prompt.system == "Answer from the passages only."


def test_a_template_missing_the_context_is_refused() -> None:
    """The failure it prevents is silent and expensive: 160 answers generated
    from the question alone, in a run that otherwise looks complete."""
    with pytest.raises(ValueError, match=r"\{context\}"):
        build_prompt({**PARAMS, "prompt_template": "Question: {question}"}, "ctx", "q")


def test_a_template_missing_the_question_is_refused() -> None:
    with pytest.raises(ValueError, match=r"\{question\}"):
        build_prompt({**PARAMS, "prompt_template": "{context}"}, "ctx", "q")


def test_an_empty_prompt_is_refused_rather_than_defaulted_in_code() -> None:
    """A default here would put the prompt back in the source, where changing it
    would not move the run id."""
    with pytest.raises(ValueError, match="prompt_template is empty"):
        build_prompt({**PARAMS, "prompt_template": "   "}, "ctx", "q")
    with pytest.raises(ValueError, match="system_prompt is empty"):
        build_prompt({**PARAMS, "system_prompt": ""}, "ctx", "q")


def test_a_passage_containing_a_placeholder_is_not_re_substituted() -> None:
    """Substituting one field then the other would let a passage rewrite itself.
    Scientific text really does contain braces -- set notation, code, LaTeX."""
    prompt = build_prompt(PARAMS, "the set {question} was measured", "how many?")
    assert "the set {question} was measured" in prompt.user
    # The literal survived AND the real question still landed.
    assert prompt.user.rstrip().endswith("how many?")


# ---------------------------------------------------------------- the context


def test_chunks_are_joined_in_the_order_they_were_given() -> None:
    """Rank order, not document order: re-sorting here would undo the rerank
    factor for the one arm it is supposed to distinguish."""
    assert render_context(["second", "first"], "\n\n") == "second\n\nfirst"


def test_chunk_whitespace_does_not_leak_into_the_separator() -> None:
    """Otherwise a chunk ending in a newline is spaced differently from one that
    does not, and the context carries a formatting difference that tracks the
    chunker rather than the text."""
    assert render_context(["a\n", "  b  "], "\n\n") == "a\n\nb"


def test_an_empty_context_still_renders() -> None:
    """A query that retrieved nothing must still reach the model, so the
    abstention is the model's and not an exception's."""
    prompt = build_prompt(PARAMS, render_context([], "\n\n"), "where?")
    assert "where?" in prompt.user


# ----------------------------------------------------------------- the digest


def test_the_digest_covers_what_the_model_sees() -> None:
    first = build_prompt(PARAMS, "context one", "q")
    second = build_prompt(PARAMS, "context two", "q")
    assert first.sha256 != second.sha256
    assert first.sha256 == build_prompt(PARAMS, "context one", "q").sha256


def test_the_digest_moves_when_the_system_turn_moves() -> None:
    """Both turns reach the model, so both must reach the digest."""
    other = {**PARAMS, "system_prompt": "Answer from the passages only!"}
    assert build_prompt(PARAMS, "c", "q").sha256 != build_prompt(other, "c", "q").sha256


def test_the_two_turns_cannot_be_confused_for_one_another() -> None:
    """A digest over concatenated text would collide when a word moves from the
    end of the system turn to the start of the user turn."""
    left = Prompt(system="ab", user="c", context="c", question="q")
    right = Prompt(system="a", user="bc", context="c", question="q")
    assert left.sha256 != right.sha256


# --------------------------------------------------- the template's own digest


def test_an_edited_v1_is_visible_even_though_the_label_did_not_change() -> None:
    """`prompt_template_id` is written by a human and can be forgotten. The
    digest is derived from the text, so a report can print both and an edited
    "v1" shows up as one whose digest no longer matches."""
    edited = {**PARAMS, "prompt_template": PARAMS["prompt_template"] + " Be brief."}
    assert edited["prompt_template_id"] == PARAMS["prompt_template_id"]
    assert template_digest(edited) != template_digest(PARAMS)


def test_the_separator_reaches_the_template_digest() -> None:
    """It changes every prompt in the run, so it is part of the prompt's identity."""
    assert template_digest({**PARAMS, "context_separator": "\n---\n"}) != template_digest(PARAMS)
