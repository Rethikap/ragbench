"""On-disk caches. This is where resumability actually lives.

Two caches, keyed as the hierarchy in :mod:`ragbench.cache_keys` requires:

* raw JATS, keyed by PMCID alone -- the bytes NCBI returns for a frozen PMCID do
  not depend on our parser, so a PARSER_VERSION bump must re-parse but must never
  re-download.
* parsed papers, under a directory keyed by manifest_sha + PARSER_VERSION.

Every write is atomic (temp file, then replace). An interrupted run must not
leave a truncated file that a later run would mistake for a complete cache hit;
that is the difference between "resumable" and "corrupt".
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from ..hashing import canonical_json
from ..types import ParsedPaper


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data)
    os.replace(temporary, path)


class ArticleStore:
    def __init__(self, raw_dir: Path, parsed_dir: Path) -> None:
        self.raw_dir = Path(raw_dir)
        self.parsed_dir = Path(parsed_dir)

    # -------------------------------------------------------------- raw JATS

    def raw_path(self, pmcid: str) -> Path:
        return self.raw_dir / f"{pmcid}.xml"

    def has_raw(self, pmcid: str) -> bool:
        path = self.raw_path(pmcid)
        return path.is_file() and path.stat().st_size > 0

    def read_raw(self, pmcid: str) -> bytes:
        return self.raw_path(pmcid).read_bytes()

    def write_raw(self, pmcid: str, data: bytes) -> None:
        _atomic_write(self.raw_path(pmcid), data)

    # --------------------------------------------------------- parsed papers

    def parsed_path(self, pmcid: str) -> Path:
        return self.parsed_dir / f"{pmcid}.json"

    def has_parsed(self, pmcid: str) -> bool:
        path = self.parsed_path(pmcid)
        return path.is_file() and path.stat().st_size > 0

    def read_parsed(self, pmcid: str) -> ParsedPaper:
        data = json.loads(self.parsed_path(pmcid).read_text(encoding="utf-8"))
        return ParsedPaper.from_dict(data)

    def write_parsed(self, paper: ParsedPaper) -> None:
        _atomic_write(
            self.parsed_path(paper.pmcid),
            canonical_json(paper.to_dict()).encode("utf-8"),
        )

    def parsed_pmcids(self) -> list[str]:
        if not self.parsed_dir.is_dir():
            return []
        return sorted(path.stem for path in self.parsed_dir.glob("*.json"))
