"""The four thesis figures.

Each answers one question and says which. The design-system parameters they draw
with -- palette, surfaces, how a figure is saved -- live in
:mod:`ragbench.report.figure_style`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .figure_style import GRID, INK, INK_SOFT, MARKERS, SERIES, SURFACE, ZERO_LINE, _save, _style


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
        "power_against_n": power_against_n(report, directory),
    }


def power_against_n(report: dict[str, Any], directory: Path) -> dict[str, Any]:
    """Power against sample size per primary, with the 80% target marked.

    A line chart because the quantity is a curve over a continuous axis and its
    shape is the point -- where it turns over says how much a few more questions
    would buy. The title says "future study" because a power curve is the one
    figure a reader is most likely to mistake for a statement about the study
    that produced it.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = [row for row in report["primaries"] if row.get("power_curve")]
    if not rows:
        return {"written": [], "skipped": "no primary comparison has a power curve"}

    figure, axes = plt.subplots(figsize=(8.2, 4.4), facecolor=SURFACE)
    _style(axes)
    axes.grid(True, axis="y", color=GRID, linewidth=0.6)

    target = rows[0]["sample_size"]["target_power"]
    axes.axhline(target, color=ZERO_LINE, linewidth=1.0, linestyle=(0, (4, 3)), zorder=1)
    axes.annotate(
        f"{target:.0%} power",
        xy=(0.995, target), xycoords=("axes fraction", "data"),
        ha="right", va="bottom", fontsize=8.5, color=INK_SOFT,
    )

    for index, row in enumerate(rows):
        # Fixed order, never cycled: a seventh series would fold into a second
        # figure rather than reuse slot 1 and collide with it.
        colour = SERIES[index] if index < len(SERIES) else INK_SOFT
        marker = MARKERS[index] if index < len(MARKERS) else "x"
        sizes = [point["n"] for point in row["power_curve"]]
        powers = [point["power"] for point in row["power_curve"]]
        needed = row["sample_size"]["estimates"]["observed"]["at_alpha"].get("n")
        label = f"{row['research_question']} {row['label']}"
        if needed:
            label += f"  (n≈{needed})"
        axes.plot(sizes, powers, color=colour, linewidth=2.0, marker=marker, markersize=5,
                  markeredgecolor=SURFACE, markeredgewidth=1.0, zorder=3, label=label)
        if needed and needed <= max(sizes):
            axes.plot([needed], [target], marker="|", markersize=11, color=colour, zorder=4)

    axes.set_xlabel("questions in a future gold set", fontsize=9, color=INK_SOFT)
    axes.set_ylabel("power", fontsize=9, color=INK_SOFT)
    axes.set_ylim(0, 1.02)
    axes.set_title(
        "Power against sample size for a FUTURE study\n"
        "planning estimate at the effects observed here, not the power of this study",
        fontsize=11, color=INK, loc="left", pad=12,
    )
    axes.legend(frameon=False, fontsize=8.5, loc="lower right")

    written = _save(figure, directory, "power_against_n")
    plt.close(figure)
    return {"written": written}
