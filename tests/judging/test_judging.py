"""The judge stage: the rubric's vocabulary, the client's manners, and resuming.

All offline. No API key, no network, no spend. What is tested is the contract
around the hosted judge -- that an abstention is never scored, that a malformed
reply is retried once and then counted rather than coerced, that a bad key fails
instantly instead of after five backoffs, and that a metered stage never pays
twice for the same call.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ragbench.gold.freeze import gold_set_sha, write_gold_set
from ragbench.jsonl import write_jsonl
from ragbench.judging.base import (
    ABSTAINED,
    UNPARSED,
    JudgeError,
    JudgeQuotaExhausted,
    Verdict,
    build_judge,
    judge_params,
    parse_verdict,
)
from ragbench.judging.pipeline import (
    judge_one_config,
    judgements_path,
    load_judgements,
)
from ragbench.judging.prompt import build_prompt, rubric_digest
from ragbench.judging.standin import StandInJudge
from ragbench.types import (
    Chunk,
    GeneratedAnswer,
    GoldSpan,
    Judgement,
    Query,
    RetrievalResult,
    ScoredChunk,
)

REFUSAL = "The provided context does not contain the answer."
JUDGE: dict[str, Any] = {
    "provider": "openrouter",
    "model_id": "stand-in",
    "temperature": 0.0,
    "seed": 1,
    "max_tokens": 400,
    "api_key_env": "RAGBENCH_TEST_KEY",
    "requests_per_minute": 0,
    "max_retries": 3,
    "require_json_object": True,
    "passes": 2,
    "rubric_id": "v1",
    "scales": ["faithfulness", "relevance", "completeness"],
    "verdicts": ["correct", "partially_correct", "incorrect", "abstained"],
    "system_prompt": "Grade the answer.",
    "prompt_template": (
        "QUESTION:\n{question}\n\nREFERENCE:\n{reference_answer}\n\n"
        "PASSAGES:\n{context}\n\nANSWER:\n{answer}\n{judge_note}"
    ),
    "judge_note_template": "\nSPECIAL INSTRUCTION: {judge_note}",
    "retry_instruction": "JSON only.",
    "calibration_sample": 4,
    "calibration_seed": 1,
    "refusal_text": REFUSAL,
}


def prompt(answer: str = "the hippocampus", context: str = "plaques in the hippocampus"):
    return build_prompt(JUDGE, "where?", "the hippocampus", context, answer)


# ------------------------------------------------------- the rubric's vocabulary


def test_a_verdict_outside_the_rubric_is_refused_not_coerced() -> None:
    """A judge answering "good" has not followed the rubric, and mapping it onto
    the nearest permitted word would put a number in the results that no rubric
    defines."""
    with pytest.raises(ValueError, match="not one of"):
        parse_verdict({"verdict": "good", "faithfulness": 5}, JUDGE)


def test_a_score_off_the_scale_is_refused() -> None:
    payload = {"verdict": "correct", "faithfulness": 7, "relevance": 5, "completeness": 5}
    with pytest.raises(ValueError, match="outside the 1-5 scale"):
        parse_verdict(payload, JUDGE)


def test_a_non_abstention_may_not_leave_a_scale_null() -> None:
    payload = {"verdict": "correct", "faithfulness": None, "relevance": 5, "completeness": 5}
    with pytest.raises(ValueError, match="only an abstention may be"):
        parse_verdict(payload, JUDGE)


def test_an_abstention_carries_no_scores_even_if_the_judge_supplies_them() -> None:
    """Scoring an abstention 5 for faithfulness would reward a configuration for
    retrieving badly: the answer asserts nothing, so it cannot be unfaithful."""
    parsed = parse_verdict(
        {"verdict": "abstained", "faithfulness": 5, "relevance": 5, "completeness": 1}, JUDGE
    )
    assert parsed.verdict == ABSTAINED
    assert parsed.scores == {}
    assert not parsed.scored


def test_verdict_spelling_is_normalised_but_not_invented() -> None:
    assert parse_verdict({"verdict": "Partially Correct", "faithfulness": 3,
                          "relevance": 3, "completeness": 3}, JUDGE).verdict == "partially_correct"


# ------------------------------------------------------------------ the prompt


def test_the_judge_is_shown_the_retrieved_passages() -> None:
    """Faithfulness is a question about what the system was SHOWN. Without the
    passages the judge would be comparing the answer to the reference and
    calling the result grounding."""
    rendered = prompt(context="a very distinctive passage")
    assert "a very distinctive passage" in rendered.user


def test_a_template_without_the_context_is_refused() -> None:
    broken = {**JUDGE, "prompt_template": "{question} {reference_answer} {answer}"}
    with pytest.raises(ValueError, match=r"\{context\}"):
        build_prompt(broken, "q", "r", "c", "a")


def test_the_gold_notes_reach_the_judge_and_nothing_else_gets_an_empty_heading() -> None:
    """Two of twenty records carry a note; the other eighteen must not be
    prompted with a blank instruction block that invites one to be invented."""
    with_note = build_prompt(JUDGE, "q", "r", "c", "a", judge_note="the source is malformed")
    without = build_prompt(JUDGE, "q", "r", "c", "a")
    assert "the source is malformed" in with_note.user
    assert "SPECIAL INSTRUCTION" in with_note.user
    assert "SPECIAL INSTRUCTION" not in without.user


def test_an_edited_rubric_is_visible_even_when_the_label_did_not_change() -> None:
    edited = {**JUDGE, "system_prompt": JUDGE["system_prompt"] + " Be strict."}
    assert edited["rubric_id"] == JUDGE["rubric_id"]
    assert rubric_digest(edited) != rubric_digest(JUDGE)


# --------------------------------------------------------------- the stand-in


def test_the_stand_in_is_selected_by_id_and_is_deterministic() -> None:
    judge = build_judge(JUDGE)
    assert isinstance(judge, StandInJudge)
    assert judge.score(prompt()) == judge.score(prompt())


def test_the_stand_in_recognises_the_refusal() -> None:
    assert build_judge(JUDGE).score(prompt(answer=REFUSAL)).verdict == ABSTAINED


def test_an_unknown_provider_is_refused() -> None:
    with pytest.raises(JudgeError, match="unknown judge provider"):
        build_judge({**JUDGE, "model_id": "real", "provider": "invented"})


# ----------------------------------------------------- the judge is not the generator


def _shipped() -> dict[str, Any]:
    import yaml

    return yaml.safe_load(Path("configs/base.yaml").read_text(encoding="utf-8"))


def test_the_shipped_config_does_not_let_the_generator_judge_itself() -> None:
    """Self-preference bias stacked on small-judge unreliability, and the two
    are not separable after the fact. Checked for the SELECTED provider and for
    every alternative, so switching backends cannot reintroduce it."""
    base = _shipped()
    generator = str(base["generation"]["model_id"]).lower()

    active = judge_params({"base": base})
    assert str(active["model_id"]).lower() != generator
    assert "qwen" not in str(active["model_id"]).lower()

    for name, block in base["judge"]["providers"].items():
        model = str(block["model_id"]).lower()
        assert model != generator, f"{name} would have the generator judge itself"
        assert "qwen" not in model, f"{name} names a Qwen model"


def test_the_selected_judge_is_the_largest_non_qwen_option_on_the_tier() -> None:
    """Records the substitution, and why it was forced.

    The proposal named Llama-3.3-70B; Groq retired it from the free tier. Of the
    chat models the tier still offers, gpt-oss-120b is the largest that is not a
    Qwen model -- and "not Qwen" excluded qwen3.8-27b, which is on the same
    account and would otherwise have been a candidate. The judge-is-not-the-
    generator rule therefore cost a real option here, which is the point of
    having it checked rather than remembered.
    """
    active = judge_params({"base": _shipped()})
    assert active["model_id"] == "openai/gpt-oss-120b"
    assert "qwen" not in active["model_id"].lower()

    text = Path("configs/base.yaml").read_text(encoding="utf-8")
    assert "qwen3.8-27b" in text, "the excluded candidate is not recorded"
    assert "retired" in text, "the reason for the substitution is not recorded"


def test_provider_specific_request_fields_are_config_not_code() -> None:
    """gpt-oss models spend tokens on reasoning before answering, and those
    count against max_tokens. `reasoning_effort` is the lever if replies come
    back empty; it lives in config so the choice reaches the run id."""
    assert "extra_body" in _shipped()["judge"]["providers"]["groq"]


def test_both_backends_stay_configured_so_the_question_stays_answerable() -> None:
    """A reviewer may ask whether the result depends on the judge provider.
    Deleting the alternative makes that unanswerable after the fact."""
    providers = _shipped()["judge"]["providers"]
    assert {"groq", "openrouter"} <= set(providers)
    for block in providers.values():
        assert block["endpoint"].startswith("https://")
        assert block["api_key_env"].endswith("_API_KEY")


def test_the_backend_is_selected_from_config_not_from_a_flag() -> None:
    base = _shipped()
    assert base["judge"]["provider"] == "groq"
    active = judge_params({"base": base})
    assert active["model_id"] == "openai/gpt-oss-120b"
    assert active["endpoint"].startswith("https://api.groq.com/")
    assert active["api_key_env"] == "GROQ_API_KEY"

    switched = {**base, "judge": {**base["judge"], "provider": "openrouter"}}
    assert judge_params({"base": switched})["api_key_env"] == "OPENROUTER_API_KEY"


def test_selecting_a_provider_changes_the_run_id() -> None:
    """Two judges are two results, and they must not share a directory."""
    from ragbench.cache_keys import run_key

    base = _shipped()
    resolved = {"base": base, "corpus": {}, "factors": {}, "gold": {}, "schema_version": 1}
    switched = {**resolved, "base": {**base, "judge": {**base["judge"], "provider": "openrouter"}}}
    assert run_key(resolved) != run_key(switched)


def test_no_api_key_is_committed_anywhere_in_config() -> None:
    """The variable's NAME is documentation. Its value never touches the repo."""
    base = _shipped()
    names = {block["api_key_env"] for block in base["judge"]["providers"].values()}
    assert names == {"GROQ_API_KEY", "OPENROUTER_API_KEY"}
    text = Path("configs/base.yaml").read_text(encoding="utf-8")
    for prefix in ("sk-or-", "gsk_", "sk-"):
        assert prefix not in text


