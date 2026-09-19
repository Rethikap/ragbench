"""The embedding factor: the interface, the stand-in, and the asymmetry rule.

Everything here runs offline. The real arms are exercised on the GPU host; what
is tested here is the contract they sit behind, because that contract is where
the query-prefix asymmetry and the chunking/embedding separation live.
"""

from __future__ import annotations

import logging
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


class _AdaptersConfig:
    def __init__(self) -> None:
        self.adapters: dict[str, object] = {}
        self.active_setup = None


class _RecordingModel:
    """Stands in for an adapters-enabled model, recording how it was called.

    Models the one behaviour of `load_adapter` that matters here: `set_active`
    is honoured only when the adapter name is NEW. Loading a name the model
    already has logs "Overwriting existing adapter" and never activates.
    """

    def __init__(self, already_loaded: bool = False) -> None:
        self.calls: list[dict] = []
        self.adapters_config = _AdaptersConfig()
        if already_loaded:
            self.adapters_config.adapters["proximity"] = object()

    def load_adapter(self, adapter_id, **kwargs):
        self.calls.append({"adapter_id": adapter_id, **kwargs})
        if "proximity" not in self.adapters_config.adapters:
            self.adapters_config.adapters["proximity"] = object()
            if kwargs.get("set_active"):
                self.adapters_config.active_setup = "proximity"
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


def test_set_active_being_ignored_is_caught_at_load() -> None:
    """`set_active=True` applies only to an adapter the model does not already
    have; re-loading a name logs "Overwriting existing adapter" and silently
    leaves nothing activated. Read from adapters_config, never from the
    `active_adapters` attribute, which collides with a transformers method."""
    from ragbench.embedding.huggingface import load_pinned_adapter

    with pytest.raises(ValueError, match="set_active did not take"):
        load_pinned_adapter(_RecordingModel(already_loaded=True), "allenai/specter2", "abc123")


def test_a_freshly_loaded_adapter_activates() -> None:
    from ragbench.embedding.huggingface import load_pinned_adapter

    model = _RecordingModel()
    assert load_pinned_adapter(model, "allenai/specter2", "abc123") == "proximity"
    assert model.adapters_config.active_setup == "proximity"


# ------------------------------------------------------------ device placement


class _Tensor:
    def __init__(self, device: str) -> None:
        self.device = device


class _FakeModel:
    """A model whose `.to()` moves only what it knows about.

    `late` stands for tensors added after a move -- an adapter's weights, which
    are created on CPU when the adapter is loaded and stay there.
    """

    def __init__(self, devices=("cpu",), late=()) -> None:
        self._params = [_Tensor(d) for d in devices]
        self._buffers: list[_Tensor] = []
        self._late = [_Tensor(d) for d in late]
        self.moves: list[str] = []
        self.moves_late = True

    def parameters(self):
        return list(self._params) + list(self._late)

    def buffers(self):
        return list(self._buffers)

    def to(self, device):
        self.moves.append(device)
        for tensor in self._params:
            tensor.device = device
        if self.moves_late:
            for tensor in self._late:
                tensor.device = device
        return self


def test_every_tensor_including_the_adapter_reports_one_device() -> None:
    """The invariant the specter2 crash violated: base model on cuda:0, adapter
    weights left on cpu, and the failure surfacing inside a matmul."""
    from ragbench.embedding.huggingface import model_devices, place_on_device

    model = _FakeModel(devices=("cpu", "cpu"), late=("cpu",))
    assert place_on_device(model, "cuda:0") == "cuda:0"
    assert model_devices(model) == {"cuda:0"}


def test_a_tensor_left_behind_by_the_move_is_caught_here() -> None:
    """Rather than several frames later, in the forward pass."""
    from ragbench.embedding.huggingface import place_on_device

    model = _FakeModel(devices=("cpu",), late=("cpu",))
    model.moves_late = False  # the adapter does not follow the move
    with pytest.raises(ValueError, match="split across devices"):
        place_on_device(model, "cuda:0")


def test_buffers_are_checked_as_well_as_parameters() -> None:
    from ragbench.embedding.huggingface import place_on_device

    model = _FakeModel(devices=("cpu",))
    model._buffers = [_Tensor("cuda:0")]
    model.moves_late = False
    model._late = []
    model._buffers[0].device = "cpu"
    assert place_on_device(model, "cpu") == "cpu"


# -------------------------------------------------- the adapter actually runs


class _FakeAdapterModel:
    """Records activation and produces a different embedding when active."""

    def __init__(self, adapter_changes_output: bool = True) -> None:
        self.active = "proximity"
        self.history: list = []
        self._changes = adapter_changes_output

    def set_active_adapters(self, setup):
        if setup is not None and setup != "proximity":
            raise ValueError(f"No adapter with name '{setup}' found.")
        self.active = setup
        self.history.append(setup)

    def embed(self):
        if self.active and self._changes:
            return np.array([[1.0, 0.0]])
        return np.array([[0.0, 1.0]])


