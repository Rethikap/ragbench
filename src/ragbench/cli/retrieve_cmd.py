"""The `retrieve` stage. Where invariant I1 is spent.

Note what this file does not add. The common retrieval options registered in
`__main__` are `--budget-tokens` and `--depth`, and there is deliberately no
`--top-k`: the number of chunks reaching the generator is an output of filling
the budget, never an input. A test walks every registered option string and
fails the build if one appears.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ..config import DEFAULT_DATA_ROOT
from ..gold.freeze import GoldSetError
from ..retrieval.pipeline import run_retrieve

EXIT_DATA = 5


def add_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        metavar="DIR",
        help="root holding the chunk sets and indexes (default: %(default)s)",
    )


def run(args: argparse.Namespace, resolved: dict[str, Any], directory: Path) -> int:
    # The two overrides exist so a smaller budget or a shallower pool can be
    # tried without editing the frozen config; both are recorded in the run's
    # dumped config, so a run still describes itself.
    if getattr(args, "budget_tokens", None):
        resolved["base"]["retrieval"]["context_token_budget"] = int(args.budget_tokens)
    if getattr(args, "depth", None):
        resolved["base"]["retrieval"]["depth"] = int(args.depth)

    try:
        reports = run_retrieve(
            resolved,
            Path(args.config).parent,
            args.data_root,
            directory,
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
    add("=" * 100)
    add(f"RETRIEVAL  ({len(reports)} configurations)")
    first = reports[0] if reports else {}
    add(
        f"  budget {first.get('token_budget')} generator tokens"
        f"  ({first.get('fill_policy')})   candidate depth {first.get('depth')}"
    )
    add("=" * 100)
    add(
        f"  {'configuration':<34}{'queries':>8}{'written':>9}{'reused':>8}"
        f"  {'index':<14}{'reranker'}"
    )
    for report in reports:
        add(
            f"  {report['config']:<34}{report['n_queries']:>8}"
            f"{report['queries_written']:>9}{report['queries_reused']:>8}"
            f"  {report['index_id']:<14}{report['reranker']}"
        )
    add("=" * 100)
    return "\n".join(lines)
