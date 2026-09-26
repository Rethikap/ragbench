# Running the GPU stages on Kaggle

Written for: whoever is operating the Kaggle session. Assumes a fresh notebook
with a GPU, no local state, and a session that may die mid-run.

The GPU stages are `index` (embed ~3,640 chunks into four vector indexes),
`retrieve` (eight configurations × 20 queries) and `generate` (160 answers from
Qwen2.5-7B-Instruct at AWQ). Everything before them — selection, ingest,
chunking, the gold set — is already frozen and comes with the repository.
Nothing on Kaggle touches NCBI.

**They are two sessions, not one.** §§1–8 cover indexing and retrieval; §9
covers generation, in a fresh notebook. The split is not organisational: the
specter2 arm needs `adapters`, which pins `transformers` to 4.57.x, and vLLM
carries its own transformers range. One environment cannot satisfy both, and the
failure if you try is silent.

**`judge` is not here, and does not need to be.** It calls a hosted API, uses no
GPU, and runs from the laptop against `runs/<id>/generate/` once that comes
back — see §10.

---

## 0. What travels, and what does not

`index` and `retrieve` read **the chunk sets and the gold set, and nothing else**.
They never open a parsed paper or a raw JATS file, so those 50 MB stay at home.
`generate` reads the same chunk sets plus what `retrieve` wrote — it does not
re-retrieve, and needs no index and no embedder.

| Goes to Kaggle | Size | Where from |
|---|---|---|
| the repository, including `configs/` | ~1 MB | `git clone` |
| `data/chunks/d496939bdf79/` — the `fixed` chunk set | 3.7 MB | Kaggle Dataset |
| `data/chunks/cb01541124d3/` — the `recursive` chunk set | 3.9 MB | Kaggle Dataset |

Those two ids are the current chunk sets. Confirm before uploading — a
`CHUNKER_VERSION` bump or a `chunking.*` edit changes them:

```bash
python - <<'PY'
import sys; sys.path.insert(0, "src")
from pathlib import Path
from ragbench.config import resolve_config
from ragbench.cache_keys import chunk_set_key
from ragbench.chunking.pipeline import arm_params
r = resolve_config(Path("configs/base.yaml"))
for level in r["factors"]["chunking"]:
    print(level, chunk_set_key(r["corpus"]["manifest_sha"], arm_params(r, level)))
PY
```

`data/chunks/` may hold stale directories from earlier versions. Upload only the
two the command prints.

**Make the dataset** (locally, then upload at kaggle.com/datasets → New Dataset):

```bash
mkdir -p /tmp/ragbench-chunks
cp -r data/chunks/d496939bdf79 data/chunks/cb01541124d3 /tmp/ragbench-chunks/
```

Name it `ragbench-chunks`. It mounts read-only at
`/kaggle/input/ragbench-chunks/`.

---

## 1. Notebook settings

- **Accelerator**: GPU T4 ×2 (or P100). Either is enough; nothing here needs two.
- **Internet**: **On**. Required to clone and to pull model weights. If it cannot
  be enabled, see §3b.
- **Persistence**: leave "Files only" off. Output is captured by *Save Version*,
  which is what §7 depends on.

---

## 2. Clone and install

```python
%cd /kaggle/working
!git clone https://github.com/<you>/ragbench.git
%cd /kaggle/working/ragbench
!pip install -q -e ".[specter]"
```

Kaggle's GPU sessions run **Python 3.12**, which `requires-python` allows
(`>=3.11,<3.13`). The upper bound is `adapters`, which publishes no 3.13
classifier; on 3.13 the specter2 arm would not install. Cache ids are identical
on 3.11 and 3.12 — blake2b over canonical JSON, never Python's salted builtin
`hash()` — so the four index ids in §4 are the same numbers on either
interpreter, and the preflight census compares against them safely.

`[specter]` is not optional here — it is what makes the specter2 arm exist, and
it **pins `transformers` to 4.57.x**, because `adapters~=1.3` requires it.
Kaggle's image ships a different transformers; let pip downgrade it. The bge arm
and the reranker run happily on 4.57 too.

> **`[specter]` and `[generate]` must not share a session.** The generate stage
> needs vLLM, which carries its own `transformers` range; `adapters~=1.3` pins
> transformers to 4.57.x. Installing both leaves whichever ran last in place and
> silently breaks the other. They never need to coexist: **indexing and
> retrieval are one session, generation is another**, and the only thing that
> travels between them is `runs/562c4bb23747/retrieve/` — under 100 KB. Start a
> fresh notebook for §9 rather than adding vLLM to this one.

Restart the kernel after the install so the downgraded transformers is the one
that gets imported. Then:

```python
%cd /kaggle/working/ragbench
!python -c "import transformers, adapters; print(transformers.__version__, adapters.__version__)"
```

Expect `4.57.x 1.3.x`. Anything else and the specter2 arm will fail later, at the
adapter load, after you have already paid for the bge indexes.

### Paths

