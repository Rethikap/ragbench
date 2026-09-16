"""The embedding factor: one interface, two arms, one CPU stand-in.

Both arms are BERT-sized encoders taking [CLS] as the sequence representation,
and they differ in exactly two things -- which checkpoint, and whether a query
carries an instruction prefix. Everything else (pooling, normalisation, the
sequence limit) is fixed in base.yaml, because a difference anywhere else would
be an uncontrolled variable wearing the embedding factor's name.

Documents and queries go through separate methods, and that is not decoration.
bge is trained asymmetrically: a query is prefixed with an instruction, a
document never is. specter2 is symmetric and takes no prefix. One `encode`
method would make it possible to prefix a document by accident, which would
corrupt every vector in an index while leaving the run looking healthy -- so the
interface makes the two calls different and the prefix lives on the query side
only.

The GPU-dependent implementations import torch lazily, inside their
constructors. `import ragbench.embedding` stays stdlib + numpy, so CLI startup
and the CPU smoke path never drag a 2 GB dependency in.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, Protocol

import numpy as np

#: [CLS] and [SEP]. A chunk of more than max_seq_tokens - SPECIAL_TOKENS content
#: tokens loses its tail when the model encodes it.
SPECIAL_TOKENS = 2


class Embedder(Protocol):
    name: str
    dimension: int
    max_seq_tokens: int

    def encode_documents(self, texts: Sequence[str]) -> np.ndarray:
        """Vectors for chunk text. Never prefixed, whatever the arm."""

    def encode_queries(self, texts: Sequence[str]) -> np.ndarray:
        """Vectors for questions. Prefixed iff the arm's level says so."""

    def content_tokens(self, text: str) -> int:
        """Tokens excluding [CLS]/[SEP], for truncation accounting."""


def usable_tokens(max_seq_tokens: int) -> int:
    """Content tokens that survive encoding, once the specials are counted."""
    return max_seq_tokens - SPECIAL_TOKENS


def normalise_rows(vectors: np.ndarray) -> np.ndarray:
    """L2-normalise, leaving a zero row alone rather than dividing by zero.

    Cosine similarity over normalised vectors is a dot product, which is what
    the index is configured for; a zero row would otherwise become NaN and
    poison every neighbour query that touched it.
    """
    lengths = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.where(lengths == 0, 1.0, lengths)


def arm_params(resolved: Mapping[str, Any], level: str) -> dict[str, Any]:
    """Embedding parameters for one arm: base embedding plus the factor level.

    Deliberately built from ``base.embedding`` and ``factors.embedding`` only.
    No chunking input reaches an embedder, and no embedding input reaches a
    chunker (I2) -- the two factors meet for the first time in the index id, and
    they meet there as opaque strings.
    """
    try:
        override = resolved["factors"]["embedding"][level]
    except KeyError:
        known = ", ".join(sorted(resolved["factors"]["embedding"]))
        raise ValueError(f"unknown embedding level {level!r}; known: {known}") from None
    return {**resolved["base"]["embedding"], **override}


def token_counter(params: Mapping[str, Any]) -> Callable[[str], int]:
    """How this arm will segment text, without loading the encoder weights.

    The truncation census needs to know how many tokens the model will make of a
    chunk, not what it will make of them. A tokenizer is a few hundred kilobytes
    where the encoder is hundreds of megabytes, so separating the two is what
    lets the census -- the one number in this stage that has to be checked rather
    than assumed -- run on a laptop with no GPU.
    """
    model_id = str(params["model_id"])
    if model_id == "stand-in":
        from .standin import HashingEmbedder

        return HashingEmbedder(params).content_tokens
    from ..tokenizers import load_tokenizer

    return load_tokenizer(model_id, str(params.get("model_revision") or "")).count


def build_embedder(params: Mapping[str, Any]) -> Embedder:
    """Construct the arm named by ``model_id``, or the offline stand-in.

    ``stand-in`` is selected by model id rather than by a flag, so a config that
    asks for a real model cannot silently fall back to the stand-in when the
    download fails -- it fails instead.
    """
    model_id = str(params["model_id"])
    if model_id == "stand-in":
        from .standin import HashingEmbedder

        return HashingEmbedder(params)
    if params.get("adapter_id"):
        from .huggingface import AdapterEmbedder

        return AdapterEmbedder(params)
    from .huggingface import HuggingFaceEmbedder

    return HuggingFaceEmbedder(params)
