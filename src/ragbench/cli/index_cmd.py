"""The `index` stage: embed each chunk set with each embedding arm.

Four indexes, and the number comes from the Cartesian product of the two
factors rather than from a constant. There is deliberately no flag to build "an
index" without saying which pair it is for.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ..config import DEFAULT_DATA_ROOT
from ..index.pipeline import run_index

EXIT_DATA = 5


def add_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        metavar="DIR",
        help="root holding the chunk sets and the index store (default: %(default)s)",
    )
    parser.add_argument(
        "--chunking",
        action="append",
        metavar="LEVEL",
        help="chunking factor level to index, repeatable. Defaults to every level",
    )
    parser.add_argument(
        "--census-only",
        action="store_true",
        help="report how many chunks the encoder would truncate and stop. Loads each "
        "arm's tokenizer but not its weights, so it answers the truncation question "
        "on a machine that cannot run the models",
    )
    parser.add_argument(
        "--embedding",
        action="append",
        metavar="LEVEL",
        help="embedding factor level to index, repeatable. Defaults to every level. "
        "Set embedding.model_id to 'stand-in' for the offline CPU path",
    )


def run(args: argparse.Namespace, resolved: dict[str, Any], directory: Path) -> int:
    try:
        reports = run_index(
            resolved,
            args.data_root,
            chunking_levels=args.chunking,
            embedding_levels=args.embedding,
            census_only=args.census_only,
            on_progress=lambda message: print(f"  {message}", end="\r", flush=True),
        )
    except (ValueError, KeyError, OSError) as exc:
        print(f"ragbench: {exc}")
        return EXIT_DATA

    print()
    print(render(reports))
    return 0


def render(reports: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    add = lines.append
    census_only = all(report.get("census_only") for report in reports)
    add("=" * 100)
    label = "TRUNCATION CENSUS" if census_only else "INDEXES"
    add(f"{label}  ({len(reports)} = chunking levels x embedding levels)")
    add("=" * 100)
    if census_only:
        add(f"  {'index_id':<14}{'chunking':<11}{'embedding':<12}{'chunks':>8}")
        for report in reports:
            add(
                f"  {report['index_id']:<14}{report['chunking_level']:<11}"
                f"{report['embedding_level']:<12}{report['n_chunks']:>8}"
            )
        add("")
        add(_census_table(reports))
        add(_truncation_warning(reports))
        add("=" * 100)
        return "\n".join(line for line in lines if line is not None)
    header = (
        f"  {'index_id':<14}{'chunking':<11}{'embedding':<12}{'chunk_set':<14}"
        f"{'vectors':>8}{'dim':>5}{'secs':>8}{'peak MB':>9}"
    )
    add(header)
    for report in reports:
        add(
            f"  {report['index_id']:<14}{report['chunking_level']:<11}"
            f"{report['embedding_level']:<12}{report['chunk_set_id']:<14}"
            f"{report['vectors_in_store']:>8}{report['dimension']:>5}"
            f"{report['build_seconds']:>8.1f}{report['peak_rss_mb']:>9.1f}"
        )

    add("")
    add(_census_table(reports))
    warning = _truncation_warning(reports)
    if warning:
        add(warning)

    add("")
    add("  reused vs written (a completed index re-runs to near-zero work):")
    for report in reports:
        add(
            f"    {report['index_id']:<14} written {report['vectors_written']:>6}"
            f"   reused {report['vectors_reused']:>6}"
            f"   -> {report['directory']}"
        )
    add("=" * 100)
    return "\n".join(lines)


def _census_table(reports: list[dict[str, Any]]) -> str:
    lines = ["  content tokens per chunk, and what the encoder had room for:"]
    lines.append(
        f"  {'index_id':<14}{'embedding':<12}{'mean tok':>9}{'max tok':>9}{'limit':>7}"
        f"{'truncated':>11}{'share':>8}{'worst over':>12}"
    )
    for report in reports:
        census = report["truncation"]
        lines.append(
            f"  {report['index_id']:<14}{report['embedding_level']:<12}"
            f"{census['mean_content_tokens']:>9.1f}"
            f"{census['max_content_tokens']:>9}{census['usable_content_tokens']:>7}"
            f"{census['n_truncated']:>11}{census['share_truncated'] * 100:>7.1f}%"
            f"{census['worst_overflow_tokens']:>12}"
        )
    return "\n".join(lines)


def _truncation_warning(reports: list[dict[str, Any]]) -> str:
    """Two causes, reported separately, because only one of them is a defect."""
    arithmetic = sum(
        report["truncation"]["n_truncated"]
        for report in reports
        if report["truncation"].get("canonical_tokenizer")
    )
    expansion = sum(
        report["truncation"]["n_truncated"]
        for report in reports
        if not report["truncation"].get("canonical_tokenizer")
    )
    lines: list[str] = []
    if arithmetic:
        lines.append(
            f"\n  DEFECT: {arithmetic} chunks truncated on the arm that uses the canonical\n"
            "  chunk tokenizer. max_seq_tokens counts [CLS] and [SEP], so a chunk has room\n"
            "  for max_seq_tokens - 2 content tokens. Set chunking.target_tokens to match."
        )
    if expansion:
        lines.append(
            f"\n  EXPECTED: {expansion} chunks truncated on an arm whose tokenizer is not the\n"
            "  canonical one. Boundaries are drawn once, with one tokenizer, which is what\n"
            "  keeps chunking and embedding orthogonal (I2); the price is that another arm's\n"
            "  tokenizer may make more tokens of the same text. A consequence, not a defect."
        )
    return "\n".join(lines)
