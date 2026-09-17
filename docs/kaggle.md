# Running the GPU stages on Kaggle

Written for: whoever is operating the Kaggle session. Assumes a fresh notebook
with a GPU, no local state, and a session that may die mid-run.

The GPU stages are `index` (embed ~3,640 chunks into four vector indexes) and
`retrieve` (eight configurations × 20 queries). Everything before them —
selection, ingest, chunking, the gold set — is already frozen and comes with the
repository. Nothing on Kaggle touches NCBI.

---

## 0. What travels, and what does not

`index` and `retrieve` read **the chunk sets and the gold set, and nothing else**.
They never open a parsed paper or a raw JATS file, so those 50 MB stay at home.

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
> measured with. `AdapterEmbedder` refuses to construct if activation did not
> take, so a silently-missing adapter fails loudly instead of quietly measuring
> the wrong model.

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
`runs/44e112902a29/retrieval_report.json` and prints the two tables.

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

The four indexes are ~1,574 and ~2,066 chunks each; `fixed` chunks are longer, so
its two indexes take a little longer per vector than `recursive`'s despite having
fewer of them.

---

## 6. What to bring back

**Essential — under 1 MB, and all the laptop needs to read the results:**

```
runs/44e112902a29/retrieve/*.jsonl        per-query RetrievalResult records
runs/44e112902a29/retrieve/summary.json   per-configuration summary
runs/44e112902a29/retrieval_report.json   the six metrics, aggregated
runs/44e112902a29/resolved_config.json    what the run was configured with
data/indexes/*/index.json                 per-index stats and truncation census
```

**Optional — a few hundred MB:** `data/indexes/*/chroma/`, the vector stores
themselves. Bring them back only if a later Kaggle session should skip
re-embedding (see §7). They are of no use on a laptop that cannot run the query
encoder.

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

Unzip into the repository root on the laptop. `runs/44e112902a29/` is the same
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

`retrieve` is cheap enough (minutes) that restarting it costs little. `index` is
the one worth protecting.

---

## 8. What the numbers should not look like

Bring these back with the results, because they are how you tell a working run
from a broken one:

- **Span coverage near the stand-in's 0.10–0.25** would mean retrieval is broken,
  not that the arms are equal. A hashing projection scoring the same as a trained
  sentence encoder is a sign the real embedder never loaded.
- **`specter2` indexes identical to `bge` indexes** — same vectors, same metrics —
  would mean the adapter did not activate, or both arms resolved to the same
  checkpoint. The index ids differ by construction; check `index.json` names the
  adapter.
- **Every query stopping on `candidates_exhausted`** rather than `overflow` would
  mean the depth-30 pool, not the token budget, is binding — which breaks the
  premise of I1's constant-budget comparison.
- **Realised budget far below ~85%** would mean chunks are much larger than
  expected, or the budget tokenizer is not the generator's.