`ragbench` takes `--data-root` (default `data`) and `--runs-root` (default
`runs`), both relative to the working directory. Put the chunk sets where the
default expects them:

```python
!mkdir -p /kaggle/working/ragbench/data/chunks
!cp -r /kaggle/input/ragbench-chunks/* /kaggle/working/ragbench/data/chunks/
!ls /kaggle/working/ragbench/data/chunks
```

Point the HuggingFace cache at working storage so a *Save Version* captures the
weights and a later session can reuse them:

```python
import os
os.environ["HF_HOME"] = "/kaggle/working/hf"
```

---

## 3. Getting the model artefacts down

Five pinned artefacts. Fetching them up front, in one cell, means a failure
happens in the first two minutes rather than twenty minutes into an embed.

```python
from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification

PINS = {
    "BAAI/bge-base-en-v1.5":      "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a",
    "allenai/specter2_base":      "3447645e1def9117997203454fa4495937bfbd83",
    "BAAI/bge-reranker-base":     "2cfc18c9415c912f9d8155881c133215df768a70",
}
for repo, rev in PINS.items():
    AutoTokenizer.from_pretrained(repo, revision=rev)
    print("tokenizer ok:", repo)

AutoModel.from_pretrained("BAAI/bge-base-en-v1.5", revision=PINS["BAAI/bge-base-en-v1.5"])
AutoModel.from_pretrained("allenai/specter2_base", revision=PINS["allenai/specter2_base"])
AutoModelForSequenceClassification.from_pretrained(
    "BAAI/bge-reranker-base", revision=PINS["BAAI/bge-reranker-base"])

# The budget tokenizer. Tokenizer files only -- this does NOT pull the 15 GB model.
AutoTokenizer.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct", revision="a09a35458c702b33eeacc393d103063234e8bc28")
print("all artefacts present")
```

Roughly 2 GB, two to four minutes on Kaggle's connection.

The **proximity adapter** (`allenai/specter2`, revision `2081559630a80fc5851d8f798a05ba81e9468089`)
is fetched by `adapters` at index time, not by `transformers`. It is a few MB.

> **Why the adapter matters.** `allenai/specter2_base` alone is *not* SPECTER2 for
> retrieval — the proximity adapter is what the paper's retrieval results were
> measured with. `AdapterEmbedder` proves the adapter is in the forward pass by
> encoding a probe twice, once with it deactivated, and refusing if the two
> embeddings match.
>
> **Each of the two specter2 indexes should print exactly one line like this as
> the embedder is built** — read it, do not just look for the absence of errors:
>
> ```
> adapter probe: PASS ('proximity' changes the forward pass; active vs.
> inactive embedding L2 distance = <a number>)
> ```
>
> `embedding.normalize` is on, so both vectors are unit length and the distance
> runs 0–2. No expected value is quoted here because none has been measured yet
> — record what the first run prints and compare later runs against it. What to
> react to is the *order of magnitude*: a distance that is merely nonzero
> (1e-6, say) passes the check but is worth stopping for, because the adapter
> would then be contributing nothing the results could attribute to it. If
> instead you see
>
> ```
> ValueError: adapter 'proximity' is loaded but does not change the model's
> output (L2 distance 0 between the active and deactivated embeddings), so it
> is not in the forward pass.
> ```
>
> the arm is misconfigured — do **not** work around it. The alternative is four
> plausible-looking indexes, one of which is base SPECTER2 with no adapter.
>
> An earlier version checked `model.active_adapters` instead and passed while
> nothing was active, because that attribute is a bound method on every
> `PreTrainedModel` and therefore always truthy. The `adapters` library's own
> "there are adapters available but none are activated" warning is silenced for
> the probe's deactivated pass only — that pass is the check working. Seeing it
> anywhere else still means something is wrong.

### 3b. If the Hub is unreachable from the notebook

Internet disabled, or an outage. Build a weights dataset once from a machine that
can reach the Hub:

```bash
export HF_HOME=/tmp/hf
python - <<'PY'
from huggingface_hub import snapshot_download
for repo, rev in [
    ("BAAI/bge-base-en-v1.5",  "a5beb1e3e68b9ab74eb54cfd186867f64f240e1a"),
    ("allenai/specter2_base",  "3447645e1def9117997203454fa4495937bfbd83"),
    ("allenai/specter2",       "2081559630a80fc5851d8f798a05ba81e9468089"),
    ("BAAI/bge-reranker-base", "2cfc18c9415c912f9d8155881c133215df768a70"),
]:
    snapshot_download(repo, revision=rev)
snapshot_download("Qwen/Qwen2.5-7B-Instruct",
                  revision="a09a35458c702b33eeacc393d103063234e8bc28",
                  allow_patterns=["*.json", "*.txt", "tokenizer*", "vocab*", "merges*"])
PY
```

Upload `/tmp/hf/hub` as a dataset named `ragbench-weights`, then in the notebook:

