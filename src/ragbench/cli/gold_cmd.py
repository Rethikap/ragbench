"""The `gold` subcommand: build candidates, print them for verification, freeze.

Not one of the seven pipeline stages. The gold set is an *input* to `retrieve`,
built once and frozen, the way the corpus manifest is -- putting it in STAGES
would imply it is rebuilt per run, which is exactly what freezing prevents.

Three actions, in the order they happen. `sheet` sits between `build` and
`freeze` because verification is a step, not a formality: it is where a human
reads the twenty questions, and `freeze` will not run until they have.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ..config import DEFAULT_DATA_ROOT, MANIFEST_FILENAME, gold_candidates_dir
from ..gold.freeze import GoldSetError, freeze_sha
from ..gold.pipeline import build_candidates, freeze_gold_set, load_candidates
from ..ingest.manifest import ManifestError
from ..report.gold import build_report, verification_sheet

EXIT_DATA = 5
ACTIONS = ("build", "sheet", "freeze")
SHEET_FILENAME = "verification_sheet.md"


def add_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("action", choices=ACTIONS, help="which step to run")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        metavar="DIR",
        help="root holding the parsed papers and the candidate working directory "
        "(default: %(default)s)",
    )
    parser.add_argument(
        "--drafter",
        default=None,
        metavar="SPEC",
        help="override gold.drafter: 'authored' or 'stand-in'. There is no "
        "generator-drafted option; see configs/gold.yaml for why",
    )


def run(args: argparse.Namespace, resolved: dict[str, Any], directory: Path) -> int:
    configs = Path(args.config).parent
    digest = str(resolved["corpus"].get("manifest_sha", ""))
    working = gold_candidates_dir(digest, args.data_root)

    try:
        if args.action == "build":
            return _build(args, resolved, configs, working)
        if args.action == "sheet":
            return _sheet(args, resolved, working)
        return _freeze(resolved, configs, working)
    except (ManifestError, GoldSetError, ValueError, KeyError) as exc:
        print(f"ragbench: {exc}")
        return EXIT_DATA


def _build(
    args: argparse.Namespace, resolved: dict[str, Any], configs: Path, working: Path
) -> int:
    report = build_candidates(
        resolved,
        configs / MANIFEST_FILENAME,
        args.data_root,
        working,
        configs,
        drafter_spec=args.drafter,
        on_progress=lambda message: print(f"  {message}", end="\r", flush=True),
    )
    print()
    print(f"drafter            {report['drafter']}")
    print(f"passages sampled   {report['n_passages_sampled']}")
    print(f"candidates built   {report['n_drafted']}")
    if report["n_draft_failures"]:
        print(f"build failures     {report['n_draft_failures']}")
        for failure in report["draft_failures"][:5]:
            print(f"    {failure['passage_id']}: {failure['error']}")
    print(f"auto-rejected      {report['n_auto_rejected']}")
    for reason, count in report["rejected_by_reason"].items():
        print(f"    {reason:<22} {count}")
    print(f"selected           {report['n_selected']}")
    print(f"verified           {report['n_verified']}/{report['n_selected']}")
    print(f"\ncandidates: {report['directory']}")
    if report["unverified"]:
        print("Run `ragbench gold sheet` and verify each question before freezing.")
    return 0


def _sheet(args: argparse.Namespace, resolved: dict[str, Any], working: Path) -> int:
    candidates = _require_candidates(working)
    report = build_report(resolved, candidates, args.data_root)
    sheet = verification_sheet(report)
    target = working / SHEET_FILENAME
    target.write_text(sheet, encoding="utf-8", newline="")
    print(sheet)
    print(f"\nsheet: {target}")
    return 0


def _freeze(resolved: dict[str, Any], configs: Path, working: Path) -> int:
    candidates = _require_candidates(working)
    result = freeze_gold_set(resolved, candidates, configs)
    freeze_sha(configs / "gold.yaml", result["gold_set_sha"])
    print(f"gold set      {result['n_questions']} questions -> {result['path']}")
    print(f"candidates    {result['candidates_path']}")
    print(f"gold_set_sha  {result['gold_set_sha']}  (pinned into configs/gold.yaml)")
    return 0


def _require_candidates(working: Path) -> list[dict[str, Any]]:
    candidates = load_candidates(working)
    if not candidates:
        raise ValueError(f"no candidates in {working}; run `ragbench gold build` first")
    return candidates