def test_the_adapter_is_proved_to_be_in_the_forward_pass() -> None:
    from ragbench.embedding.huggingface import verify_adapter_participates

    model = _FakeAdapterModel(adapter_changes_output=True)
    verify_adapter_participates(model, model.embed, "proximity")
    assert model.history == [None, "proximity"]


def test_a_loaded_but_inert_adapter_is_refused() -> None:
    """The failure that reached a GPU run: the adapter present, the forward pass
    unchanged by it, and every log line still saying 'specter2'."""
    from ragbench.embedding.huggingface import verify_adapter_participates

    model = _FakeAdapterModel(adapter_changes_output=False)
    with pytest.raises(ValueError, match="not in the forward pass"):
        verify_adapter_participates(model, model.embed, "proximity")


def test_the_probe_restores_the_adapter_afterwards() -> None:
    """A probe that left the adapter off would silently ruin every embedding
    after it -- worse than the bug it exists to catch."""
    from ragbench.embedding.huggingface import verify_adapter_participates

    model = _FakeAdapterModel()
    verify_adapter_participates(model, model.embed, "proximity")
    assert model.active == "proximity"


def test_the_adapter_is_restored_even_if_the_probe_raises() -> None:
    from ragbench.embedding.huggingface import verify_adapter_participates

    model = _FakeAdapterModel()
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("probe blew up")
        return np.array([[1.0, 0.0]])

    with pytest.raises(RuntimeError, match="probe blew up"):
        verify_adapter_participates(model, flaky, "proximity")
    assert model.active == "proximity"


def test_truthiness_of_active_adapters_is_not_a_check() -> None:
    """Why the old guard could never fire. `active_adapters` is a method on
    transformers' PeftAdapterMixin, which every PreTrainedModel inherits, so the
    attribute is a bound method -- truthy with or without an adapter."""
    from transformers import PreTrainedModel

    attribute = PreTrainedModel.active_adapters
    assert not isinstance(attribute, property)
    assert callable(attribute)
    assert bool(attribute) is True


# ------------------------------------------- the probe says so, in the log


def test_a_passing_probe_says_so_with_the_distance(caplog) -> None:
    """A probe whose only evidence is the absence of a crash is indistinguishable
    from a probe that never ran. The number matters too: a distance just above
    allclose's tolerance would pass the check while saying the adapter barely
    participates."""
    from ragbench.embedding.huggingface import verify_adapter_participates

    model = _FakeAdapterModel(adapter_changes_output=True)
    with caplog.at_level(logging.WARNING, logger="ragbench.embedding.huggingface"):
        verify_adapter_participates(model, model.embed, "proximity")

    passes = [r for r in caplog.records if "adapter probe: PASS" in r.getMessage()]
    assert len(passes) == 1
    # The doubles differ by exactly sqrt(2): (1, 0) against (0, 1).
    assert "1.41421" in passes[0].getMessage()


def test_a_failing_probe_reports_how_close_the_two_passes_were() -> None:
    """Distinguishes "the adapter is not loaded at all" from "it is loaded and
    contributes almost nothing" -- different bugs, same exception without it."""
    from ragbench.embedding.huggingface import verify_adapter_participates

    model = _FakeAdapterModel(adapter_changes_output=False)
    with pytest.raises(ValueError, match=r"L2 distance 0 between"):
        verify_adapter_participates(model, model.embed, "proximity")


def test_the_libraries_own_inactive_warning_is_suppressed_for_the_probe_only() -> None:
    """The deactivated pass makes `adapters` warn that nothing is activated. Here
    that is the check working, not a symptom -- but it is word-for-word the
    symptom of a real activation bug, so it is silenced for this one call and
    nowhere else."""
    from ragbench.embedding.huggingface import verify_adapter_participates

    adapters_logger = logging.getLogger("adapters.model_mixin")
    adapters_logger.setLevel(logging.INFO)
    model = _FakeAdapterModel()
    levels: list[int] = []

    def probe():
        levels.append(adapters_logger.level)
        return np.array([[1.0, 0.0]]) if model.active else np.array([[0.0, 1.0]])

    try:
        verify_adapter_participates(model, probe, "proximity")
        assert levels == [logging.INFO, logging.ERROR]
        assert adapters_logger.level == logging.INFO
    finally:
        adapters_logger.setLevel(logging.NOTSET)


def test_the_suppression_is_lifted_even_when_the_probe_raises() -> None:
    from ragbench.embedding.huggingface import _quiet_adapters_inactive_warning

    adapters_logger = logging.getLogger("adapters.model_mixin")
    adapters_logger.setLevel(logging.INFO)
    try:
        with pytest.raises(RuntimeError):
            with _quiet_adapters_inactive_warning():
                assert adapters_logger.level == logging.ERROR
                raise RuntimeError("probe blew up")
        assert adapters_logger.level == logging.INFO
    finally:
        adapters_logger.setLevel(logging.NOTSET)
