"""The embedding factor: two arms behind one interface, plus a CPU stand-in.

Importing this module pulls numpy and nothing heavier. torch and adapters are
imported inside the constructors that need them, so the CPU smoke path and CLI
startup never load a GPU stack.
"""

from __future__ import annotations

from .base import (
    SPECIAL_TOKENS,
    Embedder,
    arm_params,
    build_embedder,
    normalise_rows,
    usable_tokens,
)

__all__ = [
    "SPECIAL_TOKENS",
    "Embedder",
    "arm_params",
    "build_embedder",
    "normalise_rows",
    "usable_tokens",
]
