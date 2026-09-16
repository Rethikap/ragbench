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

Every model artefact is pinned by revision, and there are five. The three that make
vectors:

| Artefact | Config keys | Pinned revision | Role |
|---|---|---|---|
| `BAAI/bge-base-en-v1.5` | `embedding.model_id` / `.model_revision`, level `bge` | `a5beb1e3e68b9ab74eb54cfd186867f64f240e1a` | Embedding arm A. The same repo as the chunk tokenizer, and a different use of it. |
| `allenai/specter2_base` | `embedding.model_id` / `.model_revision`, level `specter2` | `3447645e1def9117997203454fa4495937bfbd83` | Arm B's encoder. **Not the arm on its own.** |
| `allenai/specter2` | `embedding.adapter_id` / `.adapter_revision` | `2081559630a80fc5851d8f798a05ba81e9468089` | Arm B's **proximity adapter** — what SPECTER2's retrieval results were measured with. `allenai/specter2_adhoc_query` is a different adapter for a different task. |

And the two tokenizers, never interchangeable with each other or with the above:

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

### I4b — Four indexes, and the embedder may not reach the chunker

The 8 runs share **two chunk sets** (I2) and **four indexes**: two chunk sets × two
embedding arms. `index_key` takes `chunk_set_id` as an opaque string, which is what keeps
the two levels independent — the embedder cannot see how chunks were cut, so swapping it
produces a new index over the *same* chunk set. `embedding.arm_params` reads
`base.embedding` and `factors.embedding` only, mirroring what `chunking.arm_params` does.
The two factors meet for the first time in the index id, and they meet there as two strings.

> A chunk-set id that changes when the embedder changes is the same bug as I2, one level up.

**The specter2 arm is the base encoder plus its activated proximity adapter.**
`allenai/specter2_base` alone is a different model and would measure something the SPECTER2
paper never reported, while every log line still said "specter2". `AdapterEmbedder` refuses
to construct if activation did not take, because a silently inactive adapter is precisely
the failure that leaves no trace in the results.

Documents and queries go through **separate methods**. `bge` prefixes a query with an
instruction and never a document; `specter2` is symmetric and takes no prefix. A single
`encode` method would make prefixing a document possible by accident, which corrupts every
vector in an index while the run still looks healthy.

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

### I6 — The generator does not write its own evaluation questions

Questions are drafted by an author other than the system under test, recorded per candidate
in `drafted_by`. There is **no** generator-drafted path in `gold/draft.py`, and this is a
decision, not a gap to be filled later: a model asked to write the questions it will be
scored on writes them in its own idiom, and then answers them well partly because they
sound like it. Hand-verification does not remove that — the questions a verifier sees are
already drawn from the generator's distribution.

The gold set as it stands was drafted by **claude-opus-5, manual local CPU session**,
working to the pinned prompt `gold.draft_prompt_id: v1` against seeded passage samples, and
is verified question-by-question by the author. That belongs in the methodology section of
the write-up, not in a footnote.

**The answer must be a finding, not the provenance of a method.** A result, a measured
relationship, a claim, or a design choice that changes how a result is read — not an
instrument or its settings, not a reagent or its supplier, not a catalogue number, not a
software version, not animal housing, not a bare count of samples.

