"""Thesis figures, as SVG and PNG.

matplotlib is imported inside each function, so `import ragbench` stays
stdlib-cheap and the analysis extra is genuinely optional.

Three decisions apply to every figure here.

**One committed look, light, no dark variant.** These are print figures. A
theme-switching palette is the right answer for a page someone reads on a
screen; it is not the right answer for a PDF that gets printed in greyscale by
an examiner.

**Colour follows the entity, never the rank.** The chunking arm keeps its hue
wherever it appears, so a reader who learns "blue is fixed" on one figure is not
re-taught on the next. The main-effect plot draws every point in one colour for
the same reason: colouring the bars by which way they happen to point would
encode the result in the palette and make a near-zero effect look like a
category.

**Identity is never carried by colour alone.** Two series always get a legend,
and the forest plot spells out each interval as text beside it -- which also
means the figure survives being printed in greyscale.

The palette is the validated categorical default: slot 1 `#2a78d6`, slot 2
`#eb6834`. Checked with the skill's validator against the `#fcfcfb` surface --
worst adjacent CVD delta-E 24.7 (protan), normal-vision 33.6, both far above
their floors.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SOFT = "#52514e"
GRID = "#d9d8d4"
SERIES = ("#2a78d6", "#eb6834")
ZERO_LINE = "#8a8984"


def _save(figure: Any, directory: Path, stem: str) -> list[str]:
    """Both formats, same figure. SVG for the thesis, PNG for everything else."""
    directory.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for suffix in ("svg", "png"):
        path = directory / f"{stem}.{suffix}"
        figure.savefig(path, format=suffix, dpi=200, bbox_inches="tight",
                       facecolor=SURFACE)
        written.append(str(path))
    return written


def _style(axes: Any) -> None:
    """Recessive furniture: the data should be the darkest thing on the page."""
    axes.set_facecolor(SURFACE)
    for side in ("top", "right"):
        axes.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        axes.spines[side].set_color(GRID)
    axes.tick_params(colors=INK_SOFT, labelsize=9, length=3)
    axes.grid(True, axis="x", color=GRID, linewidth=0.6, alpha=0.9)
    axes.set_axisbelow(True)


def main_effects(report: dict[str, Any], directory: Path) -> dict[str, Any]:
    """Dot-and-interval per factor: the effect, and how well it is pinned down.

    A forest plot rather than bars, because the quantity of interest is a
    difference with an interval around it. Bars would anchor at zero and imply a
    ratio scale that a difference does not have, and would hide the interval
    behind the fill.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = [row for row in report["primaries"] if row["n"]]
    if not rows:
        return {"written": [], "skipped": "no primary comparison has data yet"}
    rows = sorted(rows, key=lambda row: (row["family"], row["factor"]))

    height = max(2.2, 0.62 * len(rows) + 1.3)
    figure, axes = plt.subplots(figsize=(8.2, height), facecolor=SURFACE)
    _style(axes)
    positions = list(range(len(rows)))[::-1]

    for position, row in zip(positions, rows, strict=True):
        low = row["ci_low"] if row["ci_low"] is not None else row["mean_difference"]
        high = row["ci_high"] if row["ci_high"] is not None else row["mean_difference"]
        axes.plot([low, high], [position, position], color=SERIES[0], linewidth=2.0,
                  solid_capstyle="round", zorder=2)
        axes.plot([row["mean_difference"]], [position], marker="o", markersize=8,
                  color=SERIES[0], markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=3)

    axes.axvline(0.0, color=ZERO_LINE, linewidth=1.0, linestyle=(0, (4, 3)), zorder=1)
    axes.set_yticks(positions)
    axes.set_yticklabels(
        [f"{row['research_question']}  {row['label']}\n{row['metric_label']}" for row in rows],
        fontsize=9, color=INK,
    )
    axes.set_xlabel("difference (positive favours the second level)", fontsize=9, color=INK_SOFT)
    axes.set_title("Main effects with 95% bootstrap intervals", fontsize=11, color=INK,
                   loc="left", pad=12)

    # The numbers as a table column beside the plot -- a forest plot's second
    # half, and what makes the figure readable when printed in greyscale.
    # Annotated in axes fractions so the column sits OUTSIDE the data area:
    # placed inside an extended x-range it landed on top of the gridlines.
    axes.set_ylim(-0.7, len(rows) - 0.3)
    for position, row in zip(positions, rows, strict=True):
        interval = (
            f"{row['mean_difference']:+.3f}  [{row['ci_low']:+.3f}, {row['ci_high']:+.3f}]"
            if row["ci_low"] is not None
            else f"{row['mean_difference']:+.3f}"
        )
        axes.annotate(
            f"{interval}   n={row['n']}",
            xy=(1.03, position),
            xycoords=("axes fraction", "data"),
            fontsize=8.5, color=INK_SOFT, va="center", family="monospace",
            annotation_clip=False,
        )

    written = _save(figure, directory, "main_effects")
    plt.close(figure)
    return {"written": written, "n_rows": len(rows)}