# ------------------------------------------------------------- the http client


class _Response:
    def __init__(self, status: int, payload: Any = None, headers: dict | None = None) -> None:
        self.status_code = status
        self.ok = 200 <= status < 300
        self.headers = headers or {}
        self._payload = payload
        self.text = json.dumps(payload) if payload is not None else ""

    def json(self) -> Any:
        return self._payload


class _Session:
    """Replays a queue of responses and records what it was sent."""

    def __init__(self, responses: list[_Response]) -> None:
        self._responses = list(responses)
        self.sent: list[dict] = []

    def post(self, url, headers=None, json=None, timeout=None):  # noqa: A002
        self.sent.append({"url": url, "headers": headers or {}, "body": json or {}})
        return self._responses.pop(0)


def _reply(text: str) -> _Response:
    return _Response(200, {"choices": [{"message": {"content": text}}]})


HOSTED: dict[str, Any] = {
    **JUDGE,
    "provider": "groq",
    "model_id": "openai/gpt-oss-120b",
    "endpoint": "https://api.groq.com/openai/v1/chat/completions",
    "requests_per_minute": 0,
    "tokens_per_minute": 0,
    "daily_token_cap": 0,
}


def _client(monkeypatch, responses: list[_Response], **overrides):
    from ragbench.judging import openai_compatible

    monkeypatch.setenv("RAGBENCH_TEST_KEY", "test-key")
    monkeypatch.setattr(openai_compatible.time, "sleep", lambda _: None)
    judge = openai_compatible.ChatCompletionsJudge({**HOSTED, **overrides})
    judge._session = _Session(responses)
    return judge


