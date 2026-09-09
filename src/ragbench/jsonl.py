"""JSONL persistence.

Every stage writes JSONL so that work is resumable: a partially written file is
still a valid prefix of the finished one, and re-running appends only what is
missing.

Bytes are pinned deliberately -- canonical JSON, explicit "\\n", UTF-8, no
platform newline translation. The manifest's digest is computed from records
rather than file bytes, but keeping the file byte-stable means a manifest
written on Windows and one written on Colab compare equal.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any

from .hashing import canonical_json


def write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> int:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        for record in records:
            handle.write(canonical_json(record))
            handle.write("\n")
            count += 1
    return count


def append_jsonl(path: Path, record: Mapping[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as handle:
        handle.write(canonical_json(record))
        handle.write("\n")


def read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    path = Path(path)
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{number}: malformed JSONL: {exc}") from exc