def coverage_per_config(report: dict[str, Any], table: Any, directory: Path) -> dict[str, Any]:
    """Mean span coverage per configuration, coloured by chunking arm."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    configs = [row["config"] for row in report["availability"]["per_config"]]
    means: list[float] = []
    for name in configs:
        values = [
            row["span_coverage"]
            for (config, _), row in table.items()
            if config == name and row.get("span_coverage") is not None
        ]
        means.append(sum(values) / len(values) if values else 0.0)
    if not any(means):
        return {"written": [], "skipped": "no span coverage recorded"}

    arms = sorted({name.split("-", 1)[0] for name in configs})
    colours = {arm: SERIES[index % len(SERIES)] for index, arm in enumerate(arms)}

    figure, axes = plt.subplots(figsize=(8.2, 4.0), facecolor=SURFACE)
    _style(axes)
    axes.grid(True, axis="y", color=GRID, linewidth=0.6)
    axes.grid(False, axis="x")
    positions = list(range(len(configs)))
    # width 0.78 leaves a visible gap between neighbours rather than a solid band.
    axes.bar(positions, means, width=0.78,
             color=[colours[name.split("-", 1)[0]] for name in configs], zorder=2)
    for position, value in zip(positions, means, strict=True):
        axes.text(position, value + 0.015, f"{value:.2f}", ha="center", fontsize=8.5,
                  color=INK_SOFT)

    axes.set_xticks(positions)
    # Stacked over three lines rather than two: at eight configurations the
    # two-line form ran "fixed-specter2" into "recursive-bge". Each part stays
    # named in text, so identity never rests on colour alone.
    axes.set_xticklabels(
        ["\n".join(name.replace("rerank_", "rerank ").split("-")) for name in configs],
        fontsize=7.5, color=INK,
    )
    axes.set_ylim(0, 1.08)
    axes.set_ylabel("mean span coverage", fontsize=9, color=INK_SOFT)
    axes.set_title("Span coverage by configuration", fontsize=11, color=INK, loc="left", pad=22)
    handles = [plt.Rectangle((0, 0), 1, 1, color=colours[arm]) for arm in arms]
    # Above the axes, not inside it: in the plot area the legend covered a bar.
    axes.legend(handles, arms, title="chunking", frameon=False, fontsize=9,
                title_fontsize=9, loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=2)

    written = _save(figure, directory, "coverage_per_config")
    plt.close(figure)
    return {"written": written}


def chunk_lengths(resolved: dict[str, Any], data_root: Path, directory: Path) -> dict[str, Any]:
    """Chunk-length distribution per arm -- the geometry the whole design rests on."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from ..cache_keys import chunk_set_key
    from ..chunking.pipeline import arm_params, load_chunks
    from ..config import chunk_set_dir

    digest = str(resolved["corpus"].get("manifest_sha", ""))
    series: dict[str, list[int]] = {}
    for level in resolved["factors"]["chunking"]:
        directory_for = chunk_set_dir(chunk_set_key(digest, arm_params(resolved, level)), data_root)
        if not (directory_for / "chunks.jsonl").is_file():
            continue
        series[level] = [chunk.n_tokens for chunk in load_chunks(directory_for)]
    if not series:
        return {"written": [], "skipped": "no chunk sets on disk"}

    figure, axes = plt.subplots(figsize=(8.2, 4.0), facecolor=SURFACE)
    _style(axes)
    # Counts are read off the vertical axis here, so that is where the grid goes.
    axes.grid(True, axis="y", color=GRID, linewidth=0.6)
    axes.grid(False, axis="x")
    top = max(max(values) for values in series.values())
    bins = list(range(0, int(top) + 20, 20))
    for index, (level, values) in enumerate(sorted(series.items())):
        colour = SERIES[index % len(SERIES)]
        axes.hist(values, bins=bins, color=colour, alpha=0.45, zorder=2,
                  label=f"{level}  (n={len(values):,}, median {sorted(values)[len(values) // 2]})")
        axes.hist(values, bins=bins, histtype="step", color=colour, linewidth=1.6, zorder=3)

    axes.set_xlabel("chunk length (canonical tokens)", fontsize=9, color=INK_SOFT)
    axes.set_ylabel("chunks", fontsize=9, color=INK_SOFT)
    axes.set_title("Chunk length by arm", fontsize=11, color=INK, loc="left", pad=12)
    axes.legend(frameon=False, fontsize=9)

    written = _save(figure, directory, "chunk_lengths")
    plt.close(figure)
    return {"written": written}


def build_all(
    resolved: dict[str, Any],
    report: dict[str, Any],
    table: Any,
    data_root: Path,
    run_directory: Path,
) -> dict[str, Any]:
    directory = Path(run_directory) / "figures"
    return {
        "directory": str(directory),
        "main_effects": main_effects(report, directory),
        "coverage_per_config": coverage_per_config(report, table, directory),
        "chunk_lengths": chunk_lengths(resolved, data_root, directory),
    }
