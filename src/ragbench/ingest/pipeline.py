"""Ingest orchestration: the one-time freeze, and the resumable parse.

Both entry points are idempotent. ``run_ingest`` decides what to do per paper by
looking at the caches, so an interrupted run continues where it stopped and a
completed run does no work at all -- including no network, since the client is
only constructed if something actually needs fetching.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..config import parsed_papers_dir, raw_xml_dir
from ..jsonl import write_jsonl
from ..types import ParsedPaper
from .jats import JatsError, parse_article
from .manifest import freeze_sha, manifest_sha, verify_frozen, write_manifest
from .ncbi import NcbiClient
from .select import select_corpus
from .store import ArticleStore

ROLLUP_FILENAME = "papers.jsonl"
Progress = Callable[[str], None] | None


def _store(manifest_digest: str, data_root: Path) -> ArticleStore:
    return ArticleStore(raw_xml_dir(data_root), parsed_papers_dir(manifest_digest, data_root))


def run_selection(
    resolved: dict[str, Any],
    manifest_path: Path,
    corpus_yaml: Path,
    data_root: Path,
    on_progress: Progress = None,
) -> dict[str, Any]:
    """4a + 4b: select the corpus, write the manifest, freeze its digest."""
    corpus = resolved["corpus"]
    client = NcbiClient()
    # Selection fetches candidates it may reject, so the raw cache is shared and
    # keyed by PMCID alone; the parsed cache is not addressable until the digest
    # exists, which is precisely what this function produces.
    store = ArticleStore(raw_xml_dir(data_root), Path(data_root) / "parsed" / "pending")

    result = select_corpus(corpus, int(resolved["base"]["seed"]), client, store, on_progress)
    entries = result["entries"]
    digest = manifest_sha(entries)

    write_manifest(manifest_path, entries)
    freeze_sha(corpus_yaml, digest)

    return {**result, "manifest_sha": digest, "manifest_path": manifest_path}


def run_ingest(
    resolved: dict[str, Any],
    manifest_path: Path,
    data_root: Path,
    on_progress: Progress = None,
) -> dict[str, Any]:
    """4c: fetch and parse every manifest paper into ParsedPaper records."""
    corpus = resolved["corpus"]
    digest = str(corpus.get("manifest_sha", ""))
    entries = verify_frozen(manifest_path, digest)
    store = _store(digest, data_root)

    client: NcbiClient | None = None
    stats: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    fetched = parsed = cached = 0

    for entry in entries:
        pmcid = entry.pmcid
        if store.has_parsed(pmcid):
            cached += 1
            stats.append(_paper_stats(store.read_parsed(pmcid)))
            continue

        try:
            if store.has_raw(pmcid):
                xml = store.read_raw(pmcid)
            else:
                if client is None:
                    client = NcbiClient()
                xml = client.fetch_article(pmcid)
                store.write_raw(pmcid, xml)
                fetched += 1
        except Exception as exc:  # noqa: BLE001 - reported, never fatal
            failures.append(
                {"pmcid": pmcid, "stage": "fetch", "reason": f"{type(exc).__name__}: {exc}"}
            )
            continue

        try:
            paper = parse_article(xml, corpus)
        except JatsError as exc:
            failures.append({"pmcid": pmcid, "stage": "parse", "reason": str(exc)})
            continue

        store.write_parsed(paper)
        parsed += 1
        stats.append(_paper_stats(paper))
        if on_progress:
            on_progress(f"parsed {parsed} ({cached} cached) of {len(entries)}")

    rollup = store.parsed_dir / ROLLUP_FILENAME
    write_jsonl(rollup, [store.read_parsed(p).to_dict() for p in store.parsed_pmcids()])

    return {
        "manifest_sha": digest,
        "n_manifest": len(entries),
        "n_fetched": fetched,
        "n_parsed": parsed,
        "n_cached": cached,
        "parsed_dir": store.parsed_dir,
        "rollup": rollup,
        "stats": sorted(stats, key=lambda row: row["pmcid"]),
        "failures": failures,
    }


def _paper_stats(paper: ParsedPaper) -> dict[str, Any]:
    metadata = paper.parse_metadata
    return {
        "pmcid": paper.pmcid,
        "year": paper.year,
        "tables_placeholdered": metadata.get("tables_placeholdered", 0),
        "equations_placeholdered": metadata.get("equations_placeholdered", 0),
        "sections_dropped": metadata.get("sections_dropped", 0),
        "figures_dropped": metadata.get("figures_dropped", 0),
        "xrefs_dropped": metadata.get("xrefs_dropped", 0),
        "retained_chars": metadata.get("retained_chars", len(paper.body)),
        "n_sections": metadata.get("n_sections", len(paper.sections)),
    }