```python
import os
os.environ["HF_HOME"] = "/kaggle/input/ragbench-weights"
os.environ["HF_HUB_OFFLINE"] = "1"
```

Offline mode resolves pinned revisions out of the cache, so the pins still hold.
You also need the repo itself without `git clone`: upload it as a second dataset
and `pip install -e` from there.

---

## 4. Preflight — 30 seconds, before spending any GPU

```python
!python -m ragbench.cli index --config configs/base.yaml --census-only
```

This loads each arm's **tokenizer and not its weights**, so it is fast, and it
proves the chunk sets are present and readable and the pins resolve. Expect four
index ids and this table:

```
  index_id      embedding    mean tok  max tok  limit  truncated   share  worst over
  208323cba75a  bge             495.0      510    510          0    0.0%           0
  4b922d7b4802  specter2        449.4      516    510          4    0.2%           6
  c43a26f32cf4  bge             377.1      510    510          0    0.0%           0
  09222c7a0950  specter2        342.3      512    510          1    0.1%           2
```

Then confirm the frozen gold set is intact:

```python
!python -c "import sys; sys.path.insert(0,'src'); \
from pathlib import Path; from ragbench.config import resolve_config; \
from ragbench.gold.freeze import verify_frozen, GOLD_SET_FILENAME; \
r = resolve_config(Path('configs/base.yaml')); \
print(len(verify_frozen(Path('configs')/GOLD_SET_FILENAME, r['gold']['gold_set_sha'])), 'questions verified')"
```

**Stop and fix if:** the index ids differ from the four above (the chunk sets or
the config are not the ones this document was written against), the bge rows show
non-zero truncation (`chunking.target_tokens` and `embedding.max_seq_tokens`
disagree), or the gold set does not verify.

---

## 5. The run

```python
!python -m ragbench.cli index --config configs/base.yaml
```

Builds four indexes: `fixed×bge`, `fixed×specter2`, `recursive×bge`,
`recursive×specter2`. Then:

```python
!python -m ragbench.cli retrieve --config configs/base.yaml
!python -m ragbench.cli report retrieval --config configs/base.yaml
```

`retrieve` covers all eight configurations. `report retrieval` writes
`runs/562c4bb23747/retrieval_report.json` and prints the two tables.

Generation is **not** part of this session — see §9.

### Expected wall-clock

| Stage | Expected | Investigate past |
|---|---|---|
| install + restart | 2–4 min | 10 min |
| artefact download (§3) | 2–4 min | 15 min |
| `--census-only` | 20–40 s | 3 min |
| `index`, all four | 6–15 min total | 40 min |
| `retrieve`, all eight | 2–6 min total | 20 min |
| `report retrieval` | < 30 s | 3 min |

`index` prints a per-batch progress line. If it is not moving, the likely causes
are that the GPU is not attached (check `torch.cuda.is_available()` — the
embedder falls back to CPU silently and is then roughly 20× slower) or the
adapter download is stalled.

If construction raises `model tensors are split across devices [...]`, something
was added to the model after it was placed and did not follow. That check exists
because the first version of the specter2 arm loaded its adapter *after* moving
the base model to the GPU, leaving the adapter's weights on CPU; the symptom was
a `RuntimeError` about `mat1` several frames deep in a matmul.

The four indexes are ~1,574 and ~2,066 chunks each; `fixed` chunks are longer, so
its two indexes take a little longer per vector than `recursive`'s despite having
fewer of them.

---

## 6. What to bring back

**Essential — under 1 MB, and all the laptop needs to read the results:**

```
runs/562c4bb23747/retrieve/*.jsonl        per-query RetrievalResult records
runs/562c4bb23747/retrieve/summary.json   per-configuration summary
runs/562c4bb23747/retrieval_report.json   the six metrics, aggregated
runs/562c4bb23747/resolved_config.json    what the run was configured with
data/indexes/*/index.json                 per-index stats and truncation census
```

**Optional — a few hundred MB:** `data/indexes/*/chroma/`, the vector stores
themselves. Bring them back only if a later Kaggle session should skip
re-embedding (see §7). They are of no use on a laptop that cannot run the query
encoder.

`runs/562c4bb23747/retrieve/` is also the **only** thing the generation session
in §9 needs from this one. Keep it somewhere you can upload again.

Zip the essentials so one download covers it:

```python
!cd /kaggle/working/ragbench && zip -qr /kaggle/working/ragbench-results.zip \
    runs data/indexes/*/index.json && ls -lh /kaggle/working/ragbench-results.zip
```

Then **Save Version** (Save & Run All, or Quick Save if the cells have already
run). The file appears under the notebook's Output tab; download it there, or:

```bash
kaggle kernels output <user>/<notebook-slug> -p ./from-kaggle
```

Unzip into the repository root on the laptop. `runs/562c4bb23747/` is the same
path the local config resolves to — the digest is computed from `configs/`, which
is in git — so the reports read without any rewiring.

---

## 7. If the session dies mid-run

