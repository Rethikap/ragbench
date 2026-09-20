"""Rendering the generation report for a terminal.

Split from :mod:`ragbench.report.generation`, which aggregates: one module
computes the numbers, one lays them out. The renderer is where the length
figures are labelled, and the labels do real work -- an amortised batch time
read as a per-answer latency, or a stand-in table read as results, would each be
a wrong number nobody could see was wrong.
"""

from __future__ import annotations

from typing import Any


def _wrap(text: str, width: int, indent: str) -> list[str]:
    """Flow an answer across lines instead of cutting it off.

    Reading answers is the point of this view -- a truncated one cannot be
    judged, which is what the reader is here to do before the judge does. ASCII
    only, because this prints to a Windows console at cp1252 as often as to a
    UTF-8 one, and a mangled byte inside an answer reads as a generation defect.
    """
    flat = " ".join(text.split())
    if not flat:
        return [indent + "(empty)"]
    lines: list[str] = []
    current = indent
    for word in flat.split(" "):
        if current.strip() and len(current) + 1 + len(word) > width:
            lines.append(current)
            current = indent + word
        else:
            current = f"{current} {word}" if current.strip() else current + word
    if current.strip():
        lines.append(current)
    return lines


def render(report: dict[str, Any], only: bool = False) -> str:
    """Length and timing per configuration, then the answers themselves."""
    lines: list[str] = []
    add = lines.append
    add("=" * 108)
    add("GENERATION REPORT")
    if report["model_id"] == "stand-in":
        add("  *** CPU STAND-IN. These answers are extracted sentences, not generated text.")
        add("  *** They exist to prove the stage runs offline. Never report them as results.")
    add(
        f"  model        : {report['model_id']}@{report['model_revision'][:12]}"
        f"  ({report['quantization'] or 'no quantization'})"
    )
    add(
        f"  prompt       : {report['prompt_template_id']}"
        f"  (digest {report['prompt_digest']} -- of the TEXT, not the label)"
    )
    add(
        f"  answers      : {report['n_answers']}/{report['n_answers_expected']}"
        f"  ({report['n_configs_generated']}/{report['n_configs']} configurations,"
        f" {report['n_questions']} questions)"
    )
    add("=" * 108)

    if not report["n_answers"]:
        add("  Nothing generated yet. Run `ragbench generate`.")
        add("=" * 108)
        return "\n".join(lines)

    add("")
    add("--- ANSWER LENGTH  (the judge literature reports a length bias; measure it first)")
    add(
        f"  {'configuration':<32}{'answers':>8}{'tokens':>8}{'median':>8}{'max':>6}"
        f"{'chars':>8}{'prompt':>8}{'chunks':>8}{'trunc':>7}{'refuse':>8}"
    )
    for config in report["configs"]:
        if not config["n_answers"]:
            add(f"  {config['config']:<32}{'--':>8}   (not generated)")
            continue
        tokens, chars = config["completion_tokens"], config["answer_chars"]
        add(
            f"  {config['config']:<32}{config['n_answers']:>8}{tokens['mean']:>8.0f}"
            f"{tokens['median']:>8.0f}{tokens['max']:>6}{chars['mean']:>8.0f}"
            f"{config['prompt_tokens']['mean']:>8.0f}"
            f"{config['context_chunks']['mean']:>8.1f}"
            f"{config['hit_max_new_tokens']:>7}{config['refusals']:>8}"
        )
    add("")
    add(
        f"  trunc = answers stopped by the {report['max_new_tokens']}-token ceiling, cut"
        " off mid-sentence rather than finished short."
    )
    add(
        "  refuse = answers exactly matching the configured abstention sentence."
        "  Both are counts, not rates."
    )
    for config in report["configs"]:
        if config.get("truncated_ids"):
            add(f"    truncated in {config['config']}: {', '.join(config['truncated_ids'])}")

    add("")
    add("--- TIME PER ANSWER  (amortised over its batch, not a measured per-answer latency)")
    add(f"  {'configuration':<32}{'ms/answer':>11}{'p90':>9}")
    for config in report["configs"]:
        if not config["n_answers"]:
            continue
        latency = config["latency_ms"]
        add(f"  {config['config']:<32}{latency['mean']:>11.0f}{latency['p90']:>9.0f}")

    add("")
    add("--- ANSWERS" + ("  (selected questions)" if only else "  (every question)"))
    for item in report["side_by_side"]:
        add("")
        add("-" * 108)
        add(f"  [{item['query_id']}] {item['question']}")
        add("  reference:")
        lines.extend(_wrap(item["reference_answer"], 104, "      "))
        for name, answer in item["answers"].items():
            mark = "   [TRUNCATED at the ceiling]" if answer["finish_reason"] == "length" else ""
            add("")
            add(
                f"  {name}   ({answer['n_completion_tokens']} tokens from"
                f" {answer['n_context_chunks']} chunks){mark}"
            )
            lines.extend(_wrap(answer["answer"], 104, "      "))
    add("=" * 108)
    return "\n".join(lines)
