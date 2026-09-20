"""Hosted judges behind one OpenAI-compatible client.

Two providers, selected from config, because a reviewer may reasonably ask
whether a result depends on which judge produced it. Keeping both answerable
costs one registry entry; deleting one makes the question unanswerable after the
fact.

| provider | model | free tier |
|---|---|---|
| `groq` | `llama-3.3-70b-versatile` | no card required; request **and token** limits |
| `openrouter` | `meta-llama/llama-3.3-70b-instruct` | now requires a credit balance |

Both speak `/chat/completions` with the same request and response shape, so what
differs is an endpoint, a key, some headers and the limits. That is data, not
code, and it lives in `judge.providers` in config.

**Tokens are the binding constraint, not requests.** One judgement carries the
retrieved context -- it must, or faithfulness cannot be assessed -- which makes
it roughly 3,250 tokens. At a free tier's 12,000 tokens/minute that is under
four calls a minute, far below the 30 requests/minute the same tier allows. A
client pacing only on requests would spend its day collecting 429s. So this one
paces on both, and stops cleanly against a daily token cap rather than
discovering it as an error.
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections import deque
from collections.abc import Mapping
from typing import Any

from .base import JudgeError, JudgeQuotaExhausted, Verdict, parse_verdict
from .prompt import JudgePrompt

logger = logging.getLogger(__name__)

#: Everything provider-specific that is not already in config. Endpoints and
#: limits live in `judge.providers`; this is only the shape of what is known.
PROVIDERS: tuple[str, ...] = ("groq", "openrouter")

#: Status codes worth trying again: throttling, and the provider's own wobbles.
TRANSIENT = frozenset({408, 409, 429, 500, 502, 503, 504})

#: Rough tokens-per-character. Used only to pace *before* a reply arrives; the
#: actual count from the response replaces it immediately afterwards.
CHARS_PER_TOKEN = 4


def extract_json(text: str) -> dict[str, Any]:
    """Pull the JSON object out of a reply, tolerating a markdown fence.

    Tolerant about packaging, strict about content: the object still has to
    validate against the rubric in :func:`~ragbench.judging.base.parse_verdict`.
    Models wrap JSON in ```json fences often enough that refusing one would
    spend the single retry on formatting rather than on judgement.
    """
    body = text.strip()
    if body.startswith("```"):
        body = body.split("\n", 1)[-1] if "\n" in body else body
        body = body.rsplit("```", 1)[0]
    start, end = body.find("{"), body.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object in the reply")
    return json.loads(body[start : end + 1])


class Pacer:
    """Spends requests and tokens no faster than the tier allows.

    A rolling 60-second window over both, because the limits are per minute and
    a fixed sleep between calls either wastes the allowance or overruns it. The
    token window is the one that usually binds.
    """

    def __init__(self, requests_per_minute: float, tokens_per_minute: float) -> None:
        self.requests_per_minute = max(0.0, requests_per_minute)
        self.tokens_per_minute = max(0.0, tokens_per_minute)
        self._events: deque[tuple[float, int]] = deque()

    def _prune(self, now: float) -> None:
        while self._events and now - self._events[0][0] >= 60.0:
            self._events.popleft()

    def _wait_for(self, now: float, estimated: int) -> float:
        """Seconds to wait before a call of this size fits both windows."""
        self._prune(now)
        delay = 0.0
        if self.requests_per_minute and len(self._events) >= self.requests_per_minute:
            delay = max(delay, 60.0 - (now - self._events[0][0]))
        if self.tokens_per_minute:
            spent = sum(tokens for _, tokens in self._events)
            # Walk the window forward until the estimated call fits.
            for moment, tokens in self._events:
                if spent + estimated <= self.tokens_per_minute:
                    break
                spent -= tokens
                delay = max(delay, 60.0 - (now - moment))
        return max(0.0, delay)

    def before(self, estimated_tokens: int) -> None:
        delay = self._wait_for(time.monotonic(), estimated_tokens)
        if delay > 0:
            time.sleep(delay)
        self._events.append((time.monotonic(), estimated_tokens))

    def correct(self, actual: int) -> None:
        """Replace the estimate with what the response actually cost.

        The estimate paces the call that is about to go out; the true figure
        paces every call after it, so a systematically wrong estimate cannot
        compound into a rate-limit breach.
        """
        if self._events and actual > 0:
            moment, _ = self._events[-1]
            self._events[-1] = (moment, actual)