**The Kaggle fact that matters:** an interactive session's `/kaggle/working` is
lost when the session ends unless a version was saved. Nothing resumes from
thin air.

**During `index`.** Re-run the identical command:

```python
!python -m ragbench.cli index --config configs/base.yaml
```

Resumption is per batch: the store is asked which chunk ids it already holds and
only the rest are embedded. **Confirm it resumed rather than restarted** by
reading the last block of the output:

```
  reused vs written (a completed index re-runs to near-zero work):
    208323cba75a   written      0   reused   1574   -> data/indexes/208323cba75a
```

`written 0, reused 1574` means it was already complete. `written 412, reused 1162`
means it resumed and finished the gap. **`written 1574, reused 0` means it
restarted** — the index directory was not there, and you have lost that work.

**If the session itself ended**, the working directory is gone. To resume rather
than restart:

1. Save a version *before* you lose the session if you can — that captures
   `/kaggle/working`.
2. In the new session: **Add data → Notebook Output → your previous version**. It
   mounts at `/kaggle/input/<notebook-slug>/`.
3. Copy the partial state back into place before running anything:

```python
!mkdir -p /kaggle/working/ragbench/data/indexes
!cp -r /kaggle/input/<notebook-slug>/ragbench/data/indexes/* \
       /kaggle/working/ragbench/data/indexes/ 2>/dev/null || true
!cp -r /kaggle/input/<notebook-slug>/ragbench/runs /kaggle/working/ragbench/ 2>/dev/null || true
```

4. Re-run `index`, and check the `written`/`reused` line as above.

**During `retrieve`.** Same command again. Resumption is per query: results are
appended to JSONL keyed by query id and completed queries are skipped. The run
summary reports `queries_written` and `queries_reused` per configuration —
`written 0, reused 20` across all eight means there was nothing left to do.

**During `generate`.** Same command again. Resumption is per question: answers
are appended to JSONL keyed by query id, and a completed question is skipped.
The summary reports `new` and `reused` per configuration.

Two things are different from `retrieve`, and both matter.

*It refuses to resume into a changed prompt.* Every answer records the sha256 of
the prompt it was produced from. On resume each existing record's prompt is
re-rendered and compared, and a mismatch stops the stage:

```
ragbench: fixed-bge-rerank_off: q018 was answered from a different prompt
(4f1a... on disk, 9c22... now).
```

That means the template, the separator or the retrieved chunks changed under a
directory that already holds answers. Do not work around it — delete the file
and regenerate that cell. Half a run under each of two prompts cannot be
separated afterwards.

*A resumed batch is not bit-identical to an uninterrupted one.* vLLM decodes a
batch concurrently, and which requests share a batch changes the reduction order
inside the kernels; at temperature 0 this is rare and small, but it is not
guaranteed to be nothing. Resuming changes the batch composition by definition,
because the finished questions are no longer in it. If an individual answer has
to be reproducible token for token, run with `--batch-size 1`, which costs
roughly 4-6x the wall clock. For the factorial comparison it does not matter:
the effect is far below the difference between configurations.

`retrieve` is cheap enough (minutes) that restarting it costs little. `index` is
the one worth protecting, and `generate` is the one that fails loudly.

---

## 8. What the numbers should not look like

Bring these back with the results, because they are how you tell a working run
from a broken one:

- **Span coverage near the stand-in's 0.10–0.25** would mean retrieval is broken,
  not that the arms are equal. A hashing projection scoring the same as a trained
  sentence encoder is a sign the real embedder never loaded.
- **`specter2` indexes identical to `bge` indexes** — same vectors, same metrics —
  would mean both arms resolved to the same checkpoint. An *inactive* adapter can
  no longer produce this quietly: construction refuses. Check `index.json` names
  the adapter and its revision.
- **Every query stopping on `candidates_exhausted`** rather than `overflow` would
  mean the depth-30 pool, not the token budget, is binding — which breaks the
  premise of I1's constant-budget comparison.
- **Realised budget far below ~85%** would mean chunks are much larger than
  expected, or the budget tokenizer is not the generator's.

And for generation specifically:

- **Answers all ~512 tokens, with `trunc` at or near 20/20**, means the ceiling
  is binding rather than the model finishing. Those answers are cut off
  mid-sentence, and a judge will mark them down for an incompleteness the
  generator never chose. The prompt asks for one to three sentences, so a
  handful of truncations is worth reading and a column of them is a defect.
- **A `refuse` count near 20/20 in one configuration** is a retrieval finding,
  not a generation defect — that arm put nothing useful in the window. Near
  20/20 in *every* configuration means the context is not reaching the model:
  check `prompt` tokens in the length table, which should be roughly the 2000
  budget plus scaffolding, not 100.
- **`prompt` tokens near the 4096 `max_model_len`** would mean something is
  assembling far more context than the budget allows. The budget is spent in
  `retrieve`; `generate` only renders what it chose.
