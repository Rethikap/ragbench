"""The `report` subcommand. Currently one topic: `chunks`."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ..config import DEFAULT_DATA_ROOT
from ..report.chunks import build_report

EXIT_DATA = 5
TOPICS = ("chunks",)


def add_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("topic", choices=TOPICS, help="which report to produce")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        metavar="DIR",
        help="root holding the chunk sets to report on (default: %(default)s)",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=20000,
        metavar="N",
        help="random fills used to estimate how many chunks a budget holds "
        "(default: %(default)s)",
    )


def run(args: argparse.Namespace, resolved: dict[str, Any], directory: Path) -> int:
    try:
        report = build_report(resolved, args.data_root, trials=args.trials)
    except (ValueError, KeyError) as exc:
        print(f"ragbench: {exc}")
        return EXIT_DATA

    target = directory / f"{args.topic}_report.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8", newline="")

    print(render(report, resolved))
    print(f"\nJSON artefact: {target}")
    return 0


def _row(label: str, stats: dict[str, Any]) -> str:
    if not stats.get("n"):
        return f"  {label:<22} (none)"
    return (
        f"  {label:<22} {stats['mean']:>8} {stats['median']:>8} {stats['p10']:>8}"
        f" {stats['p25']:>8} {stats['p75']:>8} {stats['p90']:>8}"
        f" {stats['min']:>7} {stats['max']:>7}"
    )


def _header(unit: str) -> str:
    return (
        f"  {unit:<22} {'mean':>8} {'median':>8} {'p10':>8} {'p25':>8}"
        f" {'p75':>8} {'p90':>8} {'min':>7} {'max':>7}"
    )


def render(report: dict[str, Any], resolved: dict[str, Any]) -> str:
    budget = report["budget"]
    separators = list(resolved["base"]["chunking"]["separators"])
    lines: list[str] = []
    add = lines.append

    add("=" * 92)
    add("CHUNK REPORT")
    add(f"  corpus manifest_sha : {report['manifest_sha']}")
    add(f"  chunk tokenizer     : {budget['chunk_tokenizer_id']}  (canonical, both arms)")
    add(f"  budget tokenizer    : {budget['budget_tokenizer_id']}")
    add(
        f"  context budget      : {budget['context_token_budget']} generator tokens"
        f"  ({budget['fill_policy']})"
    )
    add("=" * 92)

    for arm in report["arms"]:
        add("")
        add(f"--- {arm['level'].upper()}  ({arm['strategy']})  chunk_set {arm['chunk_set_id']}")
        add(f"  {arm['n_chunks']:,} chunks from {arm['n_papers']} papers")
        add("")
        add(_header("distribution"))
        add(_row("canonical tokens", arm["canonical_tokens"]))
        add(_row("budget tokens", arm["budget_tokens"]))
        add(_row("characters", arm["chars"]))
        add(_row("chunks per paper", arm["chunks_per_paper"]))

        add("")
        fill = arm["budget_fill"]
        add(f"  chunks needed to fill {budget['context_token_budget']} budget tokens:")
        add(_header("distribution"))
        add(_row("chunks per fill", fill["chunks_per_budget"]))
        add(_row("tokens actually used", fill["tokens_used"]))
        total = sum(fill["histogram"].values())
        shares = "  ".join(
            f"{count}:{value * 100 / total:.0f}%" for count, value in fill["histogram"].items()
        )
        add(f"  fill histogram (chunks:share)  {shares}")
        if fill["chunks_larger_than_budget"]:
            add(f"  chunks too large to ever fit   {fill['chunks_larger_than_budget']}")

        add("")
        levels = arm["separator_levels"]
        if levels and set(levels) != {"whole"}:
            add("  separator level that produced each chunk:")
            for key, count in levels.items():
                if key == "whole":
                    label = "fitted whole, no split"
                else:
                    label = f"level {key}: {separators[int(key)]!r}"
                share = count * 100 / arm["n_chunks"]
                add(f"    {label:<28} {count:>6}  {share:5.1f}%")
        else:
            add("  separator levels: n/a (fixed windows never consult the hierarchy)")

        add("")
        mid = arm["mid_sentence"]
        add(
            f"  cut mid-sentence      {mid['n']:>6}  {mid['share'] * 100:5.1f}%"
            f"   (excluding each paper's last chunk: {mid['excluding_final_chunk_of_paper']})"
        )
        place = arm["placeholders"]
        add(
            f"  contain a placeholder {place['n_chunks_with_placeholder']:>6}"
            f"  {place['share'] * 100:5.1f}%"
        )
        add(_header("placeholder vs prose"))
        add(_row("placeholder chunks", place["placeholder_tokens"]))
        add(_row("prose chunks", place["prose_tokens"]))

    comparison = report.get("comparison")
    if comparison:
        add("")
        add("=" * 92)
        add("DO THE ARMS DIFFER?")
        first, second = comparison["levels"]
        add(f"  median canonical tokens   {first}: {comparison['median_tokens'][0]:>7}"
            f"    {second}: {comparison['median_tokens'][1]:>7}"
            f"    ratio {comparison['median_ratio']}")
        add(f"  spread (std dev)          {first}: {comparison['std_tokens'][0]:>7}"
            f"    {second}: {comparison['std_tokens'][1]:>7}")
        add(f"  mean chunks per budget    {first}: {comparison['mean_chunks_per_budget'][0]:>7}"
            f"    {second}: {comparison['mean_chunks_per_budget'][1]:>7}")
        add(f"  total chunks              {first}: {comparison['chunk_count'][0]:>7}"
            f"    {second}: {comparison['chunk_count'][1]:>7}")
        add("=" * 92)

    return "\n".join(lines)
