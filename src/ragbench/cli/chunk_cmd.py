"""The `chunk` subcommand: build one chunk set per chunking factor level."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ..chunking.pipeline import run_chunk
from ..config import DEFAULT_DATA_ROOT, MANIFEST_FILENAME
from ..ingest.manifest import ManifestError

EXIT_DATA = 5


def add_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DEFAULT_DATA_ROOT,
        metavar="DIR",
        help="root for the parsed-paper and chunk caches (default: %(default)s)",
    )
    parser.add_argument(
        "--chunking",
        action="append",
        metavar="LEVEL",
        help="chunking factor level to build, repeatable. Defaults to every level in "
        "factors.yaml, since the design needs all of them. The embedding factor is "
        "deliberately not selectable here: chunk boundaries do not depend on it",
    )


def run(args: argparse.Namespace, resolved: dict[str, Any], directory: Path) -> int:
    manifest_path = Path(args.config).parent / MANIFEST_FILENAME
    try:
        reports = run_chunk(
            resolved,
            manifest_path,
            args.data_root,
            levels=args.chunking,
            on_progress=lambda message: print(f"  {message}", end="\r", flush=True),
        )
    except (ManifestError, ValueError) as exc:
        print(f"ragbench: {exc}")
        return EXIT_DATA

    print()
    identifiers = set()
    for report in reports:
        identifiers.add(report["chunk_set_id"])
        state = "reused" if report["reused"] else "built"
        print(f"{report['level']:<10} {state:<7} chunk_set_id {report['chunk_set_id']}")
        print(f"           chunks   {report['n_chunks']:,} from {report['n_papers']} papers")
        print(f"           levels   {report['separator_levels'] or 'n/a (fixed windows)'}")
        print(f"           path     {report['directory']}")
    if len(reports) > 1:
        print(f"\ndistinct chunk sets: {len(identifiers)} (expected one per chunking level)")
    return 0
