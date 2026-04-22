#!/usr/bin/env python3
"""Compare fresh baseline and RAG run logs under matched settings.

Usage:
    python scripts/compare_rag.py
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

from implementation import config as config_lib


BEST_PATTERN = re.compile(r"Best score of island.*?(-?\d+(?:\.\d+)?)\s*$", re.MULTILINE)
DEBUG_PATTERN = re.compile(
    r"^DEBUG: Sample\s+\d+\s+(?:prefix:|is empty or too short!)",
    re.MULTILINE,
)
METADATA_PATTERN = re.compile(r"^RUN_METADATA:\s*(\{.*\})\s*$", re.MULTILINE)
EVAL_PATTERN = re.compile(r"^EVAL_SUMMARY:\s*valid=(\d+)\s+total=(\d+)\s+ratio=([0-9.]+)\s*$", re.MULTILINE)
RETRIEVAL_DIAGNOSTICS_PATTERN = re.compile(r"^RETRIEVAL_DIAGNOSTICS:\s*(\{.*\})\s*$", re.MULTILINE)
COMPARE_MAX_SAMPLE_NUMS = config_lib.RuntimeDefaults().compare_max_sample_nums


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
    retrieval_policy_counts: dict[str, int] = field(default_factory=dict)
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


@dataclass(frozen=True)
class ComparePolicyConfig:
    allowed_run_modes: tuple[str, ...] = ("compare",)
    compare_budget_cap: int | None = COMPARE_MAX_SAMPLE_NUMS
    require_same_run_mode: bool = True


@dataclass(frozen=True)
class AcceptanceConfig:
    policy: ComparePolicyConfig = field(default_factory=ComparePolicyConfig)
    min_valid_eval_ratio: float = 0.85
    max_valid_eval_drop: float = 0.1
    max_completion_drop: float = 0.1
    min_relative_gain_pct: float = 0.0
    require_same_seed: bool = True


def parse_run_log(path: Path) -> ParsedRun:
    text = path.read_text(encoding="utf-8", errors="ignore")

    best_scores = [float(match.group(1)) for match in BEST_PATTERN.finditer(text)]
    sample_lines = len(DEBUG_PATTERN.findall(text))

    metadata: dict[str, Any] = {}
    metadata_matches = list(METADATA_PATTERN.finditer(text))
    if metadata_matches:
        # Use the most recent metadata record if multiple are present.
        last_metadata = metadata_matches[-1].group(1)
        try:
            metadata = json.loads(last_metadata)
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
    retrieval_policy_counts: dict[str, int] = {}
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

        applied_retrieval_policy = payload.get("applied_retrieval_policy")
        if isinstance(applied_retrieval_policy, str) and applied_retrieval_policy:
            retrieval_policy_counts[applied_retrieval_policy] = (
                retrieval_policy_counts.get(applied_retrieval_policy, 0) + 1
            )

        if payload.get("should_skip_retrieval") is True:
            retrieval_skip_events += 1

    retrieval_mean_top_score = (
        sum(retrieval_top_scores) / len(retrieval_top_scores)
        if retrieval_top_scores else None
    )
    retrieval_mean_top_score_gap = (
        sum(retrieval_score_gaps) / len(retrieval_score_gaps)
        if retrieval_score_gaps else None
    )
    retrieval_mean_confidence = (
        sum(retrieval_confidences) / len(retrieval_confidences)
        if retrieval_confidences else None
    )
    retrieval_mean_injected_chars = (
        sum(retrieval_injected_chars) / len(retrieval_injected_chars)
        if retrieval_injected_chars else None
    )
    retrieval_mean_injected_sources = (
        sum(retrieval_injected_sources) / len(retrieval_injected_sources)
        if retrieval_injected_sources else None
    )
    retrieval_mean_unique_sources = (
        sum(retrieval_unique_sources) / len(retrieval_unique_sources)
        if retrieval_unique_sources else None
    )
    retrieval_multi_source_hit_rate = (
        retrieval_multi_source_events / retrieval_events
        if retrieval_events else None
    )
    retrieval_skip_ratio = (
        retrieval_skip_events / retrieval_events
        if retrieval_events else None
    )

    return ParsedRun(
        best_scores=best_scores,
        sample_lines=sample_lines,
        metadata=metadata,
        valid_eval_events=len(eval_matches),
        total_valid_evals=total_valid_evals,
        total_eval_attempts=total_eval_attempts,
        retrieval_events=retrieval_events,
        retrieval_mean_top_score=retrieval_mean_top_score,
        retrieval_mean_top_score_gap=retrieval_mean_top_score_gap,
        retrieval_mean_confidence=retrieval_mean_confidence,
        retrieval_mean_injected_chars=retrieval_mean_injected_chars,
        retrieval_mean_injected_sources=retrieval_mean_injected_sources,
        retrieval_mean_unique_sources=retrieval_mean_unique_sources,
        retrieval_multi_source_hit_rate=retrieval_multi_source_hit_rate,
        retrieval_policy_counts=retrieval_policy_counts,
        retrieval_skip_ratio=retrieval_skip_ratio,
    )


def _fmt_float(value: float | None) -> str:
    return "NA" if value is None else f"{value:.6f}"


def _match_flag(left: Any, right: Any) -> str:
    if left is None or right is None:
        return "Unknown"
    return "Yes" if left == right else "No"


def _to_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _compute_delta(baseline_best: float | None, rag_best: float | None) -> float | None:
    if baseline_best is None or rag_best is None:
        return None
    return rag_best - baseline_best


def _compute_relative_gain_pct(baseline_best: float | None, rag_best: float | None) -> float | None:
    delta = _compute_delta(baseline_best, rag_best)
    if delta is None or baseline_best is None or baseline_best == 0:
        return None
    return (delta / abs(baseline_best)) * 100.0


def _format_cap_label(compare_budget_cap: int | None) -> str:
    return "Not enforced" if compare_budget_cap is None else str(compare_budget_cap)


def _format_policy_counts(policy_counts: dict[str, int]) -> str:
    if not policy_counts:
        return "NA"
    return ", ".join(
        f"{policy}:{count}"
        for policy, count in sorted(policy_counts.items())
    )


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
    lines.append(f"- {label} retrieval policy counts: {_format_policy_counts(run.retrieval_policy_counts)}")
    skip_ratio_pct = (
        f"{run.retrieval_skip_ratio * 100.0:.2f}%"
        if run.retrieval_skip_ratio is not None else "NA"
    )
    lines.append(f"- {label} retrieval skip ratio: {skip_ratio_pct}")


def evaluate_compare_policy(
    baseline: ParsedRun,
    rag: ParsedRun,
    policy_config: ComparePolicyConfig | None = None,
) -> dict[str, Any]:
    resolved_policy = policy_config or ComparePolicyConfig()
    baseline_mode = baseline.metadata.get("run_mode")
    rag_mode = rag.metadata.get("run_mode")

    baseline_budget = _to_int(
        baseline.metadata.get("effective_max_sample_nums", baseline.metadata.get("max_sample_nums"))
    )
    rag_budget = _to_int(
        rag.metadata.get("effective_max_sample_nums", rag.metadata.get("max_sample_nums"))
    )

    warnings: list[str] = []
    same_run_mode = baseline_mode == rag_mode
    allowed_run_modes = resolved_policy.allowed_run_modes
    modes_allowed = baseline_mode in allowed_run_modes and rag_mode in allowed_run_modes
    mode_compliant = modes_allowed and (
        same_run_mode or not resolved_policy.require_same_run_mode
    )
    if not modes_allowed:
        warnings.append(
            f"Both logs must use an allowed run_mode: {', '.join(allowed_run_modes)}."
        )
    elif resolved_policy.require_same_run_mode and not same_run_mode:
        warnings.append("Baseline and RAG run_mode must match.")

    budget_known = baseline_budget is not None and rag_budget is not None
    if not budget_known:
        warnings.append("Missing compare budget metadata in one or both logs.")

    budget_match = budget_known and baseline_budget == rag_budget
    if budget_known and not budget_match:
        warnings.append("Baseline and RAG budgets do not match.")

    if resolved_policy.compare_budget_cap is None:
        cap_compliant = budget_known
    else:
        cap_compliant = (
            budget_known
            and baseline_budget <= resolved_policy.compare_budget_cap
            and rag_budget <= resolved_policy.compare_budget_cap
        )
        if budget_known and not cap_compliant:
            warnings.append(f"Compare budget exceeds cap ({resolved_policy.compare_budget_cap}).")

    sample_evidence_compliant = (
        budget_known
        and baseline.sample_lines <= baseline_budget
        and rag.sample_lines <= rag_budget
    )
    if budget_known and not sample_evidence_compliant:
        warnings.append("Observed sample evidence exceeds declared compare budget.")

    return {
        "baseline_mode": baseline_mode,
        "rag_mode": rag_mode,
        "same_run_mode": same_run_mode,
        "allowed_run_modes": allowed_run_modes,
        "baseline_budget": baseline_budget,
        "rag_budget": rag_budget,
        "mode_compliant": mode_compliant,
        "budget_known": budget_known,
        "budget_match": budget_match,
        "cap_compliant": cap_compliant,
        "sample_evidence_compliant": sample_evidence_compliant,
        "policy_compliant": (
            mode_compliant
            and budget_known
            and budget_match
            and cap_compliant
            and sample_evidence_compliant
        ),
        "warnings": warnings,
        "compare_budget_cap": resolved_policy.compare_budget_cap,
    }


def evaluate_acceptance(
    baseline: ParsedRun,
    rag: ParsedRun,
    target_samples: int,
    acceptance_config: AcceptanceConfig | None = None,
) -> dict[str, Any]:
    resolved_config = acceptance_config or AcceptanceConfig()
    policy = evaluate_compare_policy(
        baseline=baseline,
        rag=rag,
        policy_config=resolved_config.policy,
    )
    baseline_best = baseline.best
    rag_best = rag.best
    relative_gain_pct = _compute_relative_gain_pct(baseline_best, rag_best)
    baseline_seed = baseline.metadata.get("seed")
    rag_seed = rag.metadata.get("seed")

    same_model = baseline.metadata.get("llm_model") == rag.metadata.get("llm_model")
    same_seed = baseline_seed is not None and rag_seed is not None and baseline_seed == rag_seed
    same_budget = policy["budget_match"]
    score_win = (
        baseline_best is not None
        and rag_best is not None
        and rag_best > baseline_best
    )

    baseline_valid_ratio = baseline.valid_eval_ratio
    rag_valid_ratio = rag.valid_eval_ratio
    valid_ratio_known = baseline_valid_ratio is not None and rag_valid_ratio is not None
    valid_ratio_floor_guard = (
        valid_ratio_known
        and rag_valid_ratio >= resolved_config.min_valid_eval_ratio
    )
    valid_ratio_drop_guard = (
        valid_ratio_known
        and rag_valid_ratio >= baseline_valid_ratio - resolved_config.max_valid_eval_drop
    )
    valid_ratio_guard = valid_ratio_floor_guard and valid_ratio_drop_guard

    baseline_completion = (baseline.sample_lines / target_samples) if target_samples > 0 else 0.0
    rag_completion = (rag.sample_lines / target_samples) if target_samples > 0 else 0.0
    completion_guard = rag_completion >= baseline_completion - resolved_config.max_completion_drop

    if not score_win:
        relative_gain_guard = False
    elif resolved_config.min_relative_gain_pct <= 0.0:
        relative_gain_guard = True
    else:
        relative_gain_guard = (
            relative_gain_pct is not None
            and relative_gain_pct >= resolved_config.min_relative_gain_pct
        )

    warnings: list[str] = []
    if resolved_config.require_same_seed and not same_seed:
        warnings.append("Seed mismatch: acceptance requires same seed.")
    if not same_model:
        warnings.append("Model mismatch: acceptance requires same model.")
    if not same_budget:
        warnings.append("Budget mismatch: acceptance requires same budget.")
    if not score_win:
        warnings.append("RAG best score does not beat baseline best score.")
    if not relative_gain_guard:
        warnings.append(
            "Relative gain did not meet the minimum acceptance threshold."
        )
    if not valid_ratio_known:
        warnings.append("Valid eval ratio is unavailable; acceptance guard cannot be evaluated.")
    else:
        if not valid_ratio_floor_guard:
            warnings.append(
                "RAG valid eval ratio is below the minimum threshold."
            )
        if not valid_ratio_drop_guard:
            warnings.append("Valid eval ratio degraded beyond allowed threshold.")
    if not completion_guard:
        warnings.append("Sample completion degraded beyond allowed threshold.")
    if not policy["policy_compliant"]:
        warnings.append("Compare policy is not compliant.")

    accepted = (
        policy["policy_compliant"]
        and (same_seed or not resolved_config.require_same_seed)
        and same_model
        and same_budget
        and score_win
        and relative_gain_guard
        and valid_ratio_guard
        and completion_guard
    )

    return {
        "accepted": accepted,
        "same_seed": same_seed,
        "same_model": same_model,
        "same_budget": same_budget,
        "score_win": score_win,
        "relative_gain_pct": relative_gain_pct,
        "min_relative_gain_pct": resolved_config.min_relative_gain_pct,
        "relative_gain_guard": relative_gain_guard,
        "baseline_valid_eval_ratio": baseline_valid_ratio,
        "rag_valid_eval_ratio": rag_valid_ratio,
        "valid_ratio_floor_guard": valid_ratio_floor_guard,
        "valid_ratio_drop_guard": valid_ratio_drop_guard,
        "valid_ratio_guard": valid_ratio_guard,
        "baseline_completion": baseline_completion,
        "rag_completion": rag_completion,
        "completion_guard": completion_guard,
        "warnings": warnings,
    }


def build_pair_markdown(
    baseline_log: Path,
    rag_log: Path,
    baseline: ParsedRun,
    rag: ParsedRun,
    target_samples: int,
    acceptance_config: AcceptanceConfig | None = None,
) -> str:
    baseline_best = baseline.best
    rag_best = rag.best

    delta = None
    relative = None
    improved = "Unknown"
    if baseline_best is not None and rag_best is not None:
        delta = _compute_delta(baseline_best, rag_best)
        relative = _compute_relative_gain_pct(baseline_best, rag_best)
        improved = "Yes" if delta > 0 else "No"

    baseline_seed = baseline.metadata.get("seed")
    rag_seed = rag.metadata.get("seed")
    baseline_model = baseline.metadata.get("llm_model")
    rag_model = rag.metadata.get("llm_model")

    seed_match = _match_flag(baseline_seed, rag_seed)
    model_match = _match_flag(baseline_model, rag_model)
    resolved_acceptance = acceptance_config or AcceptanceConfig()
    policy = evaluate_compare_policy(
        baseline=baseline,
        rag=rag,
        policy_config=resolved_acceptance.policy,
    )
    acceptance = evaluate_acceptance(
        baseline=baseline,
        rag=rag,
        target_samples=target_samples,
        acceptance_config=resolved_acceptance,
    )

    lines = [
        "# Baseline vs RAG Comparison Report",
        "",
        "## Run Setup",
        f"- Baseline log: `{baseline_log.as_posix()}`",
        f"- RAG log: `{rag_log.as_posix()}`",
        f"- Baseline seed: {baseline_seed if baseline_seed is not None else 'NA'}",
        f"- RAG seed: {rag_seed if rag_seed is not None else 'NA'}",
        f"- Baseline model: {baseline_model if baseline_model is not None else 'NA'}",
        f"- RAG model: {rag_model if rag_model is not None else 'NA'}",
        f"- Baseline budget: {policy['baseline_budget'] if policy['baseline_budget'] is not None else 'NA'}",
        f"- RAG budget: {policy['rag_budget'] if policy['rag_budget'] is not None else 'NA'}",
        f"- Seed match: {seed_match}",
        f"- Model match: {model_match}",
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
        "## Policy Compliance",
        f"- Policy compliant: {'Yes' if policy['policy_compliant'] else 'No'}",
        f"- Run mode valid: {'Yes' if policy['mode_compliant'] else 'No'}",
        f"- Same run mode: {'Yes' if policy['same_run_mode'] else 'No'}",
        f"- Budgets match: {'Yes' if policy['budget_match'] else 'No'}",
        f"- Budget cap ({_format_cap_label(policy['compare_budget_cap'])}) respected: {'Yes' if policy['cap_compliant'] else 'No'}",
        f"- Sample evidence within budget: {'Yes' if policy['sample_evidence_compliant'] else 'No'}",
        "",
        "## Acceptance",
        f"- Acceptance passed: {'Yes' if acceptance['accepted'] else 'No'}",
        f"- Same seed required: {'Yes' if acceptance['same_seed'] else 'No'}",
        f"- Same model required: {'Yes' if acceptance['same_model'] else 'No'}",
        f"- Same budget required: {'Yes' if acceptance['same_budget'] else 'No'}",
        f"- Score beats baseline: {'Yes' if acceptance['score_win'] else 'No'}",
        f"- Relative gain guard ({acceptance['min_relative_gain_pct']:.2f}%): {'Yes' if acceptance['relative_gain_guard'] else 'No'}",
        f"- Valid eval ratio guard: {'Yes' if acceptance['valid_ratio_guard'] else 'No'}",
        f"- Completion guard: {'Yes' if acceptance['completion_guard'] else 'No'}",
    ])

    if policy["warnings"]:
        lines.append("- Policy warnings:")
        for warning in policy["warnings"]:
            lines.append(f"  - {warning}")
    else:
        lines.append("- Policy warnings: None")

    if acceptance["warnings"]:
        lines.append("- Acceptance warnings:")
        for warning in acceptance["warnings"]:
            lines.append(f"  - {warning}")
    else:
        lines.append("- Acceptance warnings: None")

    lines.extend([
        "",
        "## Notes",
        "- Fresh baseline and RAG logs should be generated under matched budget and timeout for fair comparison.",
        "- If seed/model do not match, treat the result as directional rather than controlled evidence.",
    ])
    return "\n".join(lines) + "\n"


def print_cli_summary(baseline: ParsedRun, rag: ParsedRun, target_samples: int) -> None:
    baseline_best = baseline.best
    rag_best = rag.best

    delta = None
    relative_gain_pct = None
    improved = "Unknown"
    if baseline_best is not None and rag_best is not None:
        delta = _compute_delta(baseline_best, rag_best)
        relative_gain_pct = _compute_relative_gain_pct(baseline_best, rag_best)
        improved = "Yes" if delta > 0 else "No"

    acceptance_config = AcceptanceConfig()
    policy = evaluate_compare_policy(
        baseline=baseline,
        rag=rag,
        policy_config=acceptance_config.policy,
    )
    acceptance = evaluate_acceptance(
        baseline=baseline,
        rag=rag,
        target_samples=target_samples,
        acceptance_config=acceptance_config,
    )

    print("=" * 72)
    print("FRESH BASELINE VS RAG")
    print("=" * 72)
    print(f"Baseline best score       : {_fmt_float(baseline_best)}")
    print(f"RAG best score            : {_fmt_float(rag_best)}")
    print(f"Delta (rag-baseline)      : {_fmt_float(delta)}")
    print(
        "Relative gain pct         : "
        f"{_fmt_float(relative_gain_pct)}"
    )
    print(f"Improved                  : {improved}")
    print(f"Baseline valid eval ratio : {_fmt_float(baseline.valid_eval_ratio)}")
    print(f"RAG valid eval ratio      : {_fmt_float(rag.valid_eval_ratio)}")
    print(f"RAG mean retrieval conf.  : {_fmt_float(rag.retrieval_mean_confidence)}")
    print(f"Policy compliant          : {'Yes' if policy['policy_compliant'] else 'No'}")
    print(f"Acceptance passed         : {'Yes' if acceptance['accepted'] else 'No'}")
    if policy["warnings"]:
        print(f"Policy warnings           : {' | '.join(policy['warnings'])}")
    if acceptance["warnings"]:
        print(f"Acceptance warnings       : {' | '.join(acceptance['warnings'])}")
    print(f"Baseline sample evidence  : {baseline.sample_lines}/{target_samples}")
    print(f"RAG sample evidence       : {rag.sample_lines}/{target_samples}")
    print("=" * 72)


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

    raise ValueError(
        f"Missing {label} log path. Set CompareReportConfig.{label}_log_path in implementation/config.py."
    )


def main() -> int:
    report_config = config_lib.CompareReportConfig()
    results_dir = Path(report_config.results_dir)
    baseline_log = _resolve_log_path(
        explicit_path=report_config.baseline_log_path,
        results_dir=results_dir,
        pattern="compare_baseline_*.log",
        label="baseline",
    )
    rag_log = _resolve_log_path(
        explicit_path=report_config.rag_log_path,
        results_dir=results_dir,
        pattern="compare_rag_*.log",
        label="rag",
    )
    output = Path(report_config.output_path)
    target_samples = report_config.target_samples

    baseline = parse_run_log(baseline_log)
    rag = parse_run_log(rag_log)

    print_cli_summary(baseline=baseline, rag=rag, target_samples=target_samples)

    report = build_pair_markdown(
        baseline_log=baseline_log,
        rag_log=rag_log,
        baseline=baseline,
        rag=rag,
        target_samples=target_samples,
    )
    output.write_text(report, encoding="utf-8")
    print(f"Report written to: {output.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
