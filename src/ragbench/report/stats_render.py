"""Laying out the analysis.

Two labels do the heavy lifting and neither is decoration. **n** is printed on
every row, because a comparison over 20 questions and one over 6 are not the
same evidence and a table without it invites reading them as though they were.
And **exploratory** is printed on everything outside the pre-specified family,
because an uncorrected p-value from a list of twenty is not the same object as a
corrected one from a list of six.
"""

from __future__ import annotations

from typing import Any


def _num(value: float | None, places: int = 3, sign: bool = False) -> str:
    if value is None:
        return "--"
    return f"{value:+.{places}f}" if sign else f"{value:.{places}f}"


def _interval(row: dict[str, Any]) -> str:
    if row["ci_low"] is None:
        return "--"
    return f"[{row['ci_low']:+.3f}, {row['ci_high']:+.3f}]"


def _stars(row: dict[str, Any]) -> str:
    if row.get("p_holm") is None:
        return ""
    return " *" if row.get("significant") else ""


def render(report: dict[str, Any]) -> str:
    lines: list[str] = []
    add = lines.append
    availability = report["availability"]

    add("=" * 112)
    add("STATISTICS")
    add(f"  gold_set_sha        : {report['gold_set_sha']}")
    add(
        f"  analysis plan       : configs/stats.yaml"
        f"  (digest {report['prespecification_digest']}, fixed before the judge results)"
    )
    plan = report["prespecification"]
    add(
        "  primary metrics     : "
        + ",  ".join(f"{family} -> {metric}" for family, metric in sorted(plan["primary"].items()))
    )
    add(
        f"  bootstrap           : {plan['bootstrap_resamples']:,} resamples of QUESTIONS,"
        f" seed {plan['bootstrap_seed']}, {plan['confidence']:.0%} percentile interval"
    )
    add("=" * 112)

    add("")
    add("--- WHAT IS AVAILABLE")
    add(
        f"  judgements {availability['n_judgements']}/{availability['n_judgements_expected']}"
        f"  across {len(availability['judged_configs'])}/{availability['n_configs']}"
        " configurations"
    )
    if availability["unjudged_configs"]:
        add("  not yet judged:")
        for name in availability["unjudged_configs"]:
            add(f"    {name}")
        add("")
        add("  A factor's difference needs EVERY cell it averages over. Any comparison")
        add("  touching an unjudged configuration is reported with n=0 rather than")
        add("  averaged over whichever cells happen to exist -- those would be different")
        add("  estimators wearing one name. Re-run this report when judging completes.")

    add("")
    add("--- PRIMARY  (pre-specified; Holm-corrected across these six only)")
    add(
        f"  {'RQ':<4}{'comparison':<30}{'metric':<17}{'n':>4}{'diff':>9}"
        f"{'95% CI':>22}{'effect':>9}{'p':>9}{'p_holm':>9}"
    )
    for row in report["primaries"]:
        add(
            f"  {row['research_question']:<4}{row['label'][:29]:<30}{row['metric'][:16]:<17}"
            f"{row['n']:>4}{_num(row['mean_difference'], sign=True):>9}{_interval(row):>22}"
            f"{_num(row['effect_size'], 2, True):>9}{_num(row['p_value'], 4):>9}"
            f"{_num(row.get('p_holm'), 4):>9}{_stars(row)}"
        )
    add("")
    add("  diff = mean over questions of (second level - first level), each question's")
    add("  value being the average of its 4 paired comparisons. effect = matched-pairs")
    add("  rank-biserial. * = significant after Holm at alpha "
        f"{plan['alpha']}.")

    incomplete = [row for row in report["primaries"] if not row["n"]]
    if incomplete:
        add("")
        add(f"  {len(incomplete)} primary comparisons have no data yet:")
        for row in incomplete:
            add(
                f"    {row['research_question']} {row['metric']:<16}"
                f" needs {', '.join(row['missing_configs'][:3])}"
                + (" ..." if len(row["missing_configs"]) > 3 else "")
            )

    lines.extend(_sample_size(report))

    add("")
    add("--- EXPLORATORY  (uncorrected; NOT evidence on their own)")
    add(
        f"  {'comparison':<30}{'metric':<22}{'n':>4}{'diff':>9}{'95% CI':>22}"
        f"{'effect':>9}{'p':>9}"
    )
    for row in report["exploratory"]:
        add(
            f"  {row['label'][:29]:<30}{row['metric'][:21]:<22}{row['n']:>4}"
            f"{_num(row['mean_difference'], sign=True):>9}{_interval(row):>22}"
            f"{_num(row['effect_size'], 2, True):>9}{_num(row['p_value'], 4):>9}"
        )
    add("")
    add("  These were not corrected for multiplicity and are not a basis for a claim.")
    add("  They are here so the write-up can say what was looked at.")

    if report["interactions"]:
        add("")
        add("--- INTERACTIONS  (EXPLORATORY -- n=20 cannot support an interaction claim)")
        add(f"  {'contrast':<52}{'metric':<17}{'n':>4}{'diff':>9}{'95% CI':>22}")
        for row in report["interactions"]:
            add(
                f"  {row['label'][:51]:<52}{row['metric'][:16]:<17}{row['n']:>4}"
                f"{_num(row['mean_difference'], sign=True):>9}{_interval(row):>22}"
            )
        add("")
        add("  An interaction contrast is a difference of differences and carries roughly")
        add("  twice the variance of either main effect it is built from. These intervals")
        add("  are wide by construction. The write-up must not claim an interaction from")
        add("  them; it may say the data do not settle one, which is a different thing.")

    calibration = report.get("calibration")
    add("")
    add("--- RQ4: THE JUDGE AGAINST THE HUMAN")
    if calibration is None:
        add("  Not computed. Fill in calibration_scores.csv and pass --calibration <path>.")
        add("  No agreement figure is reported rather than a zero -- an agreement of")
        add("  nothing is not an agreement of zero.")
    else:
        add(f"  {calibration['n_paired']} of {calibration['n_sheet_items']} sheet items paired")
        add(
            f"  {'scale':<16}{'n':>5}{'kappa_w':>10}{'spearman':>10}{'exact':>8}"
            f"{'human':>8}{'judge':>8}{'diff':>8}"
        )
        for scale, summary in calibration["scales"].items():
            exact = summary["exact_agreement"]
            exact_text = "--" if exact is None else f"{exact * 100:.0f}%"
            add(
                f"  {scale:<16}{summary['n']:>5}{_num(summary['kappa'], 2):>10}"
                f"{_num(summary['spearman'], 2):>10}{exact_text:>8}"
                f"{_num(summary['mean_human'], 2):>8}{_num(summary['mean_judge'], 2):>8}"
                f"{_num(summary['mean_difference'], 2, True):>8}"
            )
        verdict = calibration["verdict"]
        add(f"  {'verdict':<16}{verdict['n']:>5}{_num(verdict['kappa'], 2):>10}")

    figures = report.get("figures")
    if figures:
        add("")
        add("--- FIGURES")
        add(f"  {figures['directory']}")
        for key in ("main_effects", "coverage_per_config", "chunk_lengths", "power_against_n"):
            entry = figures.get(key) or {}
            if entry.get("written"):
                add(f"    {key:<22} {len(entry['written'])} files (svg + png)")
            else:
                add(f"    {key:<22} skipped: {entry.get('skipped', 'unknown')}")
    add("=" * 112)
    return "\n".join(lines)