GOOD = '{"faithfulness": 5, "relevance": 4, "completeness": 3, "verdict": "correct", ' \
       '"rationale": "matches"}'


def test_a_missing_api_key_fails_before_any_request(monkeypatch) -> None:
    from ragbench.judging import openai_compatible

    monkeypatch.delenv("RAGBENCH_TEST_KEY", raising=False)
    with pytest.raises(JudgeError, match="is not set"):
        openai_compatible.ChatCompletionsJudge(HOSTED)


def test_the_request_goes_to_the_configured_endpoint(monkeypatch) -> None:
    """The one thing that differs between the two providers at the wire level."""
    judge = _client(monkeypatch, [_reply(GOOD)])
    judge.score(prompt())
    assert judge._session.sent[0]["url"] == HOSTED["endpoint"]


def test_provider_specific_headers_are_sent_only_where_configured(monkeypatch) -> None:
    plain = _client(monkeypatch, [_reply(GOOD)])
    plain.score(prompt())
    assert "HTTP-Referer" not in plain._session.sent[0]["headers"]

    attributed = _client(
        monkeypatch,
        [_reply(GOOD)],
        provider="openrouter",
        endpoint="https://openrouter.ai/api/v1/chat/completions",
        extra_headers={"HTTP-Referer": "https://github.com/ragbench", "X-Title": "ragbench"},
    )
    attributed.score(prompt())
    assert attributed._session.sent[0]["headers"]["X-Title"] == "ragbench"


def test_the_key_travels_in_the_header_and_not_in_the_body(monkeypatch) -> None:
    judge = _client(monkeypatch, [_reply(GOOD)])
    judge.score(prompt())
    sent = judge._session.sent[0]
    assert sent["headers"]["Authorization"] == "Bearer test-key"
    assert "test-key" not in json.dumps(sent["body"])


def test_a_rejected_key_is_not_retried(monkeypatch) -> None:
    """401 is not transient. Retrying it five times with backoff turns an
    instant, obvious failure into a slow, confusing one."""
    judge = _client(monkeypatch, [_Response(401, {"error": "no"})])
    with pytest.raises(JudgeError, match="401"):
        judge.score(prompt())
    assert len(judge._session.sent) == 1


