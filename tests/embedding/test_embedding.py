"""The embedding factor: the interface, the stand-in, and the asymmetry rule.

Everything here runs offline. The real arms are exercised on the GPU host; what
is tested here is the contract they sit behind, because that contract is where
the query-prefix asymmetry and the chunking/embedding separation live.
"""

from __future__ import annotations

import sys

import numpy as np
import pytest

from ragbench.embedding.base import (
    SPECIAL_TOKENS,
    arm_params,
    build_embedder,
    normalise_rows,
    token_counter,
    usable_tokens,
)
from ragbench.embedding.standin import HashingEmbedder

BASE = {
    "normalize": True,
    "pooling": "cls",
    "max_seq_tokens": 512,
    "batch_size": 8,
    "dimension": 32,
}
BGE = {**BASE, "model_id": "stand-in", "query_instruction": "Represent this sentence: "}
SPECTER = {**BASE, "model_id": "stand-in", "query_instruction": ""}

RESOLVED = {
    "base": {"embedding": BASE},
    "factors": {
        "embedding": {
            "bge": {"model_id": "stand-in", "query_instruction": "Represent this sentence: "},
            "specter2": {"model_id": "stand-in", "query_instruction": ""},
        }
    },
}


# ------------------------------------------------------------- the asymmetry


def test_the_query_instruction_reaches_queries_and_never_documents() -> None:
    """bge is trained asymmetrically and specter2 is not, so a single `encode`
    would make prefixing a document possible by accident -- which would corrupt
    every vector in an index while the run still looked healthy."""
    embedder = HashingEmbedder(BGE)
    plain = HashingEmbedder(SPECTER)

    text = "amyloid beta in cerebrospinal fluid"
    # A document is the same vector whether the arm carries an instruction.
    assert np.allclose(embedder.encode_documents([text]), plain.encode_documents([text]))
    # A query is not, for the arm that has one.
    assert not np.allclose(embedder.encode_queries([text]), embedder.encode_documents([text]))
    # And is, for the arm that does not.
    assert np.allclose(plain.encode_queries([text]), plain.encode_documents([text]))


def test_an_arm_without_an_instruction_treats_queries_as_documents() -> None:
    plain = HashingEmbedder(SPECTER)
    texts = ["tau pathology", "plasma neurofilament light"]
    assert np.allclose(plain.encode_queries(texts), plain.encode_documents(texts))


# -------------------------------------------------------------- the stand-in


def test_the_stand_in_is_deterministic_across_processes() -> None:
    """Every feature index comes from hashing.py, never Python's salted builtin
    hash, so two machines agree (I3)."""
    first = HashingEmbedder(BGE).encode_documents(["cerebrospinal fluid biomarkers"])
    second = HashingEmbedder(BGE).encode_documents(["cerebrospinal fluid biomarkers"])
    assert np.array_equal(first, second)


def test_the_stand_in_places_shared_vocabulary_near_together() -> None:
    """Not a semantic model, but a lexical projection -- enough that a retrieval
    smoke test returns something other than noise."""
    embedder = HashingEmbedder(BGE)
    vectors = embedder.encode_documents(
        [
            "amyloid beta plaques in the hippocampus",
            "amyloid beta plaques in the cortex",
            "gas chromatography of industrial solvents",
        ]
    )
    near = float(vectors[0] @ vectors[1])
    far = float(vectors[0] @ vectors[2])
    assert near > far


def test_vectors_are_normalised() -> None:
    vectors = HashingEmbedder(BGE).encode_documents(["one", "two words here", "three"])
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1.0)


def test_an_empty_batch_keeps_its_shape() -> None:
    vectors = HashingEmbedder(BGE).encode_documents([])
    assert vectors.shape == (0, 32)


def test_the_stand_in_truncates_like_the_arm_it_stands_in_for() -> None:
    """It must not quietly see more of a chunk than a real encoder would."""
    short = HashingEmbedder({**BGE, "max_seq_tokens": 4})
    long = HashingEmbedder({**BGE, "max_seq_tokens": 400})
    text = " ".join(f"word{i}" for i in range(50))
    assert not np.allclose(short.encode_documents([text]), long.encode_documents([text]))