- **Identical answers across all eight configurations** for most questions would
  mean the context is not varying — or is being ignored. Some agreement is
  expected and is itself a result (the arms often retrieve the same gold chunk);
  total agreement is not.
- **Stand-in answers.** The report prints a two-line `*** CPU STAND-IN` banner
  when `generation.model_id` is `stand-in`. If you see it on Kaggle, vLLM never
  loaded and the numbers are extracted sentences, not generated text.

---

## 9. Generation — a separate session

Generation needs vLLM and **must not** share an environment with `[specter]`
(see §2). Start a fresh notebook.

### 9a. Install

```python
%cd /kaggle/working
!git clone https://github.com/<you>/ragbench.git
%cd /kaggle/working/ragbench
!pip install -q -e ".[generate]"
```

Restart the kernel, then confirm the GPU is visible to vLLM:

```python
!python -c "import torch, vllm; print(vllm.__version__, torch.cuda.get_device_name(0))"
```

### 9b. Bring the retrieval results in

> **The run id moved, and your retrieval results are under the old one.** The
> run id is the digest of the *whole* resolved config, and adding the generation
> block — the prompt text above all — changed it:
>
> | | run id |
> |---|---|
> | when `retrieve` ran | `runs/44e112902a29/` |
> | when `generate` ran | `runs/f66638fb9655/` |
> | now | `runs/562c4bb23747/` |
>
> It has moved twice, once per stage configured: adding `base.generation` moved
> it the first time and adding `base.judge` the second. **The pipeline is now
> complete, so it should not move again** unless a setting is deliberately
> changed.
>
> That is the design working, not a bug: a run with a different prompt is a
> different run. The retrieval outputs themselves are unaffected, and that was
> checked rather than assumed — diffing the two resolved configs shows every
> changed key under `base.generation`, and nothing in `chunk`, `index` or
> `retrieve` reads that section. So the results carry across unchanged. Copy,
> do not re-run: re-running `retrieve` would need the indexes and the GPU again.

`generate` reads what `retrieve` chose; it does **not** re-retrieve, and it needs
no index and no embedder. Mount the earlier notebook's output
(**Add data -> Notebook Output**) and copy that directory to the **new** id:

```python
!mkdir -p /kaggle/working/ragbench/runs/562c4bb23747
!cp -r /kaggle/input/<indexing-notebook-slug>/ragbench/runs/44e112902a29/retrieve \
       /kaggle/working/ragbench/runs/562c4bb23747/
!ls /kaggle/working/ragbench/runs/562c4bb23747/retrieve
```

Confirm the destination id first, because it moves again the next time anything
in `configs/` changes:

```python
!python -c "from pathlib import Path; from ragbench.config import resolve_config, run_dir; \
print(run_dir(resolve_config(Path('configs/base.yaml'))))"
```

Expect eight `.jsonl` files and `summary.json`. It also needs the **chunk sets**,
because the prompt is assembled from chunk text:

```python
!cp -r /kaggle/input/<indexing-notebook-slug>/ragbench/data/chunks \
       /kaggle/working/ragbench/data/
```

Or rebuild them, which is CPU-only and takes a couple of minutes:

```python
!python -m ragbench.cli chunk --config configs/base.yaml
```

### 9c. The model

```python
from huggingface_hub import snapshot_download
snapshot_download("Qwen/Qwen2.5-7B-Instruct-AWQ",
                  revision="b25037543e9394b818fdfca67ab2a00ecc7dd641")
```

**~5.6 GB**, six to twelve minutes on Kaggle's connection. This is the AWQ repo,
not the bf16 one — `Qwen/Qwen2.5-7B-Instruct` is ~15 GB and will not fit a T4
alongside a KV cache.

> The budget tokenizer stays pinned to `Qwen/Qwen2.5-7B-Instruct`, and that is
> correct rather than an oversight: the two repos ship byte-identical
> `tokenizer.json`, `tokenizer_config.json`, `vocab.json` and `merges.txt`, so
> the 2000-token budget was measured with the tokenizer this model uses.
> Quantisation changes weights, not vocabulary.

### 9d. Run

```python
!python -m ragbench.cli generate --config configs/base.yaml
!python -m ragbench.cli report generation --config configs/base.yaml
```

On a single T4, add `--gpu-memory-utilization 0.85` if the KV cache will not
allocate, and `--enforce-eager` if it still will not (slower decoding,
noticeably less memory).

`generate` covers all eight configurations and loads the model **once** for all
of them. 8 x 20 = 160 answers.

### Expected wall-clock

| Step | Expected | Investigate past |
|---|---|---|
| install + restart | 3-6 min | 15 min |
| AWQ download (9c) | 6-12 min | 25 min |
| vLLM engine startup | 2-5 min | 12 min |
| `generate`, all 160 | 4-10 min total | 35 min |
| `report generation` | < 30 s | 3 min |

The engine start is a fixed cost paid once, and on a T4 it is a large fraction of
the total — most of the 4-10 minutes above is CUDA graph capture and weight
loading, not decoding. `--enforce-eager` trades a slower decode for a much
shorter startup, which on a run this small is often the faster choice overall.

