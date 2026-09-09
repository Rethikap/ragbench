"""The `ingest` subcommand: one-time corpus freeze, then resumable parsing."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ..config import DEFAULT_DATA_ROOT, MANIFEST_FILENAME
from ..ingest.manifest import ManifestError
from ..ingest.ncbi import NcbiError
from ..ingest.pipeline import run_ingest, run_selection

EXIT_DATA = 5


def add_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        metavar="DIR",
        help="root for the raw-JATS and parsed-paper caches (default: %(default)s). "
        "Ingest is factor-independent, so its caches are shared by all 8 runs and "
        "live here rather than inside any one run directory",
    )
    parser.add_argument(
        "--select-corpus",
        action="store_true",
        help="ONE-TIME: run the PMC query, select the corpus, write "
        f"configs/{MANIFEST_FILENAME} and freeze its digest into corpus.yaml. "
        "After this the corpus is immutable and ingest never queries NCBI again",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="allow --select-corpus to overwrite an existing frozen manifest",
    )


def run(args: argparse.Namespace, resolved: dict[str, Any], directory: Path) -> int:
    configs_dir = Path(args.config).parent
    manifest_path = configs_dir / MANIFEST_FILENAME
    try:
        if args.select_corpus:
            return _select(args, resolved, manifest_path, configs_dir)
        return _ingest(args, resolved, manifest_path)
    except (ManifestError, NcbiError, ValueError) as exc:
        print(f"ragbench: {exc}")
        return EXIT_DATA


def _select(
    args: argparse.Namespace,
    resolved: dict[str, Any],
    manifest_path: Path,
    configs_dir: Path,
) -> int:
    if manifest_path.exists() and not args.force:
        print(
            f"ragbench: {manifest_path} already exists and the corpus is frozen.\n"
            "  Re-selecting would change every downstream cache id. Pass --force if "
            "you really mean to rebuild it."
        )
        return EXIT_DATA

    print("Selecting corpus (this queries NCBI; it runs once and is then frozen)...", flush=True)
    report = run_selection(
        resolved,
        manifest_path,
        configs_dir / "corpus.yaml",
        args.data_root,
        on_progress=lambda message: print(f"  {message}", end="\r", flush=True),
    )
    survey = report["survey"]
    print(f"\n  candidates enumerated : {survey['unique_total']} unique")
    print(f"  per-year windows      : {survey['per_year']}")
    print(f"  whole-range count     : {survey['whole_range_count']}")
    print(f"  partition exact       : {survey['partition_is_exact']}")
    print(f"  candidates considered : {report['considered']} of pool {report['pool_size']}")
    print(f"  rejected              : {report['rejected'] or 'none'}")
    print(f"  papers selected       : {len(report['entries'])}")
    print(f"  manifest              : {report['manifest_path']}")
    print(f"  manifest_sha          : {report['manifest_sha']}  (frozen into corpus.yaml)")
    if report["failures"]:
        print(f"  failures              : {len(report['failures'])}")
        for failure in report["failures"][:10]:
            print(f"    {failure['pmcid']} [{failure['stage']}] {failure['reason']}")
    if report["short"]:
        print("  WARNING: fewer papers than target_papers; enlarge candidate_pool")
        return EXIT_DATA
    return 0


def _ingest(args: argparse.Namespace, resolved: dict[str, Any], manifest_path: Path) -> int:
    report = run_ingest(
        resolved,
        manifest_path,
        args.data_root,
        on_progress=lambda message: print(f"  {message}", end="\r", flush=True),
    )
    print(f"\nIngest complete for manifest_sha {report['manifest_sha']}")
    print(f"  papers in manifest : {report['n_manifest']}")
    print(f"  newly fetched      : {report['n_fetched']}")
    print(f"  newly parsed       : {report['n_parsed']}")
    print(f"  already cached     : {report['n_cached']}")
    print(f"  parsed cache       : {report['parsed_dir']}")
    print(f"  rollup             : {report['rollup']}")
    if report["failures"]:
        print(f"  FAILURES           : {len(report['failures'])}")
        for failure in report["failures"]:
            print(f"    {failure['pmcid']} [{failure['stage']}] {failure['reason']}")
        return EXIT_DATA
    return 0
