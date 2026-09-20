"""The `generate` stage: one deterministic answer per cell per question.

Note which knobs are here and which are not. `--gpu-memory-utilization`,
`--enforce-eager` and `--batch-size` are host settings: they change how long the
stage takes and whether it fits the card, and they cannot change an answer, so
they are flags and stay out of the resolved config. Everything that *can* change
an answer -- the prompt, every sampling field, `max_model_len` -- lives in
`base.generation` and therefore in the run id. A run redone on a smaller GPU is
the same run; a run redone with a different prompt is not.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ..config import DEFAULT_DATA_ROOT
from ..generation.pipeline import run_generate
from ..gold.freeze import GoldSetError

EXIT_DATA = 5


def add_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        metavar="DIR",
        help="root holding the chunk sets the context is assembled from "
        "(default: %(default)s)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=0,
        metavar="N",
        help="questions decoded together (default: all pending in a configuration). "
        "Batching is where the GPU time is; N=1 decodes one at a time, which is "
        "slower but makes each answer independent of which others were pending",
    )
    parser.add_argument(
        "--gpu-memory-utilization",
        type=float,
        default=0.90,
        metavar="FRACTION",
        help="fraction of VRAM vLLM may claim (default: %(default)s); lower it if "
        "the KV cache will not fit alongside anything else on the card",
    )
    parser.add_argument(
        "--enforce-eager",
        action="store_true",
        help="skip CUDA graph capture: slower decoding, noticeably less memory",
    )


def run(args: argparse.Namespace, resolved: dict[str, Any], directory: Path) -> int:
    try:
        reports = run_generate(
            resolved,
            Path(args.config).parent,
            args.data_root,
            directory,
            batch_size=int(args.batch_size),
            runtime={
                "gpu_memory_utilization": float(args.gpu_memory_utilization),
                "enforce_eager": bool(args.enforce_eager),
            },
            on_progress=lambda message: print(f"  {message}", end="\r", flush=True),
        )
    except (ValueError, KeyError, OSError, GoldSetError) as exc:
        print(f"ragbench: {exc}")
        return EXIT_DATA

    print()
    print(render(reports))
    return 0


def render(reports: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    add = lines.append
    first = reports[0] if reports else {}
    sampling = first.get("sampling", {})
    add("=" * 100)
    add(f"GENERATION  ({len(reports)} configurations)")
    add(f"  generator     {first.get('generator', '-')}")
    add(
        f"  prompt        {first.get('prompt_template_id', '-')}"
        f"  (digest {first.get('prompt_digest', '-')})"
    )
    add(
        "  decoding      "
        + "  ".join(f"{key}={value}" for key, value in sorted(sampling.items()))
    )
    add("=" * 100)
    add(
        f"  {'configuration':<34}{'answers':>8}{'new':>6}{'reused':>8}"
        f"{'wall s':>9}{'trunc':>7}"
    )
    for report in reports:
        add(
            f"  {report['config']:<34}{report['n_answers']:>8}{report['answers_written']:>6}"
            f"{report['answers_reused']:>8}{report['wall_clock_ms'] / 1000:>9.1f}"
            f"{report['hit_max_new_tokens']:>7}"
        )
    add("=" * 100)
    add("  `ragbench report generation` for answer length, timing and the answers themselves.")
    return "\n".join(lines)
