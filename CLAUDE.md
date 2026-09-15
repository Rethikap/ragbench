# ragbench

A **controlled 2×2×2 factorial experiment** measuring how three RAG design choices affect
scientific-literature QA over a frozen corpus of open-access Alzheimer's biomarker papers.

This repository is a **measurement harness, not an application**. It has no users, no
sessions, and no conversations. Every line of code exists to make eight runs comparable to
each other. If a change does not make a measurement more valid, more reproducible, or
cheaper to compute, it does not belong here.

---

## Invariants

These are not preferences. Code that violates one is **wrong**, not merely
differently-styled, and should be fixed rather than debated.

### I1 — The controlled variable is a token budget, NOT a chunk count

Every configuration fills the generator context to a **constant 2000-token budget**
(`retrieval.context_token_budget`). It does **not** retrieve a fixed number of chunks.

This is the entire point of the experiment. A run using a coarse chunker puts *fewer,
larger* chunks in context; a run using a finer chunker puts *more, smaller* ones. Holding
*k* constant instead would confound chunk size with context size and make the comparison
meaningless.

Concretely:

- Pull `retrieval.depth` (30) dense candidates, rerank them if the factor level says so,
  then walk the ranked list adding chunks until the next one will not fit.
- `fill_policy: stop_at_overflow` — **never truncate a chunk** to make it fit. Stop at the
  first chunk that overflows, and record why.
- The budget is measured with the **generator's** tokenizer
  (`retrieval.budget_tokenizer_id`, Qwen2.5-7B-Instruct), because it is the generator's
  context that is being controlled — not the embedder's, not the chunker's.
- `RetrievalResult` must faithfully record `n_chunks`, `tokens_used`, `budget_slack` and
  `stopped_reason`. Those fields are results, not diagnostics.

> **Any function that takes a `top_k` and returns that many chunks for the generator is a
> bug.** `depth` is a candidate-pool size for reranking; it is not `k`.

### I2 — Two chunk sets, not four

Chunking uses **one canonical tokenizer** (`chunking.tokenizer_id`) for *both* embedding
arms. Chunk boundaries are therefore a function of the chunking factor alone, and the 8
runs share exactly **two** chunk sets — one `fixed`, one `recursive`.

The configured value happens to be `BAAI/bge-base-en-v1.5`, which is also the `bge`
embedding model id. **This coincidence is a trap.** It is a fixed constant that must never
be swapped to follow the embedding factor. Doing so would produce four chunk sets, make
chunking and embedding non-orthogonal, and destroy the factorial design.

Two tokenizers exist in this project and they are never interchangeable:

| Tokenizer | Config keys | Pinned revision | Role |
|---|---|---|---|
| `BAAI/bge-base-en-v1.5` | `chunking.tokenizer_id` / `.tokenizer_revision` | `a5beb1e3e68b9ab74eb54cfd186867f64f240e1a` | Draws chunk boundaries. Fixed across all 8 runs. |
| `Qwen/Qwen2.5-7B-Instruct` | `retrieval.budget_tokenizer_id` / `.budget_tokenizer_revision` | `a09a35458c702b33eeacc393d103063234e8bc28` | Measures the context budget. Fixed across all 8 runs. |

### I3 — One hashing path

Every id, digest and cache key comes from [`src/ragbench/hashing.py`](src/ragbench/hashing.py).
Do not add a second hashing path, do not call `hashlib` directly outside that module, and
do not use Python's builtin `hash()` for anything persisted — it is salted per process.

### I4 — The corpus is frozen

Corpus selection queries NCBI **once**, then writes a manifest whose digest is pinned into
`configs/corpus.yaml` as `manifest_sha`. PMC grows continuously, so an unpinned query is
not reproducible. After freezing, every stage reads the manifest and **never queries NCBI
again**.

### I5 — Gold labels are character spans, never chunk ids

A gold passage is `(pmcid, char_start, char_end)` into `ParsedPaper.body`, plus the
question, the answer and the section it came from. It is **never** a chunk id.

Chunk ids are arm-specific. `PMC10045805-0007` names different text in the `fixed` and
`recursive` chunk sets, so a gold set labelled with chunk ids would be two different gold
sets wearing one name, and the RQ1 comparison it exists to support would be comparing each
arm against its own private notion of correct. The body stream is the one representation
both arms share, which is exactly why the labels live there.

Per-arm relevant chunks are **derived at eval time** by offset overlap against whichever
chunk set is loaded. Nothing persists them.

