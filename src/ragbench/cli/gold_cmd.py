"""The `gold` subcommand: build candidates, then freeze the verified set.

Not one of the seven pipeline stages. The gold set is an *input* to `retrieve`,
built once and frozen, the way the corpus manifest is -- putting it in STAGES
would imply it is rebuilt per run, which is exactly what freezing prevents.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ..config import DEFAULT_DATA_ROOT, MANIFEST_FILENAME, gold_candidates_dir
from ..gold.freeze import GoldSetError, freeze_sha
from ..gold.pipeline import build_candidates, freeze_gold_set, load_candidates
from ..ingest.manifest import ManifestError

EXIT_DATA = 5
ACTIONS = ("build", "freeze")


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
        help="override gold.drafter: 'qwen', 'stand-in', or 'replay:<path>'. The "
        "stand-in needs no GPU and no download, and `gold freeze` refuses its output",
    )


def _configs_dir(args: argparse.Namespace) -> Path:
    return Path(args.config).parent


def run(args: argparse.Namespace, resolved: dict[str, Any], directory: Path) -> int:
    configs = _configs_dir(args)
    digest = str(resolved["corpus"].get("manifest_sha", ""))
    working = gold_candidates_dir(digest, args.data_root)

    try:
        if args.action == "build":
            return _build(args, resolved, configs, working)
        return _freeze(resolved, configs, working)
    except (ManifestError, GoldSetError, ValueError) as exc:
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
        drafter_spec=args.drafter,
        on_progress=lambda message: print(f"  {message}", end="\r", flush=True),
    )
    print()
    print(f"drafter            {report['drafter']}")
    print(f"passages sampled   {report['n_passages_sampled']}")
    print(f"candidates drafted {report['n_drafted']}")
    if report["n_draft_failures"]:
        print(f"draft failures     {report['n_draft_failures']}")
    print(f"auto-rejected      {report['n_auto_rejected']}")
    for reason, count in report["rejected_by_reason"].items():
        print(f"    {reason:<22} {count}")
    print(f"surviving checks   {report['n_surviving_checks']}")
    print(f"\ncandidates: {report['directory']}")
    print(
        "Mark the ones you verify with \"verified\": true, then run `ragbench gold freeze`."
    )
    return 0


def _freeze(resolved: dict[str, Any], configs: Path, working: Path) -> int:
    candidates = load_candidates(working)
    if not candidates:
        print(f"ragbench: no candidates in {working}; run `ragbench gold build` first")
        return EXIT_DATA
    result = freeze_gold_set(resolved, candidates, configs)
    freeze_sha(configs / "gold.yaml", result["gold_set_sha"])
    print(f"gold set      {result['n_questions']} questions -> {result['path']}")
    print(f"candidates    {result['candidates_path']}")
    print(f"gold_set_sha  {result['gold_set_sha']}  (pinned into configs/gold.yaml)")
    return 0
