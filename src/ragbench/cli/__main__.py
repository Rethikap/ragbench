"""ragbench command-line entry point.

Seven stages run in order; each resolves the same config and derives its own
output directory from the config digest, so results can never be mixed between
incomparable configurations. `gold` sits alongside them rather than among them,
because the evaluation set is an input to the pipeline, not a step in it.

Note the flag vocabulary: there is deliberately no way to say "retrieve N chunks
for the generator". See :func:`_add_retrieval_options`.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from .. import __version__
from ..config import (
    DEFAULT_RUNS_ROOT,
    ConfigError,
    dump_resolved,
    resolve_config,
    run_dir,
)
from . import (
    chunk_cmd,
    generate_cmd,
    gold_cmd,
    index_cmd,
    ingest_cmd,
    report_cmd,
    retrieve_cmd,
)

STAGES: tuple[str, ...] = (
    "ingest",
    "chunk",
    "index",
    "retrieve",
    "generate",
    "judge",
    "report",
)

#: Subcommands that are not pipeline stages. The gold set is an *input* to
#: `retrieve`, built once and frozen like the corpus manifest; listing it in
#: STAGES would imply it is rebuilt per run, which is what freezing prevents.
EXTRA_COMMANDS: tuple[str, ...] = ("gold",)

COMMAND_HELP: dict[str, str] = {
    "gold": "build and freeze the character-span gold set used to score retrieval",
}

STAGE_HELP: dict[str, str] = {
    "ingest": "fetch and parse the frozen PMC corpus into ParsedPaper records",
    "chunk": "split parsed papers into chunks using the chunking factor level",
    "index": "embed chunks and build the Chroma index for one embedding arm",
    "retrieve": "select context chunks up to the token budget, optionally reranked",
    "generate": "answer each query from the retrieved context",
    "judge": "score generated answers against the rubric",
    "report": "aggregate the 8 runs into the factorial comparison",
}

# Exit codes. 0/2 are argparse's own (success, usage error); the rest are ours.
EXIT_OK = 0
EXIT_CONFIG = 3
EXIT_NOT_IMPLEMENTED = 4

# Stage -> handler. ``None`` means "declared but not built yet": the subcommand
# still parses and still resolves config, it just refuses to pretend it ran.
Handler = Callable[[argparse.Namespace, dict[str, Any], Path], int]
HANDLERS: dict[str, Handler | None] = dict.fromkeys(STAGES)
HANDLERS["ingest"] = ingest_cmd.run
HANDLERS["chunk"] = chunk_cmd.run
HANDLERS["report"] = report_cmd.run
HANDLERS["index"] = index_cmd.run
HANDLERS["retrieve"] = retrieve_cmd.run
HANDLERS["generate"] = generate_cmd.run
HANDLERS["gold"] = gold_cmd.run

#: Extra options registered per stage, beyond the common ones.
STAGE_OPTIONS: dict[str, Callable[[argparse.ArgumentParser], None]] = {
    "ingest": ingest_cmd.add_options,
    "chunk": chunk_cmd.add_options,
    "index": index_cmd.add_options,
    "retrieve": retrieve_cmd.add_options,
    "generate": generate_cmd.add_options,
    "report": report_cmd.add_options,
    "gold": gold_cmd.add_options,
}


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        metavar="PATH",
        help="path to configs/base.yaml; corpus.yaml, factors.yaml and gold.yaml are "
        "read from the same directory",
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=DEFAULT_RUNS_ROOT,
        metavar="DIR",
        help="root for run directories (default: %(default)s); the directory itself "
        "is named after the config digest",
    )


def _add_retrieval_options(parser: argparse.ArgumentParser) -> None:
    """Retrieval flags.

    There is intentionally no --top-k / -k / --num-chunks here, and there never
    may be. The number of chunks that reach the generator is an *output* of
    filling a fixed token budget, not an input a caller may set. Making the wrong
    concept inexpressible at the interface keeps it out of the implementation.
    """
    parser.add_argument(
        "--budget-tokens",
        type=int,
        default=None,
        metavar="N",
        help="override retrieval.context_token_budget: the constant generator-token "
        "budget every configuration fills. THE controlled variable. Chunks are added "
        "in rank order until the next one would overflow; none is ever truncated",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=None,
        metavar="N",
        help="rerank candidate pool size: how many dense hits are fetched before "
        "reranking. This is NOT a generator context parameter and NOT the number of "
        "chunks placed in the prompt -- that is decided solely by --budget-tokens",
    )


def build_parser() -> argparse.ArgumentParser:
    """Construct the full parser.

    Exposed as a function so tests can introspect every registered option string
    without running anything.
    """
    parser = argparse.ArgumentParser(
        prog="ragbench",
        description="Controlled 2x2x2 factorial benchmark of RAG design choices.",
    )
    parser.add_argument("--version", action="version", version=f"ragbench {__version__}")
    subparsers = parser.add_subparsers(dest="stage", metavar="COMMAND", required=True)

    for stage in (*STAGES, *EXTRA_COMMANDS):
        help_text = STAGE_HELP.get(stage) or COMMAND_HELP[stage]
        subparser = subparsers.add_parser(
            stage,
            help=help_text,
            description=help_text.capitalize() + ".",
        )
        _add_common_options(subparser)
        if stage == "retrieve":
            _add_retrieval_options(subparser)
        register_extra = STAGE_OPTIONS.get(stage)
        if register_extra is not None:
            register_extra(subparser)

    return parser


def _not_implemented(stage: str, directory: Path) -> str:
    return (
        f"ragbench: stage '{stage}' is not implemented yet.\n"
        f"  The config resolved cleanly and this run's directory would be {directory}.\n"
        f"  Nothing was read, written or cached."
    )


def _survive_a_legacy_console() -> None:
    """Never let a character the console cannot encode end a report.

    Reports quote the corpus, and the corpus is biomedical: Abeta is written
    with a beta, concentrations carry mu and >=, dashes are en dashes. A Windows
    console at cp1252 raises UnicodeEncodeError on any of them, so
    `report generation` died on the first answer that quoted a paper properly --
    after the work was done, with nothing printed.

    Replacing the character is the right loss to take. The stream's own encoding
    is kept rather than forced to UTF-8, because emitting UTF-8 bytes at a cp1252
    console turns every accented character into mojibake, which is harder to read
    than a question mark and easy to mistake for a generation defect. Each report
    also writes a JSON artefact in UTF-8, and that copy is exact.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError, OSError):  # pragma: no cover - not a text stream
            pass


def main(argv: Sequence[str] | None = None) -> int:
    _survive_a_legacy_console()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        resolved = resolve_config(args.config)
    except ConfigError as exc:
        print(f"ragbench: {exc}", file=sys.stderr)
        return EXIT_CONFIG

    directory = run_dir(resolved, args.runs_root)

    handler = HANDLERS.get(args.stage)
    if handler is None:
        # Resolve first, refuse second: a bad --config is reported as a config
        # error even for a stage that does not exist yet.
        print(_not_implemented(args.stage, directory), file=sys.stderr)
        return EXIT_NOT_IMPLEMENTED

    dump_resolved(resolved, directory)
    return handler(args, resolved, directory)


if __name__ == "__main__":
    sys.exit(main())