> A function that stores, caches or accepts a gold chunk id is a bug, however convenient.

The primary retrieval metric is **span coverage**: the fraction of a gold span's characters
present in the retrieved context. Recall@k and nDCG@10 are secondary and reported for
comparability with the literature, not relied on. Their denominator is the number of
chunks *that arm* needs to hold the span, so the two arms are not asked the same question —
and which arm the bias favours is not fixed, it follows whichever arm's boundaries align
with the unit the gold spans were drawn from. Measured on this corpus: gold spans are prose
paragraphs, the recursive arm splits on paragraphs, so recursive covers all 20 spans in one
chunk while fixed needs two for 6 of them. Here Recall@k flatters the *finer* arm; sample
the spans differently and it would flatter the coarser one. Span coverage is
granularity-neutral by construction: it asks whether the generator can see the answer,
which is the thing retrieval is for.

---

## The design

8 runs = the Cartesian product of [`configs/factors.yaml`](configs/factors.yaml):

| Factor | Level `a` | Level `b` |
|---|---|---|
| `chunking` | `fixed` | `recursive` |
| `embedding` | `bge` — `BAAI/bge-base-en-v1.5`, no adapter, query prefix `"Represent this sentence for searching relevant passages: "` | `specter2` — `allenai/specter2_base` + adapter `allenai/specter2`, no query prefix |
| `rerank` | `off` | `on` — `BAAI/bge-reranker-base` |

The `bge` query instruction is applied **at query time only, never to documents**; `specter2`
is symmetric and takes no prefix.

Everything else is held fixed in [`configs/base.yaml`](configs/base.yaml) and may not be
overridden anywhere except by a factor level: 512-token target chunks with 0 overlap,
normalized embeddings, greedy decoding (`temperature: 0.0`) from Qwen2.5-7B-Instruct at
AWQ, and a pinned OpenRouter judge (`meta-llama/llama-3.3-70b-instruct`, rubric `v1`).

Adding a level to `factors.yaml` changes the experiment size and nothing else needs
editing anywhere in the codebase. Keep it that way — never hard-code the number 8.

Pipeline stages, in order:

```
ingest → chunk → index → retrieve → generate → judge → report
```

`gold` is a command, not a stage. The evaluation set — 20 hand-verified questions with
character-span labels ([`configs/gold.yaml`](configs/gold.yaml), pinned by `gold_set_sha`) —
is an *input* to `retrieve`, built once and frozen the way the corpus manifest is. Making it
a stage would imply it is rebuilt per run, which is what freezing exists to prevent. It is
also why `resolve_config` reads four files, not three: a result scored against a different
set of questions is a different result, however identical every other setting.

---

## Parse policy

Applied during `ingest` when converting JATS XML to `ParsedPaper.body`:

- **Drop** reference lists and bibliographic cross-references.
- **Drop** figure captions.
- **Tables** → replace with `[TABLE: <label>]`, using the table's own label
  (e.g. `[TABLE: Table 3]`).
- **Display equations** → replace with `[EQUATION]`.
- **Inline math** → keep as plain-text / LaTeX source, inline in the body stream. Do not
  placeholder it; it carries meaning mid-sentence.
- **Keep** the abstract — in `ParsedPaper.abstract`, which is *not* part of the body
  stream and is *not* chunked (`chunking.chunk_abstract: false`). Abstracts exist here to
  draft questions from and to check drafted questions against; they are not retrievable.
  An abstract near-duplicates its own body, so indexing both would put two correct
  passages in the index for one gold span, and abstract-level retrieval is specter2's
  training task, which would favour one embedding arm for reasons unrelated to the
  experiment.

The `body` is a single concatenated stream; `ParsedPaper.sections` maps back into it by
character offset. Both chunkers operate on that one stream.

Record the applied policy and its effects in `ParsedPaper.parse_metadata`, per paper: counts
of tables and equations placeholdered, sections dropped, and total retained character
length. These numbers get reported — they are evidence the corpus is what it claims to be.

---

## Reproducibility

- **Seeds are fixed** (`seed: 20260813` in `base.yaml`, mirrored in `generation.seed`). Any
  stochastic step reads a seed from config; nothing calls an unseeded RNG.
- **All ids derive from `hashing.py`** (see I3). Config hashes are order-independent, so
  reordering a YAML mapping must not change a run id.