def test_throttling_is_retried_and_retry_after_is_honoured(monkeypatch) -> None:
    from ragbench.judging import openai_compatible

    slept: list[float] = []
    monkeypatch.setenv("RAGBENCH_TEST_KEY", "k")
    monkeypatch.setattr(openai_compatible.time, "sleep", lambda s: slept.append(s))
    judge = openai_compatible.ChatCompletionsJudge(HOSTED)
    judge._session = _Session([_Response(429, headers={"retry-after": "7"}), _reply(GOOD)])
    assert judge.score(prompt()).verdict == "correct"
    assert 7.0 in slept


def test_a_provider_that_rejects_response_format_is_retried_without_it(monkeypatch) -> None:
    """Not every provider behind a slug accepts the parameter, and losing the
    whole run to a 400 over an optional field would be a poor trade."""
    judge = _client(monkeypatch, [_Response(400, {"error": "response_format"}), _reply(GOOD)])
    assert judge.score(prompt()).verdict == "correct"
    assert "response_format" in judge._session.sent[0]["body"]
    assert "response_format" not in judge._session.sent[1]["body"]


def test_a_fenced_reply_is_accepted(monkeypatch) -> None:
    """Models wrap JSON in fences often enough that spending the one retry on
    formatting rather than on judgement would be waste."""
    judge = _client(monkeypatch, [_reply(f"```json\n{GOOD}\n```")])
    assert judge.score(prompt()).verdict == "correct"


def test_a_bad_reply_is_retried_exactly_once_then_raises(monkeypatch) -> None:
    judge = _client(monkeypatch, [_reply("no JSON here"), _reply(GOOD)])
    result = judge.score(prompt())
    assert result.n_parse_retries == 1
    assert "JSON only." in judge._session.sent[1]["body"]["messages"][1]["content"]

    twice = _client(monkeypatch, [_reply("nope"), _reply("still nope")])
    with pytest.raises(ValueError):
        twice.score(prompt())


# -------------------------------------------------------------- the whole cell


def _query(identifier: str, note: str = "") -> Query:
    return Query(
        query_id=identifier,
        question=f"question {identifier}?",
        reference_answer="the hippocampus",
        gold=GoldSpan(
            pmcid="PMC1", char_start=0, char_end=60, section="Results",
            context_start=0, context_end=200,
        ),
        judge_note=note,
        verified=True,
    )


def _answer(identifier: str, text: str) -> dict[str, Any]:
    return GeneratedAnswer(
        query_id=identifier,
        answer=text,
        prompt_sha256="0" * 64,
        n_prompt_tokens=1500,
        n_completion_tokens=len(text.split()),
        latency_ms=1.0,
        context_chunk_ids=("PMC1-0000",),
        n_context_chunks=1,
    ).to_dict()


def _world(
    tmp_path: Path, answers: list[dict[str, Any]]
) -> tuple[dict[str, Any], Path, Path, Path]:
    configs, data, run = tmp_path / "configs", tmp_path / "data", tmp_path / "run"
    configs.mkdir(parents=True, exist_ok=True)
    queries = [_query("q001"), _query("q002", note="the source sentence is malformed")]
    write_gold_set(configs / "gold_set.jsonl", queries)
    resolved: dict[str, Any] = {
        "base": {
            "judge": dict(JUDGE),
            "generation": {"refusal_text": REFUSAL, "context_separator": "\n\n"},
            "chunking": {
                "target_tokens": 510, "overlap_tokens": 0, "tokenizer_id": "whitespace",
                "tokenizer_revision": "x", "min_chunk_tokens": 0,
                "separators": ["\n\n"], "chunk_abstract": False,
            },
        },
        "corpus": {"manifest_sha": "deadbeef"},
        "gold": {"gold_set_sha": gold_set_sha(queries)},
        "factors": {
            "chunking": {"fixed": {"strategy": "fixed"}},
            "embedding": {"bge": {}},
            "rerank": {"off": {}},
        },
    }
    from ragbench.cache_keys import chunk_set_key
    from ragbench.chunking.pipeline import arm_params as chunking_params
    from ragbench.config import chunk_set_dir

    directory = chunk_set_dir(chunk_set_key("deadbeef", chunking_params(resolved, "fixed")), data)
    directory.mkdir(parents=True, exist_ok=True)
    write_jsonl(directory / "chunks.jsonl", [Chunk(
        chunk_id="PMC1-0000", pmcid="PMC1", chunk_index=0,
        text="Amyloid plaques accumulate in the hippocampus.", n_tokens=6,
        char_start=0, char_end=45, sections=("Results",), content_sha256="0" * 64,
    ).to_dict()])

    (run / "retrieve").mkdir(parents=True, exist_ok=True)
    write_jsonl(run / "retrieve" / "fixed-bge-rerank_off.jsonl", [
        RetrievalResult(
            query_id=q["query_id"],
            selected=(ScoredChunk(chunk_id="PMC1-0000", score=1.0, rank=1, n_budget_tokens=10),),
            n_candidates=1, n_chunks=1, tokens_used=10, token_budget=2000,
            budget_slack=1990, stopped_reason="candidates_exhausted",
        ).to_dict() for q in answers
    ])
    write_jsonl(run / "generate" / "fixed-bge-rerank_off.jsonl", answers)
    return resolved, configs, data, run