def test_normalise_rows_leaves_a_zero_row_alone() -> None:
    """A zero row would become NaN and poison every neighbour query touching it."""
    vectors = normalise_rows(np.array([[0.0, 0.0], [3.0, 4.0]], dtype=np.float32))
    assert np.array_equal(vectors[0], np.zeros(2, dtype=np.float32))
    assert np.allclose(np.linalg.norm(vectors[1]), 1.0)


# ------------------------------------------------------------------ the seam


def test_the_stand_in_needs_no_gpu_stack() -> None:
    """The CPU smoke path must never drag torch in; that is what keeps the whole
    pipeline runnable on a laptop."""
    build_embedder(BGE).encode_documents(["anything"])
    assert "torch" not in sys.modules


def test_a_real_model_id_never_falls_back_to_the_stand_in() -> None:
    """The stand-in is chosen by id, so a config asking for a real model fails
    when it cannot be loaded instead of quietly measuring something else."""
    with pytest.raises(Exception) as caught:
        build_embedder({**BASE, "model_id": "BAAI/bge-base-en-v1.5", "model_revision": ""})
    assert "stand-in" not in str(caught.value).lower()


def test_arm_params_merges_base_with_the_level() -> None:
    params = arm_params(RESOLVED, "bge")
    assert params["query_instruction"] == "Represent this sentence: "
    assert params["max_seq_tokens"] == 512
    assert arm_params(RESOLVED, "specter2")["query_instruction"] == ""


def test_an_unknown_embedding_level_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown embedding level"):
        arm_params(RESOLVED, "e5")


def test_no_chunking_input_reaches_an_embedder() -> None:
    """Invariant I2 from the other side: the embedding arm is built from
    base.embedding and factors.embedding only."""
    polluted = {
        "base": {"embedding": BASE, "chunking": {"strategy": "fixed", "target_tokens": 512}},
        "factors": RESOLVED["factors"],
    }
    assert "strategy" not in arm_params(polluted, "bge")
    assert "target_tokens" not in arm_params(polluted, "bge")


# ------------------------------------------------------------ sequence limit


def test_the_sequence_limit_counts_the_special_tokens() -> None:
    """max_seq_tokens is the model's position limit and includes [CLS]/[SEP], so
    a chunk has room for two fewer content tokens than the number suggests."""
    assert SPECIAL_TOKENS == 2
    assert usable_tokens(512) == 510


def test_a_token_counter_needs_no_encoder_weights() -> None:
    count = token_counter(BGE)
    assert count("three words here") == 3


# ----------------------------------------------------- the adapter call shape


class _RecordingModel:
    """Stands in for an adapters-enabled model, recording how it was called."""

    def __init__(self, activate: bool = True) -> None:
        self.calls: list[dict] = []
        self.active_adapters = None
        self._activate = activate

    def load_adapter(self, adapter_id, **kwargs):
        self.calls.append({"adapter_id": adapter_id, **kwargs})
        if kwargs.get("set_active") and self._activate:
            self.active_adapters = "proximity"
        return "proximity"


def test_the_adapter_is_pinned_with_version_not_revision() -> None:
    """`adapters` forwards `version` to snapshot_download(revision=...); anything
    else lands in **kwargs and is discarded, so passing `revision=` loads the
    adapter from main and reports success. That is exactly the unpinned-artefact
    failure this project has an invariant against, and it leaves no trace."""
    from ragbench.embedding.huggingface import load_pinned_adapter

    model = _RecordingModel()
    load_pinned_adapter(model, "allenai/specter2", "2081559630a8")
    call = model.calls[0]
    assert call["version"] == "2081559630a8"
    assert "revision" not in call
    assert call["set_active"] is True


def test_an_unpinned_adapter_is_refused() -> None:
    from ragbench.embedding.huggingface import load_pinned_adapter

    with pytest.raises(ValueError, match="adapter_revision is required"):
        load_pinned_adapter(_RecordingModel(), "allenai/specter2", "")


def test_an_adapter_that_loads_but_does_not_activate_is_an_error() -> None:
    """specter2 without its proximity adapter is a different model, and silence
    here would leave every log line still saying 'specter2'."""
    from ragbench.embedding.huggingface import load_pinned_adapter

    with pytest.raises(ValueError, match="is not active"):
        load_pinned_adapter(_RecordingModel(activate=False), "allenai/specter2", "abc123")