- **Caches are invalidated by version stamps** in
  [`src/ragbench/constants.py`](src/ragbench/constants.py). Bump `PARSER_VERSION` when
  ingest changes the text it produces; bump `CHUNKER_VERSION` when a chunker changes how it
  draws boundaries. A bump forces a rebuild instead of silently mixing old and new
  artefacts. **Changing behaviour without bumping the stamp is a bug.**
- **Every stage is resumable and idempotent.** Stages append JSONL keyed by a stable id;
  re-running a completed stage does near-zero work, and interrupting one mid-way and
  re-running it continues rather than restarting.
- Each stage writes into a run/cache directory whose name derives from the resolved config
  hash, and dumps the resolved config next to its outputs. A run is self-describing.
- **Network access comes in two categories, governed by different rules.** Conflating
  them is how an experiment stops being reproducible while every stage still looks
  well-behaved.

  **Data fetches** (NCBI esearch/efetch) happen **only in `ingest`**, and only under the
  `network` pytest marker. Nothing downstream may touch the network for data — if a later
  stage needs a paper, it came from the manifest or a cache. The corpus is a frozen set of
  facts and freezing it is what makes it reproducible (I4).

  **Model-artefact fetches** (tokenizers, embedding and reranking checkpoints, the
  generator) are *not* confined to `ingest`. They happen wherever a model is first needed,
  they are cached by the HF hub, and they are *expected* to happen again on Kaggle or
  Colab, where nothing local is present. So what makes them reproducible is not *when*
  they happen but *what they resolve to*:

  - **Pin a revision, never a bare id.** A Hub id is a mutable pointer: the repo behind
    `BAAI/bge-base-en-v1.5` can gain a commit, and a tokenizer that re-segments one word
    re-chunks the corpus. Every model artefact is addressed by `<thing>_id` **and**
    `<thing>_revision`, the 40-character commit sha. `HuggingFaceTokenizer` refuses to
    construct without one rather than defaulting to `main`.
  - **A revision that can change an artefact belongs in that artefact's cache key.**
    `chunking.tokenizer_revision` is in `CHUNKING_KEY_FIELDS`, so re-pinning it builds a
    new chunk set instead of silently re-drawing the boundaries under the old id.
  - The two pinned tokenizers are in the I2 table above. `embedding.model_id`,
    `rerank.model_id` and `generation.model_id` must each gain a `_revision` — and
    `index_key` must key on it — when those stages are built.
  - A model fetch still never happens on the CPU smoke path: the stand-ins (`whitespace`
    and friends) are selected by id and download nothing.

---

## Execution environment

Authored **locally on CPU** (Windows, Python 3.11); the GPU stages — embedding, reranking,
generation — run on **Kaggle or Colab**.

Therefore: **every GPU-dependent component sits behind an interface**, with a tiny CPU
stand-in implementation. The full pipeline must be smoke-testable end to end on a laptop
with no GPU and no large model download. Code that imports torch at module scope, assumes
`cuda` is available, or can only run with a 7B model loaded is not acceptable.

`import ragbench` is deliberately stdlib-only and must stay that way, so CLI startup and
the CPU path never drag in a GPU dependency.

---

## Out of scope for v1 — do not build

Not "not yet" — **not in this project**. If one of these seems necessary, say so and stop;
do not implement it.

- Web UI, chat interface, or anything conversational
- FastAPI / any HTTP server
- Docker / containerisation
- Agentic retry loops, self-correction, or multi-step tool use in the RAG path
- Semantic, cluster-based, or LLM-driven chunking (the two chunkers are the factor)
- Metadata-aware or filtered retrieval
- Query rewriting / expansion / HyDE

Retrieval is dense + optional cross-encoder rerank. Generation is one deterministic call to
one pinned model. That is the whole system.

---

## Conventions

- Python 3.11. Ruff config lives in `pyproject.toml` (line length 100, `E,F,I,UP,B`); run
  `ruff check src tests` before committing.
- **Inter-stage data uses only the record types in
  [`src/ragbench/types.py`](src/ragbench/types.py).** If a field is missing, propose a change
  to `types.py` and get it approved — never invent a parallel structure alongside it.
- Small, single-purpose modules. Nothing over ~200 lines.
- Tests live in `tests/`, mirroring the package layout. Parse tests run offline against a
  small committed JATS fixture. Network tests carry the `network` marker and are deselected
  by default; model-downloading tests carry `slow`.
- Do not add dependencies without asking first.