class _CountingJudge:
    name = "counting"

    def __init__(self) -> None:
        self.seen: list[str] = []

    def score(self, prompt: Any) -> Verdict:
        self.seen.append(prompt.answer)
        return Verdict(
            verdict="correct",
            scores={"faithfulness": 5.0, "relevance": 4.0, "completeness": 4.0},
            rationale="ok",
        )


def test_an_abstention_is_classified_without_an_api_call(tmp_path: Path) -> None:
    """40 of 320 calls on the real run, and it removes a class of judge error
    from a question that has exactly one right answer."""
    resolved, configs, data, run = _world(
        tmp_path, [_answer("q001", "the hippocampus."), _answer("q002", REFUSAL)]
    )
    judge = _CountingJudge()
    report = judge_one_config(
        resolved, "fixed", "bge", "off", configs, data, run, judge=judge
    )
    assert judge.seen == ["the hippocampus."] * 2  # two passes, one answer
    assert report["api_calls"] == 2
    assert report["abstained"] == 2
    records = {(r.query_id, r.pass_index): r for r in load_judgements(
        judgements_path(run, "fixed", "bge", "off"))}
    assert records[("q002", 0)].verdict == ABSTAINED
    assert records[("q002", 0)].scores == {}
    assert records[("q002", 0)].from_refusal_match is True


def test_every_answer_is_scored_once_per_pass(tmp_path: Path) -> None:
    resolved, configs, data, run = _world(
        tmp_path, [_answer("q001", "a"), _answer("q002", "b")]
    )
    report = judge_one_config(
        resolved, "fixed", "bge", "off", configs, data, run, judge=_CountingJudge()
    )
    assert report["n_judgements"] == 4
    assert {r.pass_index for r in load_judgements(
        judgements_path(run, "fixed", "bge", "off"))} == {0, 1}


def test_rerunning_a_finished_cell_spends_nothing(tmp_path: Path) -> None:
    """The only metered stage. A re-run must never pay twice."""
    resolved, configs, data, run = _world(tmp_path, [_answer("q001", "a")])
    judge_one_config(resolved, "fixed", "bge", "off", configs, data, run, judge=_CountingJudge())
    judge = _CountingJudge()
    report = judge_one_config(
        resolved, "fixed", "bge", "off", configs, data, run, judge=judge
    )
    assert judge.seen == []
    assert report["api_calls"] == 0
    assert report["reused"] == 2


def test_an_interrupted_cell_resumes_at_the_call_it_stopped_on(tmp_path: Path) -> None:
    class _Dying(_CountingJudge):
        def score(self, prompt: Any) -> Verdict:
            if len(self.seen) >= 2:
                raise JudgeError("rate limited out of the session")
            return super().score(prompt)

    resolved, configs, data, run = _world(
        tmp_path, [_answer("q001", "a"), _answer("q002", "b")]
    )
    with pytest.raises(JudgeError):
        judge_one_config(resolved, "fixed", "bge", "off", configs, data, run, judge=_Dying())
    assert len(load_judgements(judgements_path(run, "fixed", "bge", "off"))) == 2

    judge = _CountingJudge()
    report = judge_one_config(
        resolved, "fixed", "bge", "off", configs, data, run, judge=judge
    )
    assert report["n_judgements"] == 4
    assert len(judge.seen) == 2


def test_judging_against_regenerated_answers_is_refused(tmp_path: Path) -> None:
    """The rubric lives in config and moves the run id when edited. What that
    cannot catch is `generate` re-run underneath a directory that already holds
    judgements."""
    resolved, configs, data, run = _world(tmp_path, [_answer("q001", "a")])
    judge_one_config(resolved, "fixed", "bge", "off", configs, data, run, judge=_CountingJudge())
    write_jsonl(run / "generate" / "fixed-bge-rerank_off.jsonl", [_answer("q001", "different")])
    with pytest.raises(ValueError, match="judged against a different answer"):
        judge_one_config(
            resolved, "fixed", "bge", "off", configs, data, run, judge=_CountingJudge()
        )


