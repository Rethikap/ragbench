"""The figures' design system: palette, surfaces, and how a figure is saved.

Separated from the figures themselves because these are *parameters* -- the
values a design system supplies -- and the figures are the drawings that consume
them. Changing a hue should not mean opening a module full of plotting code.

matplotlib is imported inside each drawing function, so `import ragbench`
stays stdlib-cheap and the analysis extra is genuinely optional.

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
#: The validated categorical order, taken in the sequence the palette documents
#: rather than reordered -- a reordering was tried and validated WORSE (adjacent
#: CVD delta-E 6.1 against 9.1). Slots 1 and 2 carry the two chunking arms
#: wherever they appear, so a reader who learns "blue is fixed" is not re-taught.
SERIES = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300")
#: Secondary encoding for line charts, because three of the six slots sit below
#: 3:1 against the surface and the validator marks that relief-required. Every
#: series is also named in the legend and its number repeated in the report's
#: table, which is the relief; the marker shape is the belt.
MARKERS = ("o", "s", "^", "D", "v", "P")
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


