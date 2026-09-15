"""Freezing the gold set, the same way the corpus manifest is frozen.

``configs/gold_set.jsonl`` holds the verified questions; its digest is pinned
into ``configs/gold.yaml`` as ``gold_set_sha``. From that commit the evaluation
set is immutable, and every later stage checks the file against the pin before
reading it.

It lives in ``configs/`` for the reason the manifest does: everything under
``data/`` is declared regenerable from configs, and a hand-verified gold set is
precisely the artefact that is not. Re-running the sampler regenerates the
*passages*; it cannot regenerate the judgement that a question was a good one.

``configs/gold_candidates.jsonl`` sits beside it and holds every candidate that
was drafted, accepted or not, with the evidence each check produced. A rejection
rate quoted without the rejections is not evidence of anything.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..hashing import stable_hash
from ..jsonl import read_jsonl, write_jsonl
from ..types import Query

UNFROZEN = "unfrozen"
GOLD_SET_FILENAME = "gold_set.jsonl"
CANDIDATES_FILENAME = "gold_candidates.jsonl"
_SHA_LINE = re.compile(r"^(\s*gold_set_sha:\s*)(\S+)(.*)$", re.MULTILINE)


class GoldSetError(Exception):
    """The gold set is missing, malformed, or does not match the frozen digest."""


def sort_queries(queries: list[Query]) -> list[Query]:
    """Canonical order: by query id.

    Sampling order is seeded and deliberately not corpus order, but the stored
    order must not depend on it, or the same 20 questions could produce two
    different digests.
    """
    return sorted(queries, key=lambda query: query.query_id)


def gold_set_sha(queries: list[Query]) -> str:
    """Digest of the gold set's content, not its file bytes.

    Sorts before hashing rather than trusting the caller to have done it, and
    hashes records rather than the file, so reformatting the JSONL or writing it
    on another platform cannot change the evaluation set's identity.
    """
    return stable_hash([query.to_dict() for query in sort_queries(queries)])


def write_gold_set(path: Path, queries: list[Query]) -> int:
    return write_jsonl(Path(path), [query.to_dict() for query in sort_queries(queries)])


def read_gold_set(path: Path) -> list[Query]:
    path = Path(path)
    if not path.is_file():
        raise GoldSetError(
            f"gold set not found: {path}. Run `ragbench gold build` and then "
            "`ragbench gold freeze` once."
        )
    queries = [Query.from_dict(record) for record in read_jsonl(path)]
    if not queries:
        raise GoldSetError(f"gold set is empty: {path}")
    return queries


def verify_frozen(path: Path, expected_sha: str) -> list[Query]:
    """Load the gold set and check it against the sha pinned in gold.yaml."""
    if not expected_sha or expected_sha == UNFROZEN:
        raise GoldSetError(
            "gold.yaml has gold_set_sha: unfrozen. The evaluation set must be frozen "
            "before anything is scored against it; use `ragbench gold freeze`."
        )
    queries = read_gold_set(path)
    found = gold_set_sha(queries)
    if found != expected_sha:
        raise GoldSetError(
            f"gold set digest mismatch: {path} hashes to {found}, but gold.yaml pins "
            f"{expected_sha}. The frozen evaluation set has been altered."
        )
    return queries


def freeze_sha(gold_yaml: Path, sha: str) -> None:
    """Write ``gold_set_sha`` back into gold.yaml.

    A line-level substitution rather than a YAML round-trip, for the reason the
    manifest's is: dumping the parsed document would discard every comment, and
    the comments are the record of how the thresholds were chosen.
    """
    gold_yaml = Path(gold_yaml)
    text = gold_yaml.read_text(encoding="utf-8")
    if not _SHA_LINE.search(text):
        raise GoldSetError(f"{gold_yaml}: no 'gold_set_sha:' line to freeze")
    updated = _SHA_LINE.sub(lambda m: f"{m.group(1)}{sha}{m.group(3)}", text, count=1)
    gold_yaml.write_text(updated, encoding="utf-8", newline="")
