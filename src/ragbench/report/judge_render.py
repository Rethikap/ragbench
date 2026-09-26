"""Laying out the judge report for a terminal.

The labels carry weight here. A mean over judged answers only, an abstention
rate that is a count rather than a score, a self-consistency figure that bounds
every other number in the table, and percentage agreement that must never be
read without the kappa beside it -- each is a number that means something
different from what it looks like, and the table is where that gets said.
"""

from __future__ import annotations

from typing import Any


def _pct(value: float | None) -> str:
    return "--" if value is None else f"{value * 100:.0f}%"


def _num(value: float | None, places: int = 2) -> str:
    return "--" if value is None else f"{value:.{places}f}"


def render(report: dict[str, Any]) -> str:
    scales = list(report["scales"])
    lines: list[str] = []
    add = lines.append

    add("=" * 112)
    add("JUDGE REPORT")
    if report["judge_model"] == "stand-in":
        add("  *** CPU STAND-IN. These are lexical-overlap scores, not judgements.")
        add("  *** They exist to prove the stage runs offline. Never report them as results.")
    add(f"  judge        : {report['judge_model']}  (temperature {report['judge_temperature']})")
    add(
        f"  rubric       : {report['rubric_id']}"
        f"  (digest {report['rubric_digest']} -- of the TEXT, not the label)"
    )
    add(
        f"  judgements   : {report['n_judgements']}/{report['n_expected']}"
        f"  ({report['n_configs_judged']}/{report['n_configs']} configurations,"
        f" {report['n_questions']} questions x {report['passes']} passes)"
    )
    add("=" * 112)

    if not report["n_judgements"]:
        add("  Nothing judged yet. Run `ragbench judge`.")
        add("=" * 112)
        return "\n".join(lines)

    add("")
    add("--- SCORES  (means over JUDGED answers only; abstentions carry no scores)")
    header = f"  {'configuration':<32}"
    for scale in scales:
        header += f"{scale[:9]:>10}"
    header += f"{'n':>5}{'tokens':>8}{'abstain':>9}{'correct':>9}"
    add(header)
    for config in report["configs"]:
        if not config["n_judgements"]:
            add(f"  {config['config']:<32}   (not judged)")
            continue
        row = f"  {config['config']:<32}"
        for scale in scales:
            row += f"{_num(config['scores'].get(scale)):>10}"
        tokens = config["completion_tokens"].get("mean")
        row += f"{config['n_scored']:>5}{_num(tokens, 0):>8}"
        row += f"{_pct(config['abstention_rate']):>9}{_pct(config['correct_rate']):>9}"
        add(row)
    add("")
    add(
        "  n = answers actually scored. tokens = mean answer length, in the same table as"
    )
    add(
        "  the scores because the judge literature reports a length bias and the two must"
    )
    add("  not be read apart. abstain and correct are shares of all 20 answers.")

    add("")
    add("--- VERDICTS  (first pass; counts, out of 20 answers per configuration)")
    names = list(report["verdicts"]) + ["unparsed"]
    # 17 wide: "partially_correct" is exactly that, and truncating the one
    # verdict that names a partial result would be an unfortunate place to save
    # a character.
    add(f"  {'configuration':<32}" + "".join(f"{n[:17]:>19}" for n in names))
    for config in report["configs"]:
        if not config["n_judgements"]:
            continue
        counts = config["verdicts"]
        add(
            f"  {config['config']:<32}"
            + "".join(f"{counts.get(n, 0):>19}" for n in names)
        )

    add("")
    add("--- JUDGE AGAINST ITSELF  (two passes, temperature 0)")
    add("  This bounds every number above it: a gap between configurations smaller than")
    add("  the judge's disagreement with itself is not evidence of anything.")
    add("")
    add(
        f"  {'configuration':<32}{'items':>7}"
        + "".join(f"{s[:9] + ' k':>13}" for s in scales)
        + f"{'verdict k':>12}{'verdict =':>11}"
    )
    for config in report["configs"]:
        consistency = config.get("self_consistency") or {}
        if not consistency.get("measured"):
            continue
        row = f"  {config['config']:<32}{consistency['n_items']:>7}"
        for scale in scales:
            row += f"{_num(consistency[scale]['kappa']):>13}"
        verdict = consistency["verdict"]
        row += f"{_num(verdict['kappa']):>12}{_pct(verdict['exact_agreement']):>11}"
        add(row)
    add("")
    add("  k = Cohen's kappa; quadratic weights on the 1-5 scales, unweighted on the")
    add("  nominal verdict. 'verdict =' is raw agreement, shown only beside its kappa.")
    add("=" * 112)
    return "\n".join(lines)


def render_calibration(result: dict[str, Any], scales: list[str]) -> str:
    """Hand scores against the judge, on the blind sample."""
    lines: list[str] = []
    add = lines.append
    add("")
    add("=" * 112)
    add("CALIBRATION  (hand-scored blind sample against the judge)")
    add(
        f"  {result['n_paired']} of {result['n_sheet_items']} sheet items scored by hand"
        f" and paired with a judgement"
    )
    if result["unmatched_item_ids"]:
        add(f"  unmatched item ids: {', '.join(result['unmatched_item_ids'][:6])}")
    add("=" * 112)
    add("")
    add(
        f"  {'scale':<16}{'n':>5}{'kappa_w':>10}{'spearman':>10}{'exact':>8}{'+-1':>8}"
        f"{'human':>8}{'judge':>8}{'diff':>8}"
    )
    for scale in scales:
        summary = result["scales"][scale]
        add(
            f"  {scale:<16}{summary['n']:>5}{_num(summary['kappa']):>10}"
            f"{_num(summary['spearman']):>10}{_pct(summary['exact_agreement']):>8}"
            f"{_pct(summary['within_one']):>8}{_num(summary['mean_human']):>8}"
            f"{_num(summary['mean_judge']):>8}{_num(summary['mean_difference']):>8}"
        )
    verdict = result["verdict"]
    add("")
    add(
        f"  {'verdict':<16}{verdict['n']:>5}{_num(verdict['kappa']):>10}{'--':>10}"
        f"{_pct(verdict['exact_agreement']):>8}"
    )
    flagged = [
        (name, summary["judge_pass_means"])
        for name, summary in result["scales"].items()
        if summary.get("judge_pass_means")
    ]
    if flagged:
        add("")
        for name, count in flagged:
            add(
                f"  {count} of {name}'s judge scores are the mean of two passes that"
                " disagreed (e.g. 4.5),"
            )
        add("  so those rows CANNOT match an integer hand score and depress `exact`.")
        add("  kappa_w and spearman treat them as the near misses they are.")
    add("")
    add("  kappa_w = quadratically weighted Cohen's kappa; the verdict's is unweighted,")
    add("  because its four categories have no order and weighting would invent one.")
    add("  diff = judge mean minus human mean. A consistent offset with a high Spearman is")
    add("  a calibration difference, not a disagreement about which answers are better.")
    add("  exact agreement is inflated by chance on a 5-point scale; read kappa first.")
    add("")
    add("  items per configuration in the paired sample:")
    add("    " + "  ".join(f"{k}:{v}" for k, v in result["items_per_config"].items()))
    add("=" * 112)
    return "\n".join(lines)
