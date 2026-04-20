#!/usr/bin/env python3
"""Summarize one RAG run log against historical baseline.

Usage:
    python scripts/summarize_rag_run.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from implementation import config as config_lib


BEST_PATTERN = re.compile(
    r"Best score of island.*?(-?\d+\.\d+)\s*$",
    re.MULTILINE,
)
DEBUG_PATTERN = re.compile(r"^DEBUG: Sample\s+\d+\s+prefix:", re.MULTILINE)


@dataclass
class ParsedLog:
    best_scores: list[float]
    sample_lines: int

    @property
    def best(self) -> float | None:
        return max(self.best_scores) if self.best_scores else None


def parse_log(path: Path) -> ParsedLog:
    text = path.read_text(encoding="utf-8", errors="ignore")
    best_scores = [float(m.group(1)) for m in BEST_PATTERN.finditer(text)]
    sample_lines = len(DEBUG_PATTERN.findall(text))
    return ParsedLog(best_scores=best_scores, sample_lines=sample_lines)


def fmt_float(value: float | None) -> str:
    if value is None:
        return "NA"
    return f"{value:.6f}"


def build_markdown(
    run_log: Path,
    historical_file: Path,
    run_metrics: ParsedLog,
    historical_metrics: ParsedLog,
    target_samples: int,
) -> str:
    run_best = run_metrics.best
    hist_best = historical_metrics.best

    delta = None
    relative = None
    improved = "Unknown"
    if run_best is not None and hist_best is not None:
        delta = run_best - hist_best
        relative = (delta / abs(hist_best) * 100.0) if hist_best != 0 else None
        improved = "Yes" if delta > 0 else "No"

    completion = (
        f"{run_metrics.sample_lines}/{target_samples}"
        if target_samples > 0 else str(run_metrics.sample_lines)
    )

    lines = [
        "# RAG Full-Run Comparison Report",
        "",
        "## Run Setup",
        f"- Run log: `{run_log.as_posix()}`",
        f"- Historical baseline file: `{historical_file.as_posix()}`",
        "- Mode: RAG enabled",
        "- Config target: samples_per_prompt=4, evaluate_timeout_seconds=30, max_sample_nums=100",
        "",
        "## Metrics",
        f"- Run best score: {fmt_float(run_best)}",
        f"- Historical best score: {fmt_float(hist_best)}",
        f"- Delta (run - historical): {fmt_float(delta)}",
        f"- Relative change: {fmt_float(relative)}%" if relative is not None else "- Relative change: NA",
        f"- Improved vs historical: {improved}",
        f"- Sample progress evidence (debug lines): {completion}",
        "",
        "## Notes",
        "- This comparison uses historical notebook outputs as baseline, not a fresh no-RAG rerun.",
        "- Endpoint/model variance and runtime conditions can affect strict comparability.",
    ]
    return "\n".join(lines) + "\n"


def print_cli_table(
    run_metrics: ParsedLog,
    historical_metrics: ParsedLog,
    target_samples: int,
) -> None:
    run_best = run_metrics.best
    hist_best = historical_metrics.best

    delta = None
    improved = "Unknown"
    if run_best is not None and hist_best is not None:
        delta = run_best - hist_best
        improved = "Yes" if delta > 0 else "No"

    print("=" * 64)
    print("RAG FULL-RUN VS HISTORICAL BASELINE")
    print("=" * 64)
    print(f"Run best score           : {fmt_float(run_best)}")
    print(f"Historical best score    : {fmt_float(hist_best)}")
    print(f"Delta (run-historical)   : {fmt_float(delta)}")
    print(f"Improved                 : {improved}")
    print(f"Sample progress evidence : {run_metrics.sample_lines}/{target_samples}")
    print("=" * 64)


def _resolve_run_log_path(report_config: config_lib.HistoricalReportConfig) -> Path:
    if report_config.run_log_path.strip():
        return Path(report_config.run_log_path)

    results_dir = Path(report_config.results_dir)
    candidates = sorted(results_dir.glob(report_config.run_log_glob))
    if candidates:
        return candidates[-1]

    raise ValueError(
        "Missing run log path. Set HistoricalReportConfig.run_log_path "
        "in implementation/config.py."
    )


def main() -> int:
    report_config = config_lib.HistoricalReportConfig()
    run_log = _resolve_run_log_path(report_config)
    historical = Path(report_config.historical_log_path)
    output = Path(report_config.output_path)
    target_samples = report_config.target_samples

    run_metrics = parse_log(run_log)
    historical_metrics = parse_log(historical)

    print_cli_table(run_metrics, historical_metrics, target_samples=target_samples)

    report = build_markdown(
        run_log=run_log,
        historical_file=historical,
        run_metrics=run_metrics,
        historical_metrics=historical_metrics,
        target_samples=target_samples,
    )
    output.write_text(report, encoding="utf-8")
    print(f"Report written to: {output.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
