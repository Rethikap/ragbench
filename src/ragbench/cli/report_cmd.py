"""The `report` subcommand. Three topics: `chunks`, `gold` and `retrieval`."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ..config import DEFAULT_DATA_ROOT, gold_candidates_dir
from ..gold.freeze import GoldSetError
from ..gold.pipeline import load_candidates
from ..report import gold as gold_report
from ..report import retrieval as retrieval_report
from ..report.chunks import build_report

EXIT_DATA = 5
TOPICS = ("chunks", "gold", "retrieval")


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
        "(default: %(default)s); `chunks` topic only",
    )


def run(args: argparse.Namespace, resolved: dict[str, Any], directory: Path) -> int:
    try:
        if args.topic == "retrieval":
            report = retrieval_report.build_report(
                resolved, Path(args.config).parent, args.data_root, directory
            )
            rendered = render_retrieval(report)
        elif args.topic == "gold":
            working = gold_candidates_dir(
                str(resolved["corpus"].get("manifest_sha", "")), args.data_root
            )
            candidates = load_candidates(working)
            if not candidates:
                raise ValueError(f"no candidates in {working}; run `ragbench gold build` first")
            report = gold_report.build_report(
                resolved, candidates, args.data_root, trials=max(1, args.trials // 1000)
            )
            rendered = render_gold(report)
        else:
            report = build_report(resolved, args.data_root, trials=args.trials)
            rendered = render(report, resolved)
    except (ValueError, KeyError, GoldSetError) as exc:
        print(f"ragbench: {exc}")
        return EXIT_DATA

    target = directory / f"{args.topic}_report.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8", newline="")

    print(rendered)
    print(f"\nJSON artefact: {target}")
    return 0


def render_gold(report: dict[str, Any]) -> str:
    levels = list(report["arms"])
    lines: list[str] = []
    add = lines.append

    add("=" * 100)
    add("GOLD SET" + ("" if report["frozen"] else "   [DRAFT -- NOT FROZEN]"))
    add(f"  gold_set_sha        : {report['gold_set_sha']}")
    add(f"  corpus manifest_sha : {report['manifest_sha']}")
    add(f"  verified by hand    : {report['n_verified']}/{report['n_questions']}")
    add(f"  {report['n_questions']} questions from {report['n_papers']} papers")
    add(
        f"  evidence span       : median {report['span_chars']['median']:.0f} chars"
        f"  ({report['span_chars']['min']}-{report['span_chars']['max']})   <- the label"
    )
    add(
        f"  context paragraph   : median {report['context_chars']['median']:.0f} chars"
        f"  ({report['context_chars']['min']}-{report['context_chars']['max']})"
        "   provenance only"
    )
    add("=" * 100)

    add("")
    header = f"  {'id':<5} {'pmcid':<12} {'span':>14} {'chars':>6}"
    for level in levels:
        header += f" {level[:9]:>9}"
    add(header + "   section")
    add(
        f"  {'':<5} {'':<12} {'':>14} {'':>6}"
        + "".join(f" {'chunks':>9}" for _ in levels)
        + "   (to cover the span)"
    )
    for question in report["questions"]:
        gold = question["gold"]
        row = (
            f"  {question['query_id']:<5} {gold['pmcid']:<12}"
            f" {gold['char_start']:>6}-{gold['char_end']:<7}"
            f" {question['span_chars']:>6}"
        )

        for level in levels:
            row += f" {question['cover'][level]['n_chunks_to_cover']:>9}"
        add(row + f"   {(gold['section'] or '(untitled)')[:34]}")
    add("")
    add("--- QUESTIONS")
    for question in report["questions"]:
        add(f"  [{question['query_id']}] {question['question']}")
        add(f"        -> {question['reference_answer']}")

    add("")
    add("--- SELECTION")
    selection = report["selection"]
    add(f"  drafted    {selection['n_candidates']}")
    add(f"  selected   {selection['n_selected']}")
    add(f"  rejected   {selection['n_rejected']}  (auto: {selection['n_auto_rejected']})")
    for reason, count in selection["rejected_by_reason"].items():
        add(f"    {reason:<36} {count}")
        for note in selection["notes"].get(reason, []):
            add(f"        {note}")
    add(f"  drafted by {'; '.join(selection['drafters'])}")

    add("")
    add("--- WHAT ELSE IS IN THE WINDOW")
    budget = report["budget"]
    add(
        f"  Filled to {budget['context_token_budget']} generator tokens"
        f" ({budget['fill_policy']}); gold chunk at rank 1, remaining slots drawn at random."
    )
    add("  Ranking quality is held fixed. What varies is the geometry each arm imposes.")
    add("")
    add(
        f"    {'':<12}{'density':>9}{'distract':>9}{'chunks':>8}{'tokens':>8}"
        f"{'recall@10':>11}{'nDCG@10':>9}"
    )
    for level, arm in report["arms"].items():
        window = arm["window"]
        add(
            f"    {level:<12}{window['mean_evidence_density'] * 100:>8.2f}%"
            f"{window['mean_distractor_count']:>9.1f}"
            f"{window['chunks_in_window']['mean']:>8.1f}"
            f"{window['tokens_used']['mean']:>8.0f}"
            f"{window['recall_at_10']:>11.2f}{window['ndcg_at_10']:>9.2f}"
        )
    add("")
    add("  generator tokens before the gold chunk, if a ranker puts it at rank r:")
    first = next(iter(report["arms"].values()))["window"]["tokens_before_gold_at_rank"]
    ranks = sorted(first, key=int)
    add(f"    {'':<12}" + "".join(f"{'r=' + r:>9}" for r in ranks))
    for level, arm in report["arms"].items():
        offsets = arm["window"]["tokens_before_gold_at_rank"]
        add(
            f"    {level:<12}"
            + "".join(
                f"{offsets[r]:>9.0f}" if offsets[r] is not None else f"{'--':>9}"
                for r in ranks
            )
        )

    add("")
    add("--- CHUNKS EACH ARM MUST RETRIEVE TO COVER A GOLD SPAN")
    add("  The denominator Recall@k divides by, and the reason it is not the primary metric.")
    add("")
    add("  Labelled by MINIMAL EVIDENCE SPAN (the gold set as it stands):")
    add(f"    {'':<12}{'mean':>7}{'median':>8}{'max':>6}{'>1 chunk':>10}{'ceiling':>10}")
    for level, arm in report["arms"].items():
        stats = arm["chunks_to_cover"]
        add(
            f"    {level:<12}{stats['mean']:>7.2f}{stats['median']:>8.1f}{stats['max']:>6}"
            f"{arm['spans_needing_more_than_one_chunk']:>7}/{report['n_questions']:<2}"
            f"{arm['mean_max_coverage']:>10.4f}"
        )
    add("")
    add("  Labelled by CONTEXT PARAGRAPH, for comparison (what the first cut did):")
    add(f"    {'':<12}{'mean':>7}{'median':>8}{'max':>6}{'>1 chunk':>10}{'ceiling':>10}")
    for level, arm in report["arms_if_labelled_by_paragraph"].items():
        stats = arm["chunks_to_cover"]
        add(
            f"    {level:<12}{stats['mean']:>7.2f}{stats['median']:>8.1f}{stats['max']:>6}"
            f"{arm['spans_needing_more_than_one_chunk']:>7}/{report['n_questions']:<2}"
            f"{arm['mean_max_coverage']:>10.4f}"
        )

    for level, arm in report["arms"].items():
        stats = arm["chunks_to_cover"]
        add("")
        add(f"  {level} ({arm['strategy']}, {arm['n_chunks']:,} chunks)")
        add(
            f"    chunks per span   mean {stats['mean']:.2f}  median {stats['median']:.1f}"
            f"  min {stats['min']}  max {stats['max']}"
        )
        add(
            "    histogram         "
            + "  ".join(f"{k} chunk(s): {v}" for k, v in arm["histogram"].items())
        )
        add(
            f"    spans needing >1  {arm['spans_needing_more_than_one_chunk']}"
            f"/{report['n_questions']}"
        )
        add(f"    mean max coverage {arm['mean_max_coverage']}")
        add(
            f"    context cost      median {arm['covering_chunk_tokens']['median']:.0f}"
            f" canonical tokens to hold a full span"
        )
    add("=" * 100)
    return "\n".join(lines)


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
        tiny = arm["tiny"]
        add(
            f"  chunks over the {budget['target_tokens']}-token target"
            f"   {arm['over_target']:>6}   (must be 0)"
        )
        add(
            f"  short chunks (min_chunk_tokens: {budget['min_chunk_tokens']}"
            " -- kept, never merged):"
        )
        for key, row in tiny.items():
            label = f"under {key.removeprefix('under_')} tokens"
            add(
                f"    {label:<28} {row['n']:>6}  {row['share'] * 100:5.1f}%"
                f"   (paper-final {row['final_chunk_of_paper']}, mid-body {row['mid_body']})"
            )

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


def render_retrieval(report: dict[str, Any]) -> str:
    """The six metrics per configuration, plus what the budget actually bought."""
    lines: list[str] = []
    add = lines.append
    add("=" * 108)
    add("RETRIEVAL REPORT")
    add(f"  gold_set_sha : {report['gold_set_sha']}   manifest_sha : {report['manifest_sha']}")
    add(
        f"  budget       : {report['token_budget']} generator tokens"
        f"  ({report['fill_policy']})   depth {report['depth']}   rank k {report['rank_k']}"
    )
    add("=" * 108)

    add("")
    add("--- WHAT THE BUDGET BOUGHT  (I1: chunk count is an output, not an input)")
    add(
        f"  {'configuration':<32}{'chunks':>8}{'tokens':>9}{'slack':>8}"
        f"{'realised':>10}   stopped"
    )
    for config in report["configs"]:
        stopped = ", ".join(f"{k}:{v}" for k, v in config["stopped_reason"].items())
        add(
            f"  {config['config']:<32}{config['chunks_per_context']['mean']:>8.2f}"
            f"{config['tokens_used']['mean']:>9.0f}{config['budget_slack']['mean']:>8.0f}"
            f"{config['realised_budget_share'] * 100:>9.1f}%   {stopped}"
        )

    add("")
    add("--- METRICS  (span coverage primary; recall and nDCG secondary, I5)")
    add(
        f"  {'configuration':<32}{'coverage':>9}{'density':>9}{'distract':>9}"
        f"{'gold rank':>10}{'tok before':>11}{'recall@10':>10}{'nDCG@10':>9}"
    )
    for config in report["configs"]:
        rank = config["mean_gold_rank"]
        before = config["mean_tokens_before_gold"]
        add(
            f"  {config['config']:<32}{config['span_coverage']:>9.3f}"
            f"{config['evidence_density'] * 100:>8.2f}%{config['distractor_count']:>9.2f}"
            f"{(f'{rank:.2f}' if rank is not None else '--'):>10}"
            f"{(f'{before:.0f}' if before is not None else '--'):>11}"
            f"{config['recall_at_10']:>10.3f}{config['ndcg_at_10']:>9.3f}"
        )
    add("")
    add(
        "  gold chunk present in the context: "
        + "  ".join(
            f"{c['config'].split('-rerank_')[0]}/{c['rerank']}:{c['gold_found']}/{c['n_queries']}"
            for c in report["configs"]
        )
    )
    add("=" * 108)
    return "\n".join(lines)