def _n_text(estimate: dict[str, Any]) -> str:
    if estimate.get("n"):
        return str(estimate["n"])
    reason = estimate.get("reason", "")
    return "not est." if "not estimable" in reason else "--"


def _sample_size(report: dict[str, Any]) -> list[str]:
    """How large a FUTURE study would have to be. Not this study's power.

    The distinction is the whole point of the section, so it is stated in the
    heading, in the footer, and once more in the row labels.
    """
    rows = [row for row in report["primaries"] if row.get("sample_size")]
    lines: list[str] = ["", "--- SAMPLE SIZE FOR A FUTURE STUDY"]
    if not rows:
        lines.append("  Nothing to plan from yet: no primary comparison has data.")
        return lines

    first = rows[0]["sample_size"]
    lines.append(
        f"  Questions a NEW study would need for {first['target_power']:.0%} power at an"
        " effect the size of the one seen here."
    )
    lines.append(
        "  This is NOT the power of this study. Observed power is a function of the"
    )
    lines.append(
        "  p-value and says nothing the p-value did not; none is computed anywhere."
    )
    lines.append("")
    lines.append(
        f"  {'RQ':<4}{'metric':<16}{'basis':<22}{'effect':>9}"
        f"{'n @ ' + format(first['alpha'], '.2f'):>10}"
        f"{'n @ Holm ' + format(first['holm_alpha'], '.4f'):>18}"
    )
    labels = {
        "observed": "observed effect",
        "ci_low": "CI lower bound",
        "ci_high": "CI upper bound",
    }
    for row in rows:
        estimate = row["sample_size"]
        for key in ("observed", "ci_low", "ci_high"):
            entry = estimate["estimates"].get(key)
            if entry is None:
                continue
            if key == "observed":
                head = f"  {row['research_question']:<4}{row['metric'][:15]:<16}"
            else:
                head = f"  {'':<4}{'':<16}"
            effect = entry["effect"]
            # The marker trails the numbers rather than sharing the label's
            # field, which it overflowed and pushed every later column out.
            marker = "   <- worst case" if estimate.get("pessimistic_end") == key else ""
            lines.append(
                head
                + f"{labels[key]:<22}"
                + (f"{effect:>+9.3f}" if effect is not None else f"{'--':>9}")
                + f"{_n_text(entry['at_alpha']):>10}"
                + f"{_n_text(entry['at_holm_alpha']):>18}"
                + marker
            )
        if estimate.get("interval_spans_zero"):
            lines.append(
                f"  {'':<4}{'':<16}the interval spans zero: no worst case to size for, and"
            )
            lines.append(
                f"  {'':<4}{'':<16}the two bounds size effects in OPPOSITE directions"
            )
    lines.append("")
    lines.append(
        "  Three effect sizes because the observed one is itself a noisy estimate from"
    )
    lines.append(
        "  20 questions; a single number would claim a precision the data has not got."
    )
    lines.append(
        "  Two alpha levels because a follow-up carrying the same pre-specification"
    )
    lines.append(
        f"  faces the same correction: Holm's strictest threshold is"
        f" {first['alpha']}/6 = {first['holm_alpha']:.4f}."
    )
    lines.append(
        f"  By simulation ({first['trials']} resamples per candidate size) using the same"
    )
    lines.append("  exact tests as above, not a normal-theory formula.")
    return lines
