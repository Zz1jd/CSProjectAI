#!/usr/bin/env python3
"""Generate final markdown report from a multi-round summary JSON."""

from __future__ import annotations

import json
from pathlib import Path
import statistics


RESULTS_DIR = Path("results")
SUMMARY_GLOB = "multi_round_summary_*.json"


def _latest_summary_path() -> Path:
    candidates = sorted(RESULTS_DIR.glob(SUMMARY_GLOB))
    if not candidates:
        raise FileNotFoundError("No multi_round_summary_*.json file found in results/.")
    return candidates[-1]


def _fmt(value) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def _round_delta_stats(seed_rows: list[dict[str, object]]) -> tuple[float | None, float | None]:
    deltas = [float(row["delta"]) for row in seed_rows if row.get("delta") is not None]
    if not deltas:
        return None, None
    mean_delta = statistics.mean(deltas)
    if len(deltas) == 1:
        return mean_delta, 0.0
    return mean_delta, statistics.pstdev(deltas)


def build_report(summary: dict[str, object], source_path: Path) -> str:
    rounds = summary.get("rounds", [])
    lines: list[str] = [
        "# Multi-Round RAG Ablation Report",
        "",
        "## Setup",
        f"- Source summary: `{source_path.as_posix()}`",
        f"- Timestamp: {summary.get('timestamp', 'NA')}",
        f"- Seeds: {summary.get('seeds', [])}",
        f"- Compare budget: {summary.get('budget', 'NA')}",
        f"- Base model: {summary.get('base_model', 'NA')}",
        "",
    ]

    for round_entry in rounds:
        round_name = round_entry.get("round", "unknown")
        aggregate = round_entry.get("aggregate", {})
        seed_rows = round_entry.get("seeds", [])
        mean_delta, std_delta = _round_delta_stats(seed_rows)

        lines.extend([
            f"## {round_name}",
            f"- Win count: {aggregate.get('win_count', 0)}/{aggregate.get('seed_count', 0)}",
            f"- Win rate: {_fmt(aggregate.get('win_rate'))}",
            f"- Mean delta (rag - baseline): {_fmt(mean_delta)}",
            f"- Delta std: {_fmt(std_delta)}",
            "",
            "### Per-Seed",
            "| Seed | Baseline Best | RAG Best | Delta | Accepted | Valid Eval Ratio (B/R) | Sample Completion (B/R) |",
            "| --- | ---: | ---: | ---: | :---: | --- | --- |",
        ])

        for row in seed_rows:
            lines.append(
                "| "
                f"{row.get('seed')} | "
                f"{_fmt(row.get('baseline_best'))} | "
                f"{_fmt(row.get('rag_best'))} | "
                f"{_fmt(row.get('delta'))} | "
                f"{'Yes' if row.get('accepted') else 'No'} | "
                f"{_fmt(row.get('baseline_valid_eval_ratio'))}/{_fmt(row.get('rag_valid_eval_ratio'))} | "
                f"{row.get('baseline_samples')}/{summary.get('budget', 'NA')} ; {row.get('rag_samples')}/{summary.get('budget', 'NA')} |"
            )

        lines.append("")

    early_stop_reason = summary.get("early_stop_reason")
    lines.extend([
        "## Early Stop",
        f"- Trigger: {early_stop_reason if early_stop_reason else 'Not triggered'}",
        "",
        "## Acceptance Conclusion",
    ])

    latest_round = rounds[-1] if rounds else {}
    latest_aggregate = latest_round.get("aggregate", {}) if isinstance(latest_round, dict) else {}
    accepted = (
        latest_aggregate.get("seed_count", 0) > 0
        and latest_aggregate.get("win_rate", 0.0) >= (2.0 / 3.0)
        and latest_aggregate.get("mean_delta", 0.0) > 0.0
    )
    lines.append(f"- Final acceptance passed: {'Yes' if accepted else 'No'}")
    lines.append("- Rule: same budget and model, RAG should beat baseline on aggregate and satisfy stability guards.")
    lines.append("")
    lines.append("## Boundary Notes")
    lines.append("- Round 3 should only be interpreted when model-upgrade configuration is explicit.")
    lines.append("- If valid-eval ratio or sample completion regresses, treat score gain as unstable.")

    return "\n".join(lines) + "\n"


def main() -> int:
    summary_path = _latest_summary_path()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    report = build_report(summary=summary, source_path=summary_path)

    timestamp = summary.get("timestamp", "latest")
    output_path = RESULTS_DIR / f"multi_round_final_report_{timestamp}.md"
    output_path.write_text(report, encoding="utf-8")
    print(f"Final report written: {output_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