def test_an_unparseable_item_is_recorded_and_counted_not_dropped(tmp_path: Path) -> None:
    """Dropping it would shrink the configuration's denominator without saying so."""
    class _Garbling(_CountingJudge):
        def score(self, prompt: Any) -> Verdict:
            raise ValueError("verdict 'splendid' is not one of correct, ...")

    resolved, configs, data, run = _world(tmp_path, [_answer("q001", "a")])
    report = judge_one_config(
        resolved, "fixed", "bge", "off", configs, data, run, judge=_Garbling()
    )
    assert report["unparsed"] == 2
    assert all(r.verdict == UNPARSED for r in load_judgements(
        judgements_path(run, "fixed", "bge", "off")))


def test_the_judge_note_reaches_the_prompt_for_the_record_that_carries_one(
    tmp_path: Path,
) -> None:
    class _Capturing(_CountingJudge):
        def __init__(self) -> None:
            super().__init__()
            self.prompts: list[str] = []

        def score(self, prompt: Any) -> Verdict:
            self.prompts.append(prompt.user)
            return super().score(prompt)

    resolved, configs, data, run = _world(
        tmp_path, [_answer("q001", "a"), _answer("q002", "b")]
    )
    judge = _Capturing()
    judge_one_config(resolved, "fixed", "bge", "off", configs, data, run, judge=judge)
    with_note = [p for p in judge.prompts if "SPECIAL INSTRUCTION" in p]
    assert len(with_note) == 2  # q002, both passes
    assert "the source sentence is malformed" in with_note[0]


def test_judging_before_generating_says_so(tmp_path: Path) -> None:
    resolved, configs, data, run = _world(tmp_path, [_answer("q001", "a")])
    (run / "generate" / "fixed-bge-rerank_off.jsonl").unlink()
    with pytest.raises(ValueError, match="run `ragbench generate` first"):
        judge_one_config(
            resolved, "fixed", "bge", "off", configs, data, run, judge=_CountingJudge()
        )


def test_judging_is_not_a_factor() -> None:
    import ragbench.judging.base as module

    assert not hasattr(module, "arm_params")
    assert judge_params({"base": {"judge": dict(JUDGE)}}) == JUDGE


# --------------------------------------------------- pacing, and the daily cap


def test_the_pacer_waits_on_tokens_not_just_requests() -> None:
    """The binding constraint on a free tier. One judgement carries the
    retrieved context, so a call is ~3,250 tokens: at 12,000 tokens/minute that
    is under four calls a minute, far below the 30 requests/minute the same tier
    allows. Pacing on requests alone would collect 429s all day."""
    from ragbench.judging.openai_compatible import Pacer

    pacer = Pacer(requests_per_minute=30, tokens_per_minute=12000)
    now = 1000.0
    # 12,000 / 3,250 is 3.7, so exactly three calls fit in a minute -- an order
    # of magnitude under the 30 requests the same tier would allow.
    for _ in range(2):
        pacer._events.append((now, 3250))
    assert pacer._wait_for(now, 3250) == 0.0
    pacer._events.append((now, 3250))
    assert pacer._wait_for(now, 3250) == 60.0


def test_request_pacing_still_applies_when_tokens_are_unlimited() -> None:
    from ragbench.judging.openai_compatible import Pacer

    pacer = Pacer(requests_per_minute=2, tokens_per_minute=0)
    now = 500.0
    pacer._events.extend([(now, 10), (now, 10)])
    assert pacer._wait_for(now, 10) > 0


def test_an_unpaced_provider_never_waits() -> None:
    from ragbench.judging.openai_compatible import Pacer

    pacer = Pacer(requests_per_minute=0, tokens_per_minute=0)
    pacer._events.extend([(0.0, 99999)] * 50)
    assert pacer._wait_for(0.0, 99999) == 0.0


def test_the_estimate_is_replaced_by_what_the_call_actually_cost() -> None:
    """A systematically wrong estimate must not compound into a breach."""
    from ragbench.judging.openai_compatible import Pacer

    pacer = Pacer(30, 12000)
    pacer.before(1000)
    pacer.correct(4000)
    assert pacer._events[-1][1] == 4000


def test_the_daily_cap_stops_before_spending_rather_than_after(monkeypatch) -> None:
    """A full run is ~910,000 tokens and a free day is far less, so the stage
    has to survive being stopped. It stops before the call, so the cap is never
    exceeded rather than merely detected."""
    judge = _client(monkeypatch, [_reply(GOOD)], daily_token_cap=100)
    with pytest.raises(JudgeQuotaExhausted, match="daily token cap"):
        judge.score(prompt())
    assert judge._session.sent == []