With `--batch-size 1` the decode is roughly 4-6x longer (25-50 min); use it only
if you need each answer reproducible independently of what else was pending.

### 9e. What to bring back

```
runs/562c4bb23747/generate/*.jsonl        the 160 answers, with length and timing
runs/562c4bb23747/generate/summary.json   per-configuration summary
runs/562c4bb23747/generation_report.json  answer length, truncation, abstention
```

Under 1 MB. Read them on the laptop with:

```bash
python -m ragbench.cli report generation --config configs/base.yaml
python -m ragbench.cli report generation --config configs/base.yaml --query q018
```

The second form prints every configuration's answer to one question, one after
another with the reference answer above them. Read a few before judging — that
is what the view is for, and it is the last point at which a prompt problem is
cheap to fix.

---

## 10. Judging — on the laptop, not on Kaggle

The judge uses no GPU and nothing from Kaggle except `runs/562c4bb23747/generate/`.
Bring that home from §9, then run it locally.

### 10a. Which judge, and why two

`judge.provider` selects the backend; both stay configured.

| provider | model | free tier |
|---|---|---|
| **`groq`** (default) | `openai/gpt-oss-120b` | free, no card |
| `openrouter` | `meta-llama/llama-3.3-70b-instruct` | requires a credit balance as of 2026-09 |

**Neither is the Llama-3.3-70B the proposal named, and that is worth stating in
the write-up rather than quietly substituting.** Groq has retired
`llama-3.3-70b-versatile` from its free tier, and OpenRouter's free variants now
require a credit balance. Of the chat models Groq's free tier still offers —
`openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `openai/gpt-oss-safeguard-20b`,
`qwen/qwen3.8-27b`, `groq/compound`, `groq/compound-mini`, `allam-2-7b` —
`gpt-oss-120b` is the largest that is not a Qwen model. The judge is therefore a
120B open-weights model rather than a 70B Llama: a deviation forced by
availability, not chosen.

**"Not a Qwen model" is doing real work there.** The generator is
Qwen2.5-7B-Instruct, and the generator's family may not grade its own output —
self-preference bias on top of small-judge unreliability, and the two are not
separable afterwards. `qwen/qwen3.8-27b` sits on the same account's model list,
so that rule excluded a genuinely eligible candidate here rather than ruling out
a hypothetical one. A test checks it for the selected provider *and* every
alternative, so switching backends cannot reintroduce it.

The unused backend is kept rather than deleted because a reviewer may ask
whether the result depends on the judge provider, and that is only answerable if
the other one is still configured. Switching is one word in `configs/base.yaml`,
and because the whole resolved config reaches the run id, scores from two judges
can never land in one directory.

### 10b. The key

```bash
export GROQ_API_KEY=gsk_...              # PowerShell: $env:GROQ_API_KEY = "gsk_..."
```

The variable's name is `judge.providers.groq.api_key_env`; its value is read
inside the client and is never in the repository, in a config file, or on a
command line. There is deliberately no `--api-key` flag: a key on a command line
lands in shell history and in the process table.

### 10c. Budget first — this does not finish in one sitting

**A judgement is expensive because it must carry the retrieved context.**
Faithfulness is a judgement about what the system was *shown*, so the passages
go in the prompt; that is the design, not an oversight, and it cannot be
trimmed without changing what faithfulness means.

```
  ~2,800 tokens per judgement   (measured: 593,993 over 212 API-backed
                                 judgements, once the retries were fixed)
  ~790,000 for a full run       (~283 API-backed judgements; the other ~37 are
                                 abstentions, matched from the answer text free)
```

That per-request figure is measured, not estimated, and it was never the
problem. The first real run cost **4,743 tokens per judgement and 11,718 per
*usable* judgement**, because 27 of 42 judgements returned no content, each one
buying a second full-prompt request that failed the same way. See 10c-bis.

Two limits bite, and the token one bites first:

- **Tokens per minute.** 8,000 TPM against a ~2,800-token call is **under three
  calls a minute** — an order of magnitude below the 30 requests/minute the same
  tier allows. A client pacing only on requests would collect 429s all day, so
  this one paces on both. Its pre-call estimate is more conservative still
  (~3,250, because it counts a `max_tokens` ceiling the model will not use), and
  is replaced by the usage figure the response reports.
- **Tokens per day.** 200,000 TPD against ~2,800 a judgement is about **71
  judgements**, so a full run is roughly **four days**. Under the settings that
  produced empty replies it was 17 usable judgements a day — over two weeks.

`ragbench judge` prints both figures after every session, and the projection it
makes for the remainder is derived from what that session actually measured
rather than from a number written down once:

```
  this session     197,816 tokens over 72 judgements   = 2,747 each
  cumulative       593,993 tokens across all 240 judgements on disk
