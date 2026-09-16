"""The two real arms. Nothing here runs without torch, and nothing else imports it.

``HuggingFaceEmbedder`` is bge: one checkpoint, [CLS] pooling, an instruction
prefix on queries only.

``AdapterEmbedder`` is specter2, and it is the base encoder **plus its proximity
adapter**. That distinction is the whole arm: ``allenai/specter2_base`` on its
own is not SPECTER2 for retrieval, and loading it alone would measure something
the SPECTER2 paper never reported while every log line still said "specter2".
The adapter is activated explicitly and the constructor refuses if activation
did not take, because a silently inactive adapter is exactly the failure that
would be invisible in the results.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from .base import SPECIAL_TOKENS, normalise_rows


class _TorchEncoder:
    """Shared machinery: tokenize, forward, pool, normalise. No model loading."""

    def __init__(self, params: Mapping[str, Any]) -> None:
        import torch

        self._torch = torch
        self.max_seq_tokens = int(params["max_seq_tokens"])
        self.batch_size = int(params.get("batch_size", 32))
        self.normalize = bool(params.get("normalize", True))
        self.query_instruction = str(params.get("query_instruction", ""))
        pooling = str(params.get("pooling", "cls"))
        if pooling != "cls":
            raise ValueError(
                f"embedding.pooling is {pooling!r}; both arms are [CLS]-pooled and pooling "
                "is not a factor. Changing it for one arm would make it an uncontrolled "
                "variable inside the embedding factor."
            )
        self._device = "cuda" if torch.cuda.is_available() else "cpu"

    def content_tokens(self, text: str) -> int:
        return len(self._tokenizer(text, add_special_tokens=False)["input_ids"])

    def _encode(self, texts: Sequence[str]) -> np.ndarray:
        torch = self._torch
        out: list[np.ndarray] = []
        for start in range(0, len(texts), self.batch_size):
            batch = list(texts[start : start + self.batch_size])
            encoded = self._tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=self.max_seq_tokens,
                return_tensors="pt",
            ).to(self._device)
            with torch.no_grad():
                hidden = self._model(**encoded).last_hidden_state
            # [CLS] pooling: the first position, which is what both arms are
            # trained to use as the sequence representation.
            out.append(hidden[:, 0].float().cpu().numpy())
        vectors = np.vstack(out) if out else np.zeros((0, self.dimension), dtype=np.float32)
        return normalise_rows(vectors) if self.normalize else vectors

    def encode_documents(self, texts: Sequence[str]) -> np.ndarray:
        return self._encode(texts)

    def encode_queries(self, texts: Sequence[str]) -> np.ndarray:
        prefix = self.query_instruction
        return self._encode([f"{prefix}{text}" for text in texts] if prefix else list(texts))


class HuggingFaceEmbedder(_TorchEncoder):
    """A pinned encoder checkpoint, [CLS]-pooled. bge's arm."""

    def __init__(self, params: Mapping[str, Any]) -> None:
        super().__init__(params)
        from transformers import AutoModel, AutoTokenizer

        model_id = str(params["model_id"])
        revision = str(params.get("model_revision") or "")
        if not revision:
            raise ValueError(
                f"{model_id}: embedding.model_revision is required. A Hub id is a mutable "
                "pointer and every vector in the index is a function of the checkpoint "
                "behind it."
            )
        self.name = f"{model_id}@{revision[:12]}"
        self._tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
        self._model = AutoModel.from_pretrained(model_id, revision=revision).to(self._device)
        self._model.eval()
        self.dimension = int(self._model.config.hidden_size)
        limit = int(getattr(self._model.config, "max_position_embeddings", self.max_seq_tokens))
        if self.max_seq_tokens > limit:
            raise ValueError(
                f"embedding.max_seq_tokens is {self.max_seq_tokens} but {model_id} accepts "
                f"{limit} positions including the {SPECIAL_TOKENS} special tokens."
            )


def load_pinned_adapter(model: Any, adapter_id: str, revision: str) -> str:
    """Load an adapter at an exact commit and make it active. Returns its name.

    The parameter is ``version``, not ``revision``. `adapters` forwards it to
    ``snapshot_download(revision=...)``, and anything else lands in ``**kwargs``
    and is discarded -- so passing ``revision=`` loads the adapter from ``main``
    and reports success. That is the precise failure this project has an
    invariant against: an unpinned artefact moving under a fixed id, with
    nothing in the logs to show for it.

    Extracted from the embedder so the call shape can be tested without a GPU,
    a download, or the optional dependency installed.
    """
    if not revision:
        raise ValueError(
            f"{adapter_id}: embedding.adapter_revision is required. The adapter is half of "
            "this arm's identity, and an unpinned one moves the vectors under a fixed "
            "model id."
        )
    name = model.load_adapter(
        adapter_id,
        version=revision,
        source="hf",
        set_active=True,
    )
    if not getattr(model, "active_adapters", None):
        raise ValueError(
            f"{adapter_id} loaded but is not active. specter2 without its proximity "
            "adapter is a different model, and an inactive adapter is the one failure that "
            "would leave every log line still saying 'specter2'."
        )
    return str(name)


class AdapterEmbedder(HuggingFaceEmbedder):
    """Base encoder plus an activated adapter. specter2's arm.

    ``adapters`` is an optional dependency and it pins transformers to 4.57.x,
    so the arm runs where that environment exists -- the GPU host. See
    docs/kaggle.md.
    """

    def __init__(self, params: Mapping[str, Any]) -> None:
        super().__init__(params)
        import adapters

        adapter_id = str(params["adapter_id"])
        revision = str(params.get("adapter_revision") or "")
        adapters.init(self._model)
        self._adapter = load_pinned_adapter(self._model, adapter_id, revision)
        self.name = f"{self.name}+{adapter_id}@{revision[:12]}"