This is a measurement requirement, not a matter of taste. A provenance answer ("a Hitachi
H7600 at 80 kV") is retrieved by near-verbatim string match under every configuration, so
all 8 runs find it equally and the question discriminates between nothing. Nine of the
first twenty questions were provenance, and the cause was a filter rule: "reject an answer
with no corpus-rare token" selects *for* distinctive literal strings, and the most
distinctive strings in a paper are catalogue numbers, model numbers and version strings.
The goal was right and the proxy was backwards. The check now tests recoverability
directly — is this answer already in the rest of the corpus, or already in the question? —
and never rewards a rare literal. `methods_provenance` is a fourth rejection category
beside it.

Two corollaries, each learned by a bad question surviving review:

- **Counts of findings are findings; counts of inputs are provenance.** "A core group of 48
  proteins consistently enriched in plaques" is a discovered quantity. "648 individuals",
  "49 samples after filtering", "112 nerves from 56 rats" describe what went in, and are
  retrieved by the same near-verbatim match as a catalogue number. The surface form is
  identical — a number beside a noun — so the rule is carried by the noun, in a configured
  list from which "cells", "lesions" and "proteins" are deliberately absent.
- **The answer must be a positive claim the paper asserts, not a described non-effect.** A
  null result is a legitimate finding in science and an unusable gold answer here: a model
  answering "NfL was not significantly affected" is scientifically right and will not match
  a reference answer phrased the other way round, so the question ends up scoring the
  judge's tolerance for hedging rather than retrieval quality. The check is deliberately
  narrow — a *significance retraction* in a span where no sentence asserts an unretracted
  result — because plain negation is usually a paper asserting something: a null contrasted
  with a significant result, an absence that is half the finding, the control arm of an
  effect.

Passages are sampled from Results and Discussion first, for the same reason: a uniform draw
over a paper's paragraphs is mostly a draw over its Methods section. Methods passages stay
eligible in the last tier, because a positivity threshold or a set of covariates is worth
asking about; distinguishing that from equipment identity is the judgement the checks
cannot make, so a Methods passage with no result language raises a *warning* for the
verifier rather than an auto-rejection.

**Topic is a gate, section kind is a tier, and the difference is not stylistic.** A paper
scoring below `gold.min_topic_terms` is not sampled at all. It was once the first half of a
tier key, which meant an off-topic paper was still drawn whenever the on-topic pool ran
short — and four off-topic questions (cardiac echocardiography, hidradenitis suppurativa,
CNN morphometry, a glioma line) reached a set that had already been reviewed. A soft
preference expressed as ordering is only a preference. Papers already written about are
exempt from the gate, because their records carry decisions that must stay readable; they
are stopped at *selection* instead, where a below-threshold candidate needs
`"off_topic_override": true` **and** a note saying why the score is wrong. `gold freeze`
refuses an override with no note, because an override with no stated reason is
indistinguishable from an oversight.

The score is a proxy and it is wrong in both directions, which is what the override is for:
one selected question (`q021`) comes from a paper scoring 2 whose title is *"...Shared
Between Alzheimer's Disease and Temporal Lobe Epilepsy"*. Two caps, not one, follow from
the same split: `candidate_passages_per_paper` bounds what a paper may *offer*,
`max_per_paper` bounds what may be *selected* from it. The independence argument is about
the gold set, not the pool.

Two further rules follow, and both are enforced rather than documented:

- **`selected` and `verified` are separate fields.** Selection is editorial — this
  candidate is proposed for the set. Verification is a claim that a human read the
  question, the answer and the span and found them right. Collapsing them into one flag is
  how a gold set gets frozen claiming a verification that never happened.
- **`gold freeze` refuses while any selected question is unverified**, naming each one, the
  same way it refuses a stand-in draft.

**The span is the minimal evidence — the sentence or two that answer the question — not
the paragraph it was drafted from.** The paragraph is kept alongside as `context_start` /
`context_end`, for provenance; no metric reads it, and `GoldSpan` refuses to construct if
the evidence is not inside its context.

This is a correction, not a refinement. The first cut labelled whole paragraphs (median 555
chars), and a paragraph is exactly what the recursive chunker splits on — so recursive
covered 20/20 spans in a single chunk *by construction*, and the chunking effect could not
be told apart from the sampling unit. Narrowing to minimal spans (median 212 chars) moved
fixed from 1.30 chunks per span to 1.10, and 6/20 spans needing two chunks to 3/20.

The primary retrieval metric is **span coverage**: the fraction of a gold span's characters
present in the retrieved context. Recall@k and nDCG@10 are secondary and reported for
comparability with the literature, not relied on. Their denominator is the number of chunks
*that arm* needs to hold the span, so the two arms are not asked the same question.

**Coverage saturates on the current gold set, and three more metrics carry RQ1 through it.**
Every gold span is short enough that both arms hold it in a single chunk, so coverage,
Recall@k and nDCG@10 are all 1.0 for both. That is the metric running out of room, not a
finding that chunking has no retrieval effect: the arms retrieve the *same span* inside
*different context*, and coverage is blind to the difference by design. What differs is the
window, measured by [`src/ragbench/eval/context.py`](src/ragbench/eval/context.py):

| Metric | What it asks | Why it discriminates |
|---|---|---|
| `evidence_density` | gold characters ÷ all retrieved characters | precision at the budget; a 200-char answer in a 512-token chunk is a different prompt from the same answer in a 180-token one |
| `gold_chunk_rank` | rank of the gold-bearing chunk, **and its token offset** from the window start | position drives attention, and the offset for a given rank is a function of the arm's chunk size |
| `distractor_count` | chunks in the window that miss the span | the budget is constant (I1), so a finer arm fits more chunks in it — more context or more noise is exactly RQ1 |

All three are computed at the real 2000-token budget under `stop_at_overflow`. Ranking
quality is held fixed while retrieval does not exist, so what the report shows is the
geometry each arm imposes, not a prediction of what a retriever will rank.

A residual asymmetry survives narrowing, and it is real rather than an artefact. Measured
against two null models over the same span lengths (so chunk size is controlled), the share
of spans needing more than one chunk is:

| arm | mean chunk | observed | null: span anywhere in body | null: span inside a paragraph |
|---|---|---|---|---|
| `fixed` | 2121 chars | 15% (3/20) | 9.8% | 9.4% |
| `recursive` | 1612 chars | 0% (0/20) | 12.9% | 0.3% |

Read it this way. The observed rates match the in-paragraph nulls for both arms, so the 20
spans are not special — nothing here is a property of which questions were picked. `fixed`
is indifferent to paragraph structure: putting a span inside a paragraph does not help it
(9.8% → 9.4%). `recursive` has *smaller* chunks and therefore more boundaries per character
— hence its **higher** uniform rate — yet splits a paragraph-internal span 40× less often,
because its boundaries and the spans both follow the document's paragraph structure.

**State that as what it is, and no more.** Every gold span lies inside a single paragraph,
because passages are sampled as paragraphs, and `recursive` splits on paragraphs. So
**within-paragraph spans favour `recursive` at the retrieval stage by construction**:
on this gold set it cannot lose, and the 0% is a fact about the labelling unit meeting the
chunker's unit, not a demonstration that paragraph-aligned chunking retrieves better in
general. Whether that retrieval advantage converts into better *answers* is not settled
here — that is what the generation and judge metrics test, and they are where a claim about
which chunker is better has to be made.

> **Scope limit of the gold set.** It measures *within-paragraph* retrieval only. It cannot
> exhibit the case where an answer straddles a paragraph boundary, which is where
> `recursive` would pay. Report retrieval results as conditional on that; do not generalise
> them to multi-paragraph answers.

> **Future work — a v2 gold set stratified for paragraph-straddling spans. Do not build
> this now.** Every span in the current set lies inside one paragraph, so it measures
> *within-paragraph retrieval only*, and that is the regime in which the chunking arms
> agree: both hold the span in one chunk, and coverage is 1.0 for both. The arms diverge
> exactly where a span crosses a paragraph boundary — `recursive` splits there by
> construction and would need two chunks, `fixed` would need two only when its own window
> happens to land on the span. A v2 set would stratify deliberately: a stated proportion of
> spans whose evidence crosses a paragraph boundary, sampled as such rather than found by
> accident, and reported as a separate stratum so the within- and across-paragraph regimes
> are never averaged together. That is where coverage would discriminate again. Until it
> exists, retrieval results from this set are conditional on the within-paragraph regime and
> must be reported that way.

> **Corpus drift — a limitation of the frozen corpus, to be reported as one.** The frozen
> query matched `"alzheimer" AND biomarker` as free text, which admits papers that merely
> mention Alzheimer's: a glioma cell line, a rat sciatic nerve, Drosophila, cardiac
> echocardiography. Measured over title and abstract against the topic terms in
> `configs/gold.yaml`, **51 of the 100 papers carry fewer than 3 topic terms, and 11 carry
> none at all.** The corpus is frozen and is *not* re-queried (I4) — an unpinned re-query
> is not reproducible, and re-freezing would invalidate every artefact downstream of
> `manifest_sha`. The drift is handled where it can be: gold passages are drawn from
> on-topic papers first, each candidate records its `topic_score`, and this paragraph goes
> in the limitations section. A v2 corpus would use PMC field tags rather than free text.

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

> **The residual truncation is a consequence of I2, not a defect — and it is priced.**
> `embedding.max_seq_tokens: 512` is the encoder's position limit and *includes* `[CLS]` and
> `[SEP]`, so a chunk has room for 510 content tokens; `chunking.target_tokens` is 510 to
> match. That closes the arithmetic half of the problem: at 512 the two disagreed by exactly
> the two special tokens and **93.3% of the fixed arm's chunks lost their tail while only
> 1.9% of the recursive arm's did** — an arm-asymmetric defect produced by an off-by-two.
> At 510, truncation under the canonical tokenizer is **zero in both arms**.
>
> What remains is structural and cannot be closed without giving up something better.
> Boundaries are drawn **once, with one canonical tokenizer** — that is what makes the 8 runs
> share two chunk sets instead of four, and it is the whole of I2. The price is that the
> *other* arm's tokenizer is free to make more tokens of the same text:
>
> | chunk set | arm | mean tokens | max | truncated | cause |
> |---|---|---|---|---|---|
> | `fixed` | bge (canonical) | 495.0 | 510 | **0** | — |
> | `fixed` | specter2 | 449.4 | **516** | 4 / 1574 (0.2%) | cross-tokenizer expansion |
> | `recursive` | bge (canonical) | 377.1 | 510 | **0** | — |
> | `recursive` | specter2 | 342.3 | **512** | 1 / 2066 (0.1%) | cross-tokenizer expansion |
>
> **specter2 makes up to 516 tokens where the canonical tokenizer makes 510** — about 1.2%
> more on the worst chunk. Bounding that would mean dropping `target_tokens` to roughly 500,
> which spends 10 tokens of context on all ~3,640 chunks to rescue 5. That trade is not
> worth taking, and the methodology section should state it with these numbers rather than
> claim the pipeline truncates nothing. Every index logs its own census in `index.json`, so
> the figure is carried by each run and not by this paragraph.

Pipeline stages, in order:

```
ingest → chunk → index → retrieve → generate → judge → report
```

`gold` is a command, not a stage — `build`, then `sheet`, then `freeze`. The evaluation set
— 20 questions with minimal-evidence character-span labels
([`configs/gold.yaml`](configs/gold.yaml), pinned by `gold_set_sha`) — is an *input* to
`retrieve`, built once and frozen the way the corpus manifest is. Making it a stage would
imply it is rebuilt per run, which is what freezing exists to prevent. It is also why
`resolve_config` reads four files, not three: a result scored against a different set of
questions is a different result, however identical every other setting.

Everything a human decided lives in one committed file,
[`configs/gold_drafts.jsonl`](configs/gold_drafts.jsonl): the question, the answer, the two
anchors that narrow the label to its evidence, whether the candidate is selected, why it was
rejected if not, and whether it has been verified. Spans are authored as **anchors**, never
as integers — an offset typed by hand goes stale silently, an anchor that stops matching is
an error at load time. Everything else about the gold set is derived from that file plus the
seed.

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
- **A parser change must precede any freeze, and it will move more than it looks like it
  moves.** Stripping brackets left empty by citation removal — 3,863 of them, in 80 of the
  100 papers, about 0.3–0.8% of each affected body — shifted every character offset after
  the first change in a paper and changed *both* chunk sets:

  | arm | chunks | papers that moved | shape |
  |---|---|---|---|
  | `fixed` | 1,586 → 1,568 (−18) | 18 | every one exactly −1 |
  | `recursive` | 2,086 → 2,061 (−25) | 22 | 19 at −1, 3 at −2 |

  The asymmetry is worth stating because the intuition runs the wrong way. The *finer,
  structure-aware* arm moved more, not less. `fixed`'s boundaries depend only on a paper's
  total token count, so removing characters can delete a trailing window and nothing else —
  arithmetic, uniform, never more than one chunk per paper. `recursive`'s boundaries depend
  on whether each *paragraph* fits the target, so removing characters can carry a paragraph
  back across the 512-token threshold and stop it being split at all: four did exactly
  that, and sentence-level (`". "`) chunks fell from 238 to 230. A text edit that is
  arithmetic for one arm is structural for the other.

  Nothing downstream of a parse may be frozen before the parse is settled. Related:
  `Passage.passage_id` is content-addressed (`pmcid:<digest of the passage text>`) rather
  than offset-addressed, so a parser change re-keys only the passages whose own text it
  alters instead of orphaning the whole hand-verified gold set.

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
generation — run on **Kaggle or Colab**. The operational runbook for that is
[`docs/kaggle.md`](docs/kaggle.md): what travels, what comes back, and how to tell a
resumed run from a restarted one.

One environment constraint reaches the whole project from there: `adapters~=1.3`, which
the specter2 arm needs, requires `transformers~=4.57.6`. Installing `.[specter]`
downgrades transformers, and that is correct — the bge arm and the reranker run on 4.57
too. It is recorded in `pyproject.toml` rather than discovered on the GPU host.

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