```

**Read the session line for cost-per-judgement and the cumulative line for
spend.** They have different denominators: dividing the cumulative total — which
includes judgements reused from earlier sessions — by the current session's call
count once reported a 2,747-token judgement as 8,250.

> **Set `daily_token_cap` to whatever your own console reports.** Published
> figures move — this model replaced one that was retired mid-project — so the
> value in `configs/base.yaml` is what your account showed, not a permanent
> fact. The client also reads Groq's `x-ratelimit-remaining-tokens` and
> `x-ratelimit-limit-tokens` response headers, so what the server actually says
> is what gets reported.

### 10c-bis. What the first run cost, and why the settings changed

Worth reading before trusting the estimates above, because it is the one place
the arithmetic has already been wrong in practice.

The first real run, under `max_tokens: 400` with no `reasoning_effort`:

| | |
|---|---|
| unparsed | **24 of 40** in the first configuration (60%) |
| corrective retries | 27, across 42 judgements |
| HTTP requests | 69 for those 42 judgements |
| tokens spent | 199,211 — the whole day's allowance |
| usable judgements | **17** |

gpt-oss models emit reasoning tokens *before* their answer, and that spend counts
against `max_tokens`. At 400 the reasoning consumed the entire allowance and the
reply arrived with no content at all. Each failure then bought a corrective
retry — a second full-prompt request — which failed identically.

Two things follow, and both are now in `configs/base.yaml` with the numbers
attached:

- **`max_tokens: 800`.** The rubric's reply is a ~150-token JSON object; the
  rest is headroom so reasoning cannot starve it. A ceiling is not a charge —
  raising it costs nothing on a call that does not use it.
- **`extra_body: {reasoning_effort: low}`.** Set because the run established it
  was needed, not as a precaution. Low is the right level for this task: the
  rubric asks for a bounded comparison against a reference answer that is
  supplied, not for open-ended problem solving.

**The per-request cost was fine all along** — 2,887 measured against a ~2,900
estimate. Nearly all of the 4× overrun was retries, so removing them is most of
the fix.

Each judgement now records the tokens it cost, and `ragbench judge` prints the
per-judgement average, so the next run confirms this rather than leaving it to
be reconstructed from a daily total.

**If the `unparsed` column climbs again**, raise `max_tokens` further or set
`reasoning_effort` back to `medium` — and re-judge the failures, below, rather
than leaving them recorded.

If several days is not acceptable, the options are yours to weigh, and none
should be taken silently:

- `judge.passes: 1` halves the spend and gives up the self-consistency figure —
  the number that bounds how far any difference between configurations can be
  trusted. Not recommended.
- Judge a subset of configurations first by editing `factors.yaml`, which
  changes the experiment and the run id.
- Pay for a tier with a larger allowance.

### 10d. Run

```bash
ragbench judge --config configs/base.yaml
ragbench report judge --config configs/base.yaml
```

**Expect around 280 calls, not 320.** Every answer is scored twice — run-to-run
inconsistency is a standard LLM-judge failure mode, and the second pass is what
measures it — but the 20 abstentions are recognised from the answer text without
an API call, so 40 of the 320 cost nothing.

When the daily allowance runs out the stage stops and says so:

```
  STOPPED ON QUOTA -- 214 judgements still outstanding.
  the configured daily token cap (100,000) would be exceeded: ...
```

**That is a pause, not a failure.** Everything already scored is on disk. Re-run
the identical command after the allowance resets and it continues; nothing is
judged twice.

#### Re-judging recorded failures

An `unparsed` record is deliberately permanent: it stops a re-run spending the
calls again, and it keeps the configuration's denominator honest. But a
judgement that failed because a *setting* was wrong must not survive the fix to
that setting, or the configuration ends up scored under two regimes with nothing
to say which item came from which.

```bash
ragbench judge --config configs/base.yaml --retry-unparsed
```

That deletes the recorded failures first and scores those items again under the
current settings. Judgements that succeeded are kept, so the allowance is not
spent twice on work that was already good.

> Changing `max_tokens` or `extra_body` moves the **run id**, so judgements made
> under the old settings stay in the old run directory and the new one starts
> empty — the two regimes are already separated. `--retry-unparsed` is for the
> other case: failures that need re-judging without any config change, such as a
> provider having a bad afternoon.

| Symptom | What it means |
|---|---|
| `GROQ_API_KEY is not set` | Exported in a different shell, or spelled differently from the provider's `api_key_env`. |
| `groq rejected the API key (401)` | Not retried, deliberately — a bad key is not transient. |
| `model_not_found` or similar | The free tier's model list changes. Check the console and update `judge.providers.groq.model_id`; the judge-is-not-the-generator rule excludes any Qwen variant. |
| `STOPPED ON QUOTA` | Expected. Re-run tomorrow. |
| `judged against a different answer` | `generate` has been re-run under this run directory. Delete that configuration's judge JSONL rather than scoring two sets of answers into one. |
| a nonzero `unparsed` column | The judge returned something that was not the schema twice. Those items are persisted so a re-run does not spend the calls again — see `--retry-unparsed` below. |

### 10e. Calibration

`report judge` writes three files into the run directory:

```
calibration_sheet.md      40 answers to hand-score, configuration hidden
calibration_scores.csv    the template to fill in
calibration_key.json      the mapping back -- do not open it while scoring
```

The sheet is blind twice over: the configuration label is absent, and the items
are shuffled after stratified sampling, because five consecutive items from one
configuration would reconstruct the label from the ordering alone. Each item
carries the question, the reference answer, the answer under review, and the
retrieved passages in full — scoring faithfulness without them would not be
scoring the same thing the judge scored.

It is emitted as soon as *any* judgements exist, so the hand-scoring can be done
during the days the judge is still working through its allowance.

Fill in the CSV, then:

```bash
ragbench report judge --config configs/base.yaml \
    --calibration runs/562c4bb23747/calibration_scores.csv
