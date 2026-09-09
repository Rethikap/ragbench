"""Corpus selection (runs once, then never again).

Determinism is the whole point, and it is threatened from two directions:

* NCBI result *order* is not stable, so it must never decide anything. Every id
  set is sorted by numeric PMCID before use.
* NCBI result *completeness* is capped: esearch refuses ``retstart`` past 9998,
  so a 40k-hit query cannot be paged. Enumeration is therefore split into
  per-year windows and the partition is verified against the whole-range count.

Candidate order is then a seeded sample of the canonical list rather than the
ascending-PMCID prefix. PMCIDs are assigned at deposit, so taking the lowest N
would draw the entire corpus from the earliest year of the date range.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Mapping
from typing import Any

from ..types import ManifestEntry
from .jats import JatsError, read_metadata
from .ncbi import NcbiClient, article_url
from .store import ArticleStore


def _passes(metadata: Mapping[str, Any], corpus: Mapping[str, Any]) -> str:
    """Return "" if the paper is acceptable, else the rejection reason."""
    allowed_types = corpus.get("allowed_article_types") or []
    if allowed_types and metadata["article_type"] not in allowed_types:
        return f"article_type={metadata['article_type'] or 'missing'}"
    patterns = corpus.get("allowed_license_patterns") or []
    url = metadata["license_url"]
    if patterns and not any(pattern in url for pattern in patterns):
        return f"license={url or 'missing'}"
    return ""


def canonical_candidates(client: NcbiClient, corpus: Mapping[str, Any]) -> dict[str, Any]:
    """Every hit for the corpus query, in a stable order, with an audit trail."""
    term = corpus["query"]
    date_from, date_to = corpus["date_from"], corpus["date_to"]

    by_year = client.search_by_year(term, date_from, date_to)
    partitioned = [pmcid for ids in by_year.values() for pmcid in ids]
    unique = sorted(set(partitioned), key=int)
    whole_range = client.count(term, date_from, date_to)

    return {
        "ids": unique,
        "per_year": {year: len(ids) for year, ids in by_year.items()},
        "partition_total": len(partitioned),
        "unique_total": len(unique),
        "whole_range_count": whole_range,
        "partition_is_exact": len(partitioned) == whole_range,
    }


def select_corpus(
    corpus: Mapping[str, Any],
    seed: int,
    client: NcbiClient,
    store: ArticleStore,
    on_progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Choose ``target_papers`` papers deterministically and report the process."""
    survey = canonical_candidates(client, corpus)
    canonical = survey["ids"]
    if not canonical:
        raise ValueError("corpus query returned no hits")

    pool_size = min(int(corpus["candidate_pool"]), len(canonical))
    target = int(corpus["target_papers"])
    order = random.Random(seed).sample(canonical, pool_size)

    kept: list[ManifestEntry] = []
    rejected: dict[str, int] = {}
    failures: list[dict[str, str]] = []
    considered = 0

    for numeric_id in order:
        if len(kept) >= target:
            break
        considered += 1
        pmcid = f"PMC{numeric_id}"
        try:
            if store.has_raw(pmcid):
                xml = store.read_raw(pmcid)
            else:
                xml = client.fetch_article(pmcid)
                store.write_raw(pmcid, xml)
        except Exception as exc:  # noqa: BLE001 - reported, never fatal
            failures.append(
                {"pmcid": pmcid, "stage": "fetch", "reason": f"{type(exc).__name__}: {exc}"}
            )
            continue

        try:
            metadata = read_metadata(xml)
        except JatsError as exc:
            failures.append({"pmcid": pmcid, "stage": "metadata", "reason": str(exc)})
            continue

        reason = _passes(metadata, corpus)
        if reason:
            rejected[reason.split("=")[0]] = rejected.get(reason.split("=")[0], 0) + 1
            continue

        kept.append(
            ManifestEntry(
                pmcid=metadata["pmcid"],
                doi=metadata["doi"],
                title=metadata["title"],
                journal=metadata["journal"],
                pub_date=metadata["pub_date"],
                license_url=metadata["license_url"],
                source_url=article_url(metadata["pmcid"]),
                article_type=metadata["article_type"],
                license_text=metadata["license_text"],
            )
        )
        if on_progress:
            on_progress(f"kept {len(kept)}/{target} ({considered} considered)")

    return {
        "entries": kept,
        "survey": survey,
        "considered": considered,
        "pool_size": pool_size,
        "rejected": rejected,
        "failures": failures,
        "short": len(kept) < target,
    }
