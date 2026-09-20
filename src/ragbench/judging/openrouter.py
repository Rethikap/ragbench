"""The hosted judge. The only module here that opens a socket.

Three things about a throttled free tier shape this file:

* **Pace to the documented limit rather than discovering it through 429s.** A
  429 costs the request *and* the backoff; spacing requests costs only the
  spacing. 320 calls at 20/min is about sixteen minutes either way, and one of
  those ways finishes.
* **Honour ``Retry-After``.** When a 429 arrives anyway the server has said how
  long to wait, and exponential backoff that ignores it either sleeps too little
  and 429s again or sleeps far too long.
* **Do not retry a 401.** A missing or wrong key is not transient. Retrying it
  five times with backoff turns an instant, obvious failure into a slow,
  confusing one.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Mapping
from typing import Any

from .base import JudgeError, Verdict, parse_verdict
from .prompt import JudgePrompt

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
#: Status codes worth trying again: throttling, and the provider's own wobbles.
TRANSIENT = frozenset({408, 409, 429, 500, 502, 503, 504})


def extract_json(text: str) -> dict[str, Any]:
    """Pull the JSON object out of a reply, tolerating a markdown fence.

    Tolerant about packaging, strict about content: the object still has to
    validate against the rubric in :func:`~ragbench.judging.base.parse_verdict`.
    Models wrap JSON in ```json fences often enough that refusing one would
    spend a retry on formatting rather than on judgement, but anything past the
    braces is not repaired -- it is retried once and then counted.
    """
    body = text.strip()
    if body.startswith("```"):
        body = body.split("\n", 1)[-1] if "\n" in body else body
        body = body.rsplit("```", 1)[0]
    start, end = body.find("{"), body.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object in the reply")
    return json.loads(body[start : end + 1])


class OpenRouterJudge:
    """`meta-llama/llama-3.3-70b-instruct` by default, pinned by its full slug."""

    def __init__(self, params: Mapping[str, Any], timeout: float = 120.0) -> None:
        import requests

        self._requests = requests
        self._params = dict(params)
        self.model_id = str(params["model_id"])
        self.name = f"openrouter:{self.model_id}"
        self.max_retries = int(params.get("max_retries", 5))
        self.timeout = timeout

        variable = str(params.get("api_key_env") or "OPENROUTER_API_KEY")
        self._key = os.environ.get(variable, "").strip()
        if not self._key:
            raise JudgeError(
                f"{variable} is not set. The judge's API key comes from the environment "
                "and is never read from the repository or from a config file. Export it "
                "in the shell (or add it as a Kaggle secret) and run again."
            )
        rpm = float(params.get("requests_per_minute", 20) or 20)
        self._min_interval = 60.0 / rpm if rpm > 0 else 0.0
        self._last_request = 0.0
        self._session = requests.Session()
        self._send_response_format = bool(params.get("require_json_object", True))

    # ------------------------------------------------------------------ http

    def _pace(self) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request = time.monotonic()

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

    def _post(self, system: str, user: str) -> str:
        """One graded call, with pacing, backoff and a fast fail on a bad key."""
        last: Exception | None = None
        for attempt in range(self.max_retries):
            self._pace()
            try:
                response = self._session.post(
                    ENDPOINT,
                    headers={
                        "Authorization": f"Bearer {self._key}",
                        "Content-Type": "application/json",
                        # OpenRouter attributes traffic with these; neither is
                        # a credential and both are safe to commit.
                        "HTTP-Referer": "https://github.com/ragbench",
                        "X-Title": "ragbench",
                    },
                    json=self._payload(system, user),
                    timeout=self.timeout,
                )
            except self._requests.RequestException as exc:  # pragma: no cover - network
                last = exc
                time.sleep(min(2**attempt, 30))
                continue

            if response.status_code == 401:
                raise JudgeError(
                    "OpenRouter rejected the API key (401). This is not retried, because "
                    "it is not transient -- check the value of the variable named by "
                    "judge.api_key_env."
                )
            if response.status_code == 400 and self._send_response_format:
                # Not every provider behind a slug accepts response_format. Drop
                # it once and carry on; the prompt states the schema anyway.
                self._send_response_format = False
                last = JudgeError(f"400 from OpenRouter: {response.text[:300]}")
                continue
            if response.status_code in TRANSIENT:
                self._sleep_after(response, attempt)
                last = JudgeError(f"{response.status_code} from OpenRouter")
                continue
            if not response.ok:
                raise JudgeError(f"{response.status_code} from OpenRouter: {response.text[:300]}")

            try:
                return str(response.json()["choices"][0]["message"]["content"])
            except (KeyError, IndexError, ValueError, TypeError) as exc:
                last = JudgeError(f"unexpected response shape: {response.text[:300]}")
                last.__cause__ = exc
                time.sleep(min(2**attempt, 30))

        raise JudgeError(
            f"giving up on the judge after {self.max_retries} attempts: {last}"
        ) from last

    def _sleep_after(self, response: Any, attempt: int) -> None:
        """Wait as long as the server asked, or back off if it did not say."""
        header = response.headers.get("Retry-After", "") if response.headers else ""
        try:
            delay = float(header)
        except (TypeError, ValueError):
            delay = float(min(2**attempt, 60))
        time.sleep(max(0.0, min(delay, 120.0)))

    # ----------------------------------------------------------------- judge

    def score(self, prompt: JudgePrompt) -> Verdict:
        """Grade once, with a single corrective retry if the reply is not the schema."""
        retries = 0
        reminder = str(self._params.get("retry_instruction") or "")
        user = prompt.user
        message = user
        while True:
            reply = self._post(prompt.system, message)
            try:
                parsed = parse_verdict(extract_json(reply), self._params)
            except (ValueError, json.JSONDecodeError):
                if retries:
                    raise
                retries = 1
                message = f"{user}\n\n{reminder}" if reminder else user
                continue
            return Verdict(
                verdict=parsed.verdict,
                scores=parsed.scores,
                rationale=parsed.rationale,
                n_parse_retries=retries,
            )
