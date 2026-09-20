"""The `judge` stage: every answer scored twice against the rubric.

The API key is read from the environment inside the client and appears nowhere
here -- not as a flag, not in config, not in a log line. `judge.api_key_env`
names the variable, which is documentation rather than a secret.

The stage is restartable by design, because it is the only one that is metered:
a record on disk is never re-judged, so a session killed by a rate limit resumes
where it stopped rather than paying for the first two hundred calls again.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ..config import DEFAULT_DATA_ROOT
from ..gold.freeze import GoldSetError
from ..judging.base import JudgeError
from ..judging.pipeline import run_judge

EXIT_DATA = 5


def add_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        metavar="DIR",
        help="root holding the chunk sets the judge reads the context from "
        "(default: %(default)s)",
    )


def run(args: argparse.Namespace, resolved: dict[str, Any], directory: Path) -> int:
    try:
        reports = run_judge(
            resolved,
            Path(args.config).parent,
            args.data_root,
            directory,
            on_progress=lambda message: print(f"  {message}", end="\r", flush=True),
        )
    except (ValueError, KeyError, OSError, GoldSetError, JudgeError) as exc:
        print(f"ragbench: {exc}")
        return EXIT_DATA

    print()
    print(render(reports))
    return 0


def render(reports: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    add = lines.append
    first = reports[0] if reports else {}
    add("=" * 100)
    add(f"JUDGING  ({len(reports)} configurations)")
    add(f"  judge         {first.get('judge', '-')}")
    add(
        f"  rubric        {first.get('rubric_id', '-')}"
        f"  (digest {first.get('rubric_digest', '-')})   passes {first.get('passes', '-')}"
    )
    add("=" * 100)
    add(
        f"  {'configuration':<32}{'judged':>8}{'new':>6}{'reused':>8}"
        f"{'calls':>7}{'abstain':>9}{'unparsed':>10}"
    )
    for report in reports:
        add(
            f"  {report['config']:<32}{report['n_judgements']:>8}{report['written']:>6}"
            f"{report['reused']:>8}{report['api_calls']:>7}"
            f"{report['abstained']:>9}{report['unparsed']:>10}"
        )
    total_calls = sum(report["api_calls"] for report in reports)
    total_unparsed = sum(report["unparsed"] for report in reports)
    total_retries = sum(report["parse_retries"] for report in reports)
    add("=" * 100)
    add(f"  {total_calls} API calls; {total_retries} corrective retries after a bad reply.")
    if total_unparsed:
        add(
            f"  {total_unparsed} items are recorded as UNPARSED -- the judge returned something"
        )
        add(
            "  that was not the schema twice. They are persisted so a re-run does not spend"
        )
        add(
            "  the calls again; delete those lines from the judge JSONL to retry them."
        )
    add("  `ragbench report judge` for scores, self-consistency and the calibration sheet.")
    return "\n".join(lines)
