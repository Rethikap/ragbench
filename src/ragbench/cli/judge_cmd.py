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
    parser.add_argument(
        "--retry-unparsed",
        action="store_true",
        help="delete the recorded UNPARSED judgements first, so they are scored "
        "again. Use it after changing a setting that caused them -- a judgement "
        "that failed because max_tokens was too small must not survive raising "
        "max_tokens, or the configuration is scored under two regimes",
    )


def run(args: argparse.Namespace, resolved: dict[str, Any], directory: Path) -> int:
    try:
        reports = run_judge(
            resolved,
            Path(args.config).parent,
            args.data_root,
            directory,
            retry_unparsed=bool(args.retry_unparsed),
            on_progress=lambda message: print(f"  {message}", end="\r", flush=True),
        )
    except (ValueError, KeyError, OSError, GoldSetError, JudgeError) as exc:
        # JudgeQuotaExhausted is handled inside the pipeline and reported as a
        # pause; anything reaching here is a real failure.
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
    outstanding = sum(report.get("outstanding", 0) for report in reports)
    add("=" * 100)

    cleared = sum(report.get("unparsed_cleared", 0) for report in reports)
    if cleared:
        add(f"  --retry-unparsed removed {cleared} recorded failures before judging, so they")
        add("  were scored again under the current settings.")

    # Session and cumulative are different numerators and must not share a
    # denominator. Dividing every record in the files -- including judgements
    # reused from earlier sessions -- by THIS session's call count reported a
    # 2,747-token judgement as 8,250.
    session_tokens = sum(report.get("tokens_session", 0) for report in reports)
    total_tokens = sum(report.get("tokens_total", 0) for report in reports)
    per_judgement = session_tokens / total_calls if total_calls else 0.0

    add(
        f"  {total_calls} judgements via the API; "
        f"{total_retries} corrective retries after a bad reply."
    )
    if total_calls and session_tokens:
        add(
            f"  this session   {session_tokens:>9,} tokens over {total_calls} judgements"
            f"   = {per_judgement:,.0f} each"
        )
    if total_tokens:
        judged = sum(report["n_judgements"] for report in reports)
        add(f"  cumulative     {total_tokens:>9,} tokens across all {judged} judgements on disk")
    if total_retries:
        add("  A corrective retry is a SECOND full-prompt request, so a retried judgement")
        add("  costs about double -- and returns nothing at all if it then fails.")

    stopped = next((r for r in reports if r.get("quota_exhausted")), None)
    if stopped is not None:
        add("")
        add(f"  STOPPED ON QUOTA -- {outstanding} judgements still outstanding.")
        add(f"  {stopped['quota_message']}")
        add("")
        add("  This is a pause, not a failure. Re-run the identical command after the")
        add("  allowance resets and it continues; nothing already scored is judged again.")
        if per_judgement and outstanding:
            # Derived from what this session actually measured rather than a
            # figure written down once and left to go stale. An upper bound:
            # abstentions among the outstanding items are matched from the
            # answer text and cost nothing.
            remaining = per_judgement * outstanding
            add(
                f"  At {per_judgement:,.0f} tokens per judgement, the {outstanding} outstanding"
                f" are at most ~{remaining:,.0f} more"
            )
            add(
                f"  (~{(total_tokens + remaining) / 1000:,.0f}K for the whole run). An upper"
                " bound: abstentions among them cost nothing."
            )
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
