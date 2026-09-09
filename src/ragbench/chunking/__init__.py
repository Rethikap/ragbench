"""The chunking factor: two strategies, one canonical tokenizer.

Both arms tokenize with ``chunking.tokenizer_id`` from base.yaml, never with an
embedding model. That is invariant I2, and it is what keeps the design a clean
factorial: two chunk sets across the 8 runs, not four.
"""

from __future__ import annotations

from .base import CHUNKERS, Piece, build_chunker

__all__ = ["CHUNKERS", "Piece", "build_chunker"]
