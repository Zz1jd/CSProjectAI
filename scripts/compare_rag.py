#!/usr/bin/env python3
"""Lightweight compare/log parsing helpers for compare-only workflows."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BEST_PATTERN = re.compile(r"Best score of island.*?(-?\d+(?:\.\d+)?)\s*$", re.MULTILINE)
DEBUG_PATTERN = re.compile(
    r"^DEBUG: Sample\s+\d+\s+(?:prefix:|is empty or too short!)",
    re.MULTILINE,
)
METADATA_PATTERN = re.compile(r"^RUN_METADATA:\s*(\{.*\})\s*$", re.MULTILINE)
EVAL_PATTERN = re.compile(r"^EVAL_SUMMARY:\s*valid=(\d+)\s+total=(\d+)\s+ratio=([0-9.]+)\s*$", re.MULTILINE)
RETRIEVAL_DIAGNOSTICS_PATTERN = re.compile(r"^RETRIEVAL_DIAGNOSTICS:\s*(\{.*\})\s*$", re.MULTILINE)


@dataclass
class ParsedRun:
    best_scores: list[float]
    sample_lines: int
    metadata: dict[str, Any]
    valid_eval_events: int = 0
    total_valid_evals: int = 0
    total_eval_attempts: int = 0
    retrieval_events: int = 0
    retrieval_mean_top_score: float | None = None
    retrieval_mean_top_score_gap: float | None = None
    retrieval_mean_confidence: float | None = None
    retrieval_mean_injected_chars: float | None = None
    retrieval_mean_injected_sources: float | None = None
    retrieval_mean_unique_sources: float | None = None
    retrieval_multi_source_hit_rate: float | None = None
    retrieval_skip_ratio: float | None = None

    @property
    def best(self) -> float | None:
        return max(self.best_scores) if self.best_scores else None

    @property
    def valid_eval_ratio(self) -> float | None:
        if self.total_eval_attempts <= 0:
            return None
        return self.total_valid_evals / self.total_eval_attempts

    @property
    def evals_per_sample(self) -> float | None:
        if self.sample_lines <= 0:
            return None
        return self.total_eval_attempts / self.sample_lines


def parse_run_log(path: Path) -> ParsedRun:
    text = path.read_text(encoding="utf-8", errors="ignore")

    best_scores = [float(match.group(1)) for match in BEST_PATTERN.finditer(text)]
    sample_lines = len(DEBUG_PATTERN.findall(text))

    metadata: dict[str, Any] = {}
    metadata_matches = list(METADATA_PATTERN.finditer(text))
    if metadata_matches:
        try:
            metadata = json.loads(metadata_matches[-1].group(1))
        except json.JSONDecodeError:
            metadata = {}

    eval_matches = list(EVAL_PATTERN.finditer(text))
    total_valid_evals = sum(int(match.group(1)) for match in eval_matches)
    total_eval_attempts = sum(int(match.group(2)) for match in eval_matches)

    retrieval_top_scores: list[float] = []
    retrieval_score_gaps: list[float] = []
    retrieval_confidences: list[float] = []
    retrieval_injected_chars: list[float] = []
    retrieval_injected_sources: list[float] = []
    retrieval_unique_sources: list[float] = []
    retrieval_multi_source_events = 0
    retrieval_skip_events = 0
    retrieval_events = 0

    for match in RETRIEVAL_DIAGNOSTICS_PATTERN.finditer(text):
        retrieval_events += 1
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue

        top_score = payload.get("top_score")
        if isinstance(top_score, (int, float)):
            retrieval_top_scores.append(float(top_score))

        top_score_gap = payload.get("top_score_gap")
        if isinstance(top_score_gap, (int, float)):
            retrieval_score_gaps.append(float(top_score_gap))

        retrieval_confidence = payload.get("retrieval_confidence")
        if isinstance(retrieval_confidence, (int, float)):
            retrieval_confidences.append(float(retrieval_confidence))

        injected_chars = payload.get("injected_chars")
        if isinstance(injected_chars, (int, float)):
            retrieval_injected_chars.append(float(injected_chars))

        injected_source_count = payload.get("injected_source_count")
        if isinstance(injected_source_count, (int, float)):
            injected_source_value = float(injected_source_count)
            retrieval_injected_sources.append(injected_source_value)
            if injected_source_value >= 2.0:
                retrieval_multi_source_events += 1

        unique_source_count = payload.get("unique_source_count")
        if isinstance(unique_source_count, (int, float)):
            retrieval_unique_sources.append(float(unique_source_count))

        if payload.get("should_skip_retrieval") is True:
            retrieval_skip_events += 1

    return ParsedRun(
        best_scores=best_scores,
        sample_lines=sample_lines,
        metadata=metadata,
        valid_eval_events=len(eval_matches),
        total_valid_evals=total_valid_evals,
        total_eval_attempts=total_eval_attempts,
        retrieval_events=retrieval_events,
        retrieval_mean_top_score=_mean(retrieval_top_scores),
        retrieval_mean_top_score_gap=_mean(retrieval_score_gaps),
        retrieval_mean_confidence=_mean(retrieval_confidences),
        retrieval_mean_injected_chars=_mean(retrieval_injected_chars),
        retrieval_mean_injected_sources=_mean(retrieval_injected_sources),
        retrieval_mean_unique_sources=_mean(retrieval_unique_sources),
        retrieval_multi_source_hit_rate=(
            retrieval_multi_source_events / retrieval_events if retrieval_events else None
        ),
        retrieval_skip_ratio=(retrieval_skip_events / retrieval_events if retrieval_events else None),
    )


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _fmt_float(value: float | None) -> str:
    return "NA" if value is None else f"{value:.6f}"


def _compute_delta(baseline_best: float | None, rag_best: float | None) -> float | None:
    if baseline_best is None or rag_best is None:
        return None
    return rag_best - baseline_best


def _compute_relative_gain_pct(baseline_best: float | None, rag_best: float | None) -> float | None:
    delta = _compute_delta(baseline_best, rag_best)
    if delta is None or baseline_best is None or baseline_best == 0:
        return None
    return (delta / abs(baseline_best)) * 100.0


def _append_retrieval_lines(lines: list[str], label: str, run: ParsedRun) -> None:
    lines.append(f"- {label} retrieval events: {run.retrieval_events}")
    lines.append(f"- {label} mean top score: {_fmt_float(run.retrieval_mean_top_score)}")
    lines.append(f"- {label} mean top score gap: {_fmt_float(run.retrieval_mean_top_score_gap)}")
    lines.append(f"- {label} mean retrieval confidence: {_fmt_float(run.retrieval_mean_confidence)}")
    lines.append(f"- {label} mean injected chars: {_fmt_float(run.retrieval_mean_injected_chars)}")
    lines.append(f"- {label} mean injected sources: {_fmt_float(run.retrieval_mean_injected_sources)}")
    lines.append(f"- {label} mean unique sources: {_fmt_float(run.retrieval_mean_unique_sources)}")
    multi_source_hit_rate = (
        f"{run.retrieval_multi_source_hit_rate * 100.0:.2f}%"
        if run.retrieval_multi_source_hit_rate is not None else "NA"
    )
    lines.append(f"- {label} multi-source hit rate: {multi_source_hit_rate}")
    skip_ratio_pct = (
        f"{run.retrieval_skip_ratio * 100.0:.2f}%"
        if run.retrieval_skip_ratio is not None else "NA"
    )
    lines.append(f"- {label} retrieval skip ratio: {skip_ratio_pct}")


def build_pair_markdown(
    baseline_log: Path,
    rag_log: Path,
    baseline: ParsedRun,
    rag: ParsedRun,
    target_samples: int,
) -> str:
    baseline_best = baseline.best
    rag_best = rag.best
    delta = _compute_delta(baseline_best, rag_best)
    relative = _compute_relative_gain_pct(baseline_best, rag_best)
    improved = "Unknown"
    if delta is not None:
        improved = "Yes" if delta > 0 else "No"

    lines = [
        "# Baseline vs RAG Comparison Report",
        "",
        "## Run Setup",
        f"- Baseline log: `{baseline_log.as_posix()}`",
        f"- RAG log: `{rag_log.as_posix()}`",
        f"- Baseline seed: {baseline.metadata.get('seed', 'NA')}",
        f"- RAG seed: {rag.metadata.get('seed', 'NA')}",
        f"- Baseline model: {baseline.metadata.get('llm_model', 'NA')}",
        f"- RAG model: {rag.metadata.get('llm_model', 'NA')}",
        f"- Baseline budget: {baseline.metadata.get('max_sample_nums', 'NA')}",
        f"- RAG budget: {rag.metadata.get('max_sample_nums', 'NA')}",
        "",
        "## Metrics",
        f"- Baseline best score: {_fmt_float(baseline_best)}",
        f"- RAG best score: {_fmt_float(rag_best)}",
        f"- Delta (rag - baseline): {_fmt_float(delta)}",
        f"- Relative change vs baseline: {_fmt_float(relative)}%" if relative is not None else "- Relative change vs baseline: NA",
        f"- Improved vs baseline: {improved}",
        f"- Baseline valid eval ratio: {_fmt_float(baseline.valid_eval_ratio)}",
        f"- RAG valid eval ratio: {_fmt_float(rag.valid_eval_ratio)}",
        f"- Baseline evals per sample: {_fmt_float(baseline.evals_per_sample)}",
        f"- RAG evals per sample: {_fmt_float(rag.evals_per_sample)}",
        f"- Baseline sample progress evidence: {baseline.sample_lines}/{target_samples}",
        f"- RAG sample progress evidence: {rag.sample_lines}/{target_samples}",
        "",
        "## Retrieval Diagnostics",
    ]
    _append_retrieval_lines(lines, "Baseline", baseline)
    _append_retrieval_lines(lines, "RAG", rag)
    lines.extend([
        "",
        "## Notes",
        "- This report is descriptive only: all listed runs are executed and summarized without acceptance gates.",
        "- Use the metrics and retrieval diagnostics to compare candidate behavior under the same budget.",
    ])
    return "\n".join(lines) + "\n"


def _resolve_log_path(
    explicit_path: str,
    results_dir: Path,
    pattern: str,
    label: str,
) -> Path:
    if explicit_path.strip():
        return Path(explicit_path)

    candidates = sorted(results_dir.glob(pattern))
    if candidates:
        return candidates[-1]

    raise ValueError(f"Missing {label} log path.")