def test_a_daily_429_is_not_retried_as_though_it_were_throttling(monkeypatch) -> None:
    """Waiting a minute does not clear a spent day; retrying just burns the
    remaining attempts against a wall."""
    judge = _client(
        monkeypatch,
        [_Response(429, {"error": {"message": "rate limit reached for tokens per day (TPD)"}})],
    )
    with pytest.raises(JudgeQuotaExhausted, match="daily allowance"):
        judge.score(prompt())
    assert len(judge._session.sent) == 1


def test_the_server_s_own_remaining_allowance_is_recorded(monkeypatch) -> None:
    """Published limits move; the response headers are the authoritative
    statement of what is actually in force."""
    judge = _client(
        monkeypatch,
        [_Response(
            200,
            {"choices": [{"message": {"content": GOOD}}], "usage": {"total_tokens": 2900}},
            headers={"x-ratelimit-remaining-tokens": "8400",
                     "x-ratelimit-limit-tokens": "12000"},
        )],
    )
    judge.score(prompt())
    assert judge.remaining["x-ratelimit-remaining-tokens"] == "8400"
    assert judge.tokens_spent == 2900


def test_a_quota_stop_keeps_what_was_written_and_says_so(tmp_path: Path) -> None:
    """Resumption is the whole point: the run spans days, so stopping must be a
    pause rather than a loss."""
    class _Exhausting(_CountingJudge):
        def score(self, prompt: Any) -> Verdict:
            if len(self.seen) >= 2:
                raise JudgeQuotaExhausted("the configured daily token cap would be exceeded")
            return super().score(prompt)

    resolved, configs, data, run = _world(
        tmp_path, [_answer("q001", "a"), _answer("q002", "b")]
    )
    report = judge_one_config(
        resolved, "fixed", "bge", "off", configs, data, run, judge=_Exhausting()
    )
    assert report["quota_exhausted"] is True
    assert report["n_judgements"] == 2
    assert report["outstanding"] == 2
    assert "daily token cap" in report["quota_message"]

    # Tomorrow: the same command continues rather than restarting.
    resumed = _CountingJudge()
    again = judge_one_config(
        resolved, "fixed", "bge", "off", configs, data, run, judge=resumed
    )
    assert again["quota_exhausted"] is False
    assert again["n_judgements"] == 4
    assert again["reused"] == 2
    assert len(resumed.seen) == 2


def test_extra_body_reaches_the_request_untouched(monkeypatch) -> None:
    judge = _client(monkeypatch, [_reply(GOOD)], extra_body={"reasoning_effort": "low"})
    judge.score(prompt())
    assert judge._session.sent[0]["body"]["reasoning_effort"] == "low"


def test_an_empty_extra_body_adds_nothing(monkeypatch) -> None:
    judge = _client(monkeypatch, [_reply(GOOD)], extra_body={})
    judge.score(prompt())
    body = judge._session.sent[0]["body"]
    assert set(body) == {"model", "messages", "temperature", "max_tokens", "seed",
                         "response_format"}


def test_a_provider_without_a_block_still_names_itself() -> None:
    """`stand-in` has no provider block, so nothing merges a model_id in. Left
    blank, the report printed an empty judge and -- worse -- the CPU STAND-IN
    banner never fired, because it keys on that name. That banner is the only
    thing between a lexical-overlap table and a thesis."""
    params = judge_params({"base": {"judge": {"provider": "stand-in", "providers": {}}}})
    assert params["model_id"] == "stand-in"


# ------------------------------------------------------- retrying the failures


def test_clear_unparsed_removes_only_the_failures(tmp_path: Path) -> None:
    from ragbench.judging.pipeline import clear_unparsed

    path = tmp_path / "cell.jsonl"
    write_jsonl(path, [
        Judgement(query_id="q001", scores={"faithfulness": 5.0}, rationale="", judge_model="j",
                  rubric_id="v1", verdict="correct", pass_index=0).to_dict(),
        Judgement(query_id="q002", scores={}, rationale="bad json", judge_model="j",
                  rubric_id="v1", verdict=UNPARSED, pass_index=0).to_dict(),
        Judgement(query_id="q003", scores={}, rationale="", judge_model="refusal-match",
                  rubric_id="v1", verdict=ABSTAINED, pass_index=0).to_dict(),
    ])
    assert clear_unparsed(path) == 1
    kept = {r.query_id: r.verdict for r in load_judgements(path)}
    assert kept == {"q001": "correct", "q003": ABSTAINED}


def test_clearing_nothing_leaves_the_file_untouched(tmp_path: Path) -> None:
    from ragbench.judging.pipeline import clear_unparsed

    path = tmp_path / "cell.jsonl"
    write_jsonl(path, [
        Judgement(query_id="q001", scores={"faithfulness": 5.0}, rationale="", judge_model="j",
                  rubric_id="v1", verdict="correct", pass_index=0).to_dict(),
    ])
    before = path.read_bytes()
    assert clear_unparsed(path) == 0
    assert path.read_bytes() == before


