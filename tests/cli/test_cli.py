"""CLI behaviour, and CI enforcement of invariant I1.

CLAUDE.md *documents* that the number of chunks reaching the generator is an
output of filling a token budget, never an input. This file makes that fail a
build: if anyone adds a --top-k (or a synonym) to any subcommand, the suite goes
red. Documentation degrades; a failing test does not.

argparse exposes no public introspection API, so the walkers below reach into
``_actions`` and ``_SubParsersAction``. Private, but stable across CPython 3.x
and the only way to see every registered option string.
"""

from __future__ import annotations

import argparse
import re
from collections.abc import Iterator
from pathlib import Path

import pytest

from ragbench.cli.__main__ import (
    EXIT_CONFIG,
    EXIT_NOT_IMPLEMENTED,
    HANDLERS,
    STAGES,
    build_parser,
    main,
)

PENDING_STAGES = [stage for stage in STAGES if HANDLERS[stage] is None]

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_CONFIG = REPO_ROOT / "configs" / "base.yaml"

# Names that express "give me N chunks/docs/results". The guard errs toward
# false positives on purpose: a legitimate flag caught here costs one
# conversation, whereas a smuggled constant-k parameter silently invalidates the
# whole experiment.
BANNED_EXACT = frozenset(
    {
        "k",
        "n",
        "topk",
        "top-k",
        "top-n",
        "topn",
        "num-chunks",
        "n-chunks",
        "nchunks",
        "chunk-count",
        "max-chunks",
        "num-passages",
        "n-passages",
        "num-docs",
        "n-docs",
        "num-results",
        "n-results",
        "num-context",
        "n-context",
        "limit",
        "count",
    }
)
BANNED_PATTERN = re.compile(
    r"^(top|num|n|max|first)[-_]?"
    r"(k|chunks?|docs?|documents?|passages?|results?|hits?|contexts?)$"
)


def _normalise(option: str) -> str:
    return option.lstrip("-").lower().replace("_", "-")


def _is_banned(option: str) -> bool:
    name = _normalise(option)
    return name in BANNED_EXACT or bool(BANNED_PATTERN.match(name))


def _iter_parsers(parser: argparse.ArgumentParser) -> Iterator[argparse.ArgumentParser]:
    yield parser
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for subparser in action.choices.values():
                yield from _iter_parsers(subparser)


def _all_options(parser: argparse.ArgumentParser) -> list[tuple[str, str]]:
    return [
        (subparser.prog, option)
        for subparser in _iter_parsers(parser)
        for action in subparser._actions
        for option in action.option_strings
    ]


def _offenders(parser: argparse.ArgumentParser) -> list[tuple[str, str]]:
    return [(prog, opt) for prog, opt in _all_options(parser) if _is_banned(opt)]


def _subparser(parser: argparse.ArgumentParser, name: str) -> argparse.ArgumentParser:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action.choices[name]
    raise AssertionError("parser has no subcommands")


# --------------------------------------------------------------------- invariant I1


def test_no_subcommand_exposes_a_chunk_count_flag() -> None:
    offenders = _offenders(build_parser())
    assert not offenders, (
        "constant-k flags found: "
        + ", ".join(f"{prog} {opt}" for prog, opt in offenders)
        + ". The chunk count is an output of filling --budget-tokens, not an input."
    )


def test_the_guard_would_catch_a_smuggled_flag() -> None:
    """The guard must have teeth: prove it fails when the bad flag is present."""
    parser = build_parser()
    assert not _offenders(parser)
    _subparser(parser, "retrieve").add_argument("--top-k", type=int)
    assert _offenders(parser) == [("ragbench retrieve", "--top-k")]


@pytest.mark.parametrize("smuggled", ["-k", "--num-chunks", "--n_results", "--max-passages"])
def test_the_guard_catches_synonyms(smuggled: str) -> None:
    parser = build_parser()
    _subparser(parser, "retrieve").add_argument(smuggled, type=int)
    assert _offenders(parser)


def test_retrieve_controls_context_by_token_budget() -> None:
    options = {opt for prog, opt in _all_options(build_parser()) if prog.endswith("retrieve")}
    assert "--budget-tokens" in options


def test_depth_is_documented_as_a_rerank_pool() -> None:
    depth = next(
        action
        for action in _subparser(build_parser(), "retrieve")._actions
        if "--depth" in action.option_strings
    )
    help_text = (depth.help or "").lower()
    assert "rerank" in help_text
    assert "not" in help_text and "budget-tokens" in help_text


# --------------------------------------------------------------------- plumbing


def test_help_lists_every_stage(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        build_parser().parse_args(["--help"])
    assert exit_info.value.code == 0
    printed = capsys.readouterr().out
    for stage in STAGES:
        assert stage in printed


@pytest.mark.parametrize("stage", PENDING_STAGES)
def test_unimplemented_stage_exits_nonzero_without_traceback(
    stage: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main([stage, "--config", str(BASE_CONFIG), "--runs-root", str(tmp_path)])
    assert code == EXIT_NOT_IMPLEMENTED
    printed = capsys.readouterr().err
    assert "not implemented yet" in printed
    assert "Traceback" not in printed
    assert list(tmp_path.iterdir()) == [], "an unimplemented stage must not write anything"


def test_missing_config_is_a_clean_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["chunk", "--config", str(tmp_path / "absent.yaml"), "--runs-root", str(tmp_path)])
    assert code == EXIT_CONFIG
    printed = capsys.readouterr().err
    assert "config file not found" in printed
    assert "Traceback" not in printed


def test_config_is_required() -> None:
    with pytest.raises(SystemExit) as exit_info:
        build_parser().parse_args(["chunk"])
    assert exit_info.value.code == 2