```

That prints quadratically weighted Cohen's kappa and Spearman per scale, an
unweighted kappa for the verdict, and the mean difference between you and the
judge.

**A judge score is the mean of its two passes**, so a scale the passes disagreed
on lands on a half-point -- 4.5 against your 4 or 5. Kappa and Spearman treat
that as the near miss it is; `exact` cannot, so the report says how many rows
are affected beside the figure they depress.

If the CSV will not parse, the error names the file, the line and what was
expected. The most common cause is a comma inside an unquoted note, which shifts
every later column so the scores read back are whichever fields landed in those
positions -- quote the note and re-run. Set `RAGBENCH_TRACEBACK=1` for the full
traceback. Read kappa before the raw agreement figure: on a five-point scale where
most answers are good, two raters who never read anything would agree about a
third of the time, and a reviewer will say so. A large mean difference with a
high Spearman is a calibration offset — the judge is consistently harsher or
softer but ranks the answers as you do — which is a different finding from
genuine disagreement, and has a different remedy.

### 10f. What to keep

```
runs/562c4bb23747/judge/*.jsonl          two judgements per answer
runs/562c4bb23747/judge/summary.json     per-configuration summary
runs/562c4bb23747/judge_report.json      scores, verdicts, self-consistency
runs/562c4bb23747/calibration_*          the sheet, your scores, the key
```

All of it is tracked by git — see `.gitignore`, which ignores the regenerable
caches and names these back in.

---

## 11. Statistics -- also on the laptop

No GPU, no API, no new artefacts. It reads what the earlier stages wrote and
produces the numbers and the figures.

```bash
pip install -e ".[analysis]"     # matplotlib; the tests are exact and in-house
ragbench report stats --config configs/base.yaml
```

**It runs while judging is still going.** A factor's difference averages over
four cells, and a question contributes only when all four are present, so any
comparison touching an unjudged configuration reports `n=0` and names what it
needs rather than averaging over whichever cells happen to exist. Retrieval is
complete, so those comparisons are final now; the generation ones fill in as the
judge works through its daily allowance. Re-run it whenever you like -- it is
seconds, and nothing it does can disturb the judge.

The Holm correction is applied across the **six pre-specified** primary tests
whether or not all six are computable yet, so a retrieval result does not change
its verdict as judging progresses.

`configs/stats.yaml` holds the analysis plan and is deliberately outside the run
id: it produces no artefact that could mix with another, and putting it in
`base.yaml` would move the run directory out from under a four-day judge run.

### 11a. Sample size for a follow-up

The report ends with how many questions a **future** study would need to detect
an effect the size of the one seen here, at 80% power -- the number that turns
"underpowered at n=20" into something actionable.

It is **not** the power of this study. Observed power is a function of the
p-value and says nothing the p-value did not; none is computed anywhere, and a
test keeps it that way.

Each comparison gets three numbers, at two alpha levels: the sample needed at
the observed effect, and at each end of its bootstrap interval, because the
observed effect is itself noisy at n=20. The second alpha is Holm's strictest
threshold, 0.05/6, since a follow-up with the same pre-specification faces the
same correction. Where an interval spans zero the report says "not estimable"
rather than printing a number, because an effect near zero needs an unbounded
sample.

### 11b. RQ4

Once `calibration_scores.csv` is filled in:

```bash
ragbench report stats --config configs/base.yaml     --calibration runs/<id>/calibration_scores.csv
```

Without it, RQ4 reports "not computed" rather than a zero.

### 11c. Figures

Written to `runs/<id>/figures/` as SVG **and** PNG:

```
main_effects            dot-and-interval per factor, with 95% bootstrap intervals
coverage_per_config     mean span coverage, coloured by chunking arm
chunk_lengths           chunk-length distribution per arm
power_against_n         power vs sample size for a FUTURE study, 80% line marked
```

Light-mode only, deliberately: these go in a document that gets printed. The
palette is the validated categorical default and each figure spells its numbers
out in text as well as colour, so it survives greyscale. `--no-figures` skips
them if matplotlib is not installed.