def test_retry_unparsed_rejudges_the_failures_and_nothing_else(tmp_path: Path) -> None:
    """A judgement that failed because a setting was wrong must not survive the
    fix to that setting: the configuration would be scored under two regimes
    with nothing to say which item came from which."""
    class _Failing(_CountingJudge):
        def score(self, prompt: Any) -> Verdict:
            self.seen.append(prompt.answer)
            raise ValueError("verdict '' is not one of correct, ...")

    resolved, configs, data, run = _world(
        tmp_path, [_answer("q001", "a"), _answer("q002", "b")]
    )
    broken = judge_one_config(
        resolved, "fixed", "bge", "off", configs, data, run, judge=_Failing()
    )
    assert broken["unparsed"] == 4

    # Without the flag, the failures are permanent and cost nothing more.
    idle = _CountingJudge()
    assert judge_one_config(
        resolved, "fixed", "bge", "off", configs, data, run, judge=idle
    )["api_calls"] == 0
    assert idle.seen == []

    fixed = _CountingJudge()
    report = judge_one_config(
        resolved, "fixed", "bge", "off", configs, data, run,
        judge=fixed, retry_unparsed=True,
    )
    assert report["unparsed_cleared"] == 4
    assert report["unparsed"] == 0
    assert report["n_judgements"] == 4
    assert len(fixed.seen) == 4


def test_retry_unparsed_keeps_the_judgements_that_worked(tmp_path: Path) -> None:
    """Re-judging everything would spend the allowance twice over."""
    class _HalfFailing(_CountingJudge):
        def score(self, prompt: Any) -> Verdict:
            self.seen.append(prompt.answer)
            if prompt.answer == "b":
                raise ValueError("not the schema")
            return Verdict(verdict="correct", scores={s: 5.0 for s in
                           ("faithfulness", "relevance", "completeness")})

    resolved, configs, data, run = _world(
        tmp_path, [_answer("q001", "a"), _answer("q002", "b")]
    )
    judge_one_config(resolved, "fixed", "bge", "off", configs, data, run, judge=_HalfFailing())

    retried = _CountingJudge()
    report = judge_one_config(
        resolved, "fixed", "bge", "off", configs, data, run,
        judge=retried, retry_unparsed=True,
    )
    assert report["unparsed_cleared"] == 2
    assert report["reused"] == 2          # q001's two passes were kept
    assert retried.seen == ["b", "b"]     # only q002 was scored again


def test_a_judgement_records_what_it_cost(tmp_path: Path) -> None:
    """The first real run had its per-call cost reconstructed from an aggregate.
    The daily cap is spent in these units, so they are recorded per item."""
    class _Metered(_CountingJudge):
        tokens_spent = 0

        def score(self, prompt: Any) -> Verdict:
            type(self).tokens_spent += 2900
            return super().score(prompt)

    resolved, configs, data, run = _world(tmp_path, [_answer("q001", "a")])
    report = judge_one_config(
        resolved, "fixed", "bge", "off", configs, data, run, judge=_Metered()
    )
    assert report["tokens_session"] == 5800
    assert report["tokens_total"] == 5800
    assert all(r.n_tokens == 2900 for r in load_judgements(
        judgements_path(run, "fixed", "bge", "off")))


def test_a_resumed_session_reports_its_own_spend_not_the_cumulative_one(
    tmp_path: Path,
) -> None:
    """The bug this separation exists to prevent.

    Summing every record in the file -- including judgements reused from
    earlier sessions -- and dividing by THIS session's call count reported a
    2,747-token judgement as 8,250. Session and cumulative are different
    numerators and must not share a denominator.
    """
    class _Metered(_CountingJudge):
        tokens_spent = 0

        def score(self, prompt: Any) -> Verdict:
            type(self).tokens_spent += 1000
            return super().score(prompt)

    resolved, configs, data, run = _world(
        tmp_path, [_answer("q001", "a"), _answer("q002", "b")]
    )
    # First session: q001 only, by judging with a gold set of one question.
    first = judge_one_config(
        resolved, "fixed", "bge", "off", configs, data, run, judge=_Metered()
    )
    assert first["tokens_session"] == first["tokens_total"] == 4000

    # Second session: everything is already judged, so it spends nothing --
    # but the file still holds 4,000 tokens' worth of records.
    second = judge_one_config(
        resolved, "fixed", "bge", "off", configs, data, run, judge=_CountingJudge()
    )
    assert second["api_calls"] == 0
    assert second["tokens_session"] == 0
    assert second["tokens_total"] == 4000
