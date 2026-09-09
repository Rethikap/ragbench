"""NCBI E-utilities client -- the only place in the project that opens a socket.

Two facts about esearch shape this module:

* ``retstart`` cannot exceed 9998. NCBI simply refuses to return record 10,000 of
  a result set, so a 40k-hit query cannot be paged. The corpus query is therefore
  split into per-year windows, each comfortably under the cap, and the union is
  exact: the seven windows sum to the whole-range count.
* Result *order* is not stable across time. Nothing here depends on it; callers
  sort by PMCID before doing anything with the ids.
"""

from __future__ import annotations

import os
import time
from typing import Any

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
ARTICLE_URL = "https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"

#: NCBI rejects retstart > 9998, so no window may contain more hits than this.
ESEARCH_CAP = 9998


class NcbiError(Exception):
    """A request failed, or a result set was too large to enumerate."""


class NcbiClient:
    """Rate-limited E-utilities client.

    NCBI permits 3 requests/second anonymously and 10 with an API key; both
    credentials come from the environment (``NCBI_EMAIL``, ``NCBI_API_KEY``) so
    that nothing personal is committed and Kaggle/Colab secrets work unchanged.
    """

    def __init__(self, tool: str = "ragbench", timeout: float = 60.0) -> None:
        self.tool = tool
        self.email = os.environ.get("NCBI_EMAIL") or None
        self.api_key = os.environ.get("NCBI_API_KEY") or None
        self.timeout = timeout
        self._min_interval = 0.11 if self.api_key else 0.34
        self._last_request = 0.0
        self._session = requests.Session()

    # ------------------------------------------------------------------ http

    def _wait(self) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request = time.monotonic()

    @retry(
        retry=retry_if_exception_type(requests.RequestException),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def _get(self, endpoint: str, params: dict[str, str]) -> requests.Response:
        self._wait()
        query = {**params, "tool": self.tool}
        if self.email:
            query["email"] = self.email
        if self.api_key:
            query["api_key"] = self.api_key
        response = self._session.get(EUTILS + endpoint, params=query, timeout=self.timeout)
        response.raise_for_status()
        return response

    # --------------------------------------------------------------- esearch

    def _esearch(self, term: str, mindate: str, maxdate: str, **extra: str) -> dict[str, Any]:
        response = self._get(
            "esearch.fcgi",
            {
                "db": "pmc",
                "term": term,
                "datetype": "pdat",
                "mindate": mindate,
                "maxdate": maxdate,
                "retmode": "json",
                **extra,
            },
        )
        try:
            result: dict[str, Any] = response.json()["esearchresult"]
        except ValueError as exc:
            raise NcbiError(f"esearch returned unparseable JSON: {response.text[:200]}") from exc
        if "ERROR" in result:
            raise NcbiError(f"esearch failed for {mindate}..{maxdate}: {result['ERROR']}")
        return result

    def count(self, term: str, mindate: str, maxdate: str) -> int:
        return int(self._esearch(term, mindate, maxdate, retmax="0")["count"])

    def search_window(self, term: str, mindate: str, maxdate: str) -> list[str]:
        """Every id in one date window, or an error if the window is too large."""
        total = self.count(term, mindate, maxdate)
        if total > ESEARCH_CAP:
            raise NcbiError(
                f"window {mindate}..{maxdate} has {total} hits, above the {ESEARCH_CAP} "
                "esearch cap; narrow the window before enumerating it"
            )
        if total == 0:
            return []
        result = self._esearch(term, mindate, maxdate, retmax=str(ESEARCH_CAP), retstart="0")
        return list(result["idlist"])

    def search_by_year(self, term: str, date_from: str, date_to: str) -> dict[int, list[str]]:
        """Enumerate a multi-year query as one window per calendar year.

        Returns ids per year so the caller can verify the partition against the
        whole-range count rather than trusting it.
        """
        first, last = int(date_from[:4]), int(date_to[:4])
        found: dict[int, list[str]] = {}
        for year in range(first, last + 1):
            mindate = date_from if year == first else f"{year}/01/01"
            maxdate = date_to if year == last else f"{year}/12/31"
            found[year] = self.search_window(term, mindate, maxdate)
        return found

    # ---------------------------------------------------------------- efetch

    def fetch_article(self, pmcid: str) -> bytes:
        """Raw JATS for one PMCID, fetched singly.

        One article per request rather than batched: the bytes cached on disk are
        then exactly the bytes NCBI returned for that PMCID, which is what
        ``ParsedPaper.source_sha256`` attests to.
        """
        digits = pmcid.removeprefix("PMC")
        response = self._get("efetch.fcgi", {"db": "pmc", "id": digits, "retmode": "xml"})
        return response.content


def article_url(pmcid: str) -> str:
    return ARTICLE_URL.format(pmcid=pmcid)
