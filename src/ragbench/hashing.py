"""Deterministic hashing.

Every identifier in this project (config hashes, chunk-set ids, index keys, cache
keys) comes from here, so that two runs on two machines agree byte for byte.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

DIGEST_CHARS = 12


def canonical_json(obj: Any) -> str:
    """Serialise to the one string form we ever hash.

    Sorted keys, no insignificant whitespace, ASCII-escaped. Tuples serialise as
    arrays, so a tuple and a list of the same values hash identically -- which is
    what we want, since YAML gives lists and the dataclasses hold tuples.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(obj: Any, length: int = DIGEST_CHARS) -> str:
    """Short, stable digest of any JSON-serialisable object."""
    return hashlib.blake2b(canonical_json(obj).encode("utf-8"), digest_size=32).hexdigest()[:length]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))