class ChatCompletionsJudge:
    """One client for both providers. Everything that differs is config."""

    def __init__(self, params: Mapping[str, Any], timeout: float = 120.0) -> None:
        import requests

        self._requests = requests
        self._params = dict(params)
        self.provider = str(params.get("provider", ""))
        if self.provider not in PROVIDERS:
            raise JudgeError(
                f"unknown judge provider {self.provider!r}; known: {', '.join(PROVIDERS)}"
            )
        self.model_id = str(params["model_id"])
        self.endpoint = str(params["endpoint"])
        self.name = f"{self.provider}:{self.model_id}"
        self.max_retries = int(params.get("max_retries", 5))
        self.timeout = timeout

        variable = str(params.get("api_key_env") or "")
        self._key = os.environ.get(variable, "").strip()
        if not self._key:
            raise JudgeError(
                f"{variable} is not set. The judge's API key comes from the environment "
                "and is never read from the repository or from a config file. Export it "
                "in the shell (or add it as a notebook secret) and run again."
            )
        self._session = requests.Session()
        self._headers = {str(k): str(v) for k, v in (params.get("extra_headers") or {}).items()}
        self._pacer = Pacer(
            float(params.get("requests_per_minute", 0) or 0),
            float(params.get("tokens_per_minute", 0) or 0),
        )
        self.daily_token_cap = int(params.get("daily_token_cap", 0) or 0)
        self.tokens_spent = 0
        self.calls = 0
        self._send_response_format = bool(params.get("require_json_object", True))
        #: What the server last said was left. Reported rather than guessed at:
        #: the documented limits move, and the headers are authoritative.
        self.remaining: dict[str, str] = {}

    # ------------------------------------------------------------------ http

    def _payload(self, system: str, user: str) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": float(self._params.get("temperature", 0.0)),
            "max_tokens": int(self._params.get("max_tokens", 400)),
        }
        if self._params.get("seed") is not None:
            body["seed"] = int(self._params["seed"])
        if self._send_response_format:
            body["response_format"] = {"type": "json_object"}
        return body

    def _estimate(self, system: str, user: str) -> int:
        return (len(system) + len(user)) // CHARS_PER_TOKEN + int(
            self._params.get("max_tokens", 400)
        )

    def _check_budget(self, estimated: int) -> None:
        if self.daily_token_cap and self.tokens_spent + estimated > self.daily_token_cap:
            raise JudgeQuotaExhausted(
                f"the configured daily token cap ({self.daily_token_cap:,}) would be "
                f"exceeded: {self.tokens_spent:,} already spent this session and the next "
                f"call needs about {estimated:,}. Judgements written so far are kept; "
                "re-run the same command once the allowance resets and it continues."
            )

    def _post(self, system: str, user: str) -> str:
        """One graded call: paced, retried on transient failures, fast-failing on a bad key."""
        estimated = self._estimate(system, user)
        self._check_budget(estimated)
        last: Exception | None = None
        for attempt in range(self.max_retries):
            self._pacer.before(estimated)
            try:
                response = self._session.post(
                    self.endpoint,
                    headers={
                        "Authorization": f"Bearer {self._key}",
                        "Content-Type": "application/json",
                        **self._headers,
                    },
                    json=self._payload(system, user),
                    timeout=self.timeout,
                )
            except self._requests.RequestException as exc:  # pragma: no cover - network
                last = exc
                time.sleep(min(2**attempt, 30))
                continue

            self._note_limits(response)
            if response.status_code == 401:
                raise JudgeError(
                    f"{self.provider} rejected the API key (401). This is not retried, "
                    "because it is not transient -- check the value of the variable named "
                    "by the provider's api_key_env."
                )
            if response.status_code == 400 and self._send_response_format:
                # Not every provider accepts response_format; the prompt states
                # the schema regardless.
                self._send_response_format = False
                last = JudgeError(f"400 from {self.provider}: {response.text[:300]}")
                continue
            if response.status_code == 429 and self._daily_exhausted(response):
                raise JudgeQuotaExhausted(
                    f"{self.provider} reports the daily allowance is spent: "
                    f"{response.text[:200]}. Judgements written so far are kept; re-run "
                    "the same command once it resets and it continues."
                )
            if response.status_code in TRANSIENT:
                self._sleep_after(response, attempt)
                last = JudgeError(f"{response.status_code} from {self.provider}")
                continue
            if not response.ok:
                raise JudgeError(
                    f"{response.status_code} from {self.provider}: {response.text[:300]}"
                )

            try:
                body = response.json()
                content = str(body["choices"][0]["message"]["content"])
            except (KeyError, IndexError, ValueError, TypeError) as exc:
                last = JudgeError(f"unexpected response shape: {response.text[:300]}")
                last.__cause__ = exc
                time.sleep(min(2**attempt, 30))
                continue

            actual = int((body.get("usage") or {}).get("total_tokens") or 0)
            self._pacer.correct(actual)
            self.tokens_spent += actual or estimated
            self.calls += 1
            return content

        raise JudgeError(f"giving up after {self.max_retries} attempts: {last}") from last

    def _note_limits(self, response: Any) -> None:
        """Record what the server says is left, rather than trusting a doc page.

        Published limits move, and the response headers are the only
        authoritative statement of the allowance actually in force.
        """
        headers = getattr(response, "headers", None) or {}
        for key in (
            "x-ratelimit-remaining-requests",
            "x-ratelimit-remaining-tokens",
            "x-ratelimit-limit-tokens",
            "x-ratelimit-reset-tokens",
        ):
            value = headers.get(key)
            if value is not None:
                self.remaining[key] = str(value)

    def _daily_exhausted(self, response: Any) -> bool:
        """A 429 that will not clear by waiting a minute."""
        text = (getattr(response, "text", "") or "").lower()
        if "per day" in text or "daily" in text or "tpd" in text or "rpd" in text:
            return True
        headers = getattr(response, "headers", None) or {}
        return str(headers.get("x-ratelimit-remaining-requests", "")).strip() == "0"

    def _sleep_after(self, response: Any, attempt: int) -> None:
        """Wait as long as the server asked, or back off if it did not say."""
        headers = getattr(response, "headers", None) or {}
        try:
            delay = float(headers.get("retry-after") or headers.get("Retry-After") or "")
        except (TypeError, ValueError):
            delay = float(min(2**attempt, 60))
        time.sleep(max(0.0, min(delay, 120.0)))

    # ----------------------------------------------------------------- judge

    def score(self, prompt: JudgePrompt) -> Verdict:
        """Grade once, with a single corrective retry if the reply is not the schema."""
        retries = 0
        reminder = str(self._params.get("retry_instruction") or "")
        message = prompt.user
        while True:
            reply = self._post(prompt.system, message)
            try:
                parsed = parse_verdict(extract_json(reply), self._params)
            except (ValueError, json.JSONDecodeError):
                if retries:
                    raise
                retries = 1
                message = f"{prompt.user}\n\n{reminder}" if reminder else prompt.user
                continue
            return Verdict(
                verdict=parsed.verdict,
                scores=parsed.scores,
                rationale=parsed.rationale,
                n_parse_retries=retries,
            )
