#!/usr/bin/env python3
"""Run multi-seed, multi-round baseline-vs-RAG comparisons with early-stop control."""

from __future__ import annotations

import dataclasses
from dataclasses import asdict
import json
from pathlib import Path
import statistics
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import COMPARE_MAX_SAMPLE_NUMS
from main import build_runtime_config
from implementation import config as config_lib
from scripts._runner import build_runtime_variant
from scripts._runner import make_timestamp
from scripts._runner import run_logged_experiment
from scripts.compare_rag import build_pair_markdown
from scripts.compare_rag import evaluate_acceptance
from scripts.compare_rag import parse_run_log


SCRIPT_CONFIG = config_lib.MultiRoundScriptConfig()
RUNTIME_DEFAULTS = config_lib.RuntimeDefaults()
DEFAULT_SEEDS = list(SCRIPT_CONFIG.seeds)
RESULTS_DIR = Path(SCRIPT_CONFIG.results_dir)
ROUND_CONFIGS: dict[str, config_lib.MultiRoundPreset] = {
    round_config.name: round_config for round_config in SCRIPT_CONFIG.rounds
}


def determine_round_plan(round2_passed: bool) -> list[str]:
    if round2_passed:
        return ["round1", "round2"]
    return ["round1", "round2", "round3"]


def should_stop_after_round(aggregate: dict[str, float]) -> bool:
    return (
        aggregate.get("seed_count", 0) > 0
        and aggregate.get("win_rate", 0.0) >= (2.0 / 3.0)
        and aggregate.get("mean_delta", 0.0) > 0.0
    )


def _build_run_config(
        seed: int,
        enable_rag: bool,
        round_config: config_lib.MultiRoundPreset,
) -> config_lib.Config:
    model_track = round_config.model_track
    model_upgrade_name = round_config.model_upgrade_name
    if model_track == "upgrade" and not model_upgrade_name:
        raise RuntimeError("Round 3 requires MultiRoundPreset.model_upgrade_name to be set in implementation/config.py.")

    base_config = build_runtime_config()
    rag_overrides = {
        "corpus_roots": round_config.corpus_roots,
        "retrieval_mode": round_config.retrieval_mode,
        "score_threshold": round_config.retrieval_score_threshold,
        "enable_diagnostics": round_config.retrieval_diagnostics,
        "use_intent_query": round_config.retrieval_intent_query,
    }
    return build_runtime_variant(
        enable_rag=enable_rag,
        run_mode="compare",
        base_config=base_config,
        random_seed=seed,
        model_track=model_track,
        model_upgrade_name=model_upgrade_name,
        rag_overrides=rag_overrides,
    )


def _aggregate_seed_results(seed_results: list[dict[str, object]]) -> dict[str, float]:
    deltas = [float(item["delta"]) for item in seed_results if item.get("delta") is not None]
    win_count = sum(1 for item in seed_results if item.get("accepted") is True)
    seed_count = len(seed_results)
    return {
        "seed_count": seed_count,
        "win_count": win_count,
        "win_rate": (win_count / seed_count) if seed_count else 0.0,
        "mean_delta": statistics.mean(deltas) if deltas else 0.0,
    }


def _run_round(round_name: str, timestamp: str) -> dict[str, object]:
    round_config = ROUND_CONFIGS[round_name]
    seed_results: list[dict[str, object]] = []

    for seed in DEFAULT_SEEDS:
        baseline_log = RESULTS_DIR / f"{round_name}_seed{seed}_baseline_{timestamp}.log"
        rag_log = RESULTS_DIR / f"{round_name}_seed{seed}_rag_{timestamp}.log"
        report_path = RESULTS_DIR / f"{round_name}_seed{seed}_report_{timestamp}.md"

        baseline_config = _build_run_config(seed=seed, enable_rag=False, round_config=round_config)
        rag_config = _build_run_config(seed=seed, enable_rag=True, round_config=round_config)

        run_logged_experiment(
            label=f"{round_name}_baseline_seed{seed}",
            runtime_config=baseline_config,
            log_path=baseline_log,
            dataset_path=RUNTIME_DEFAULTS.dataset_path,
            max_sample_nums=COMPARE_MAX_SAMPLE_NUMS,
            log_dir=SCRIPT_CONFIG.log_dir,
            header_fields={"RUN_MODE": "compare", "RUN_BUDGET": COMPARE_MAX_SAMPLE_NUMS},
        )
        run_logged_experiment(
            label=f"{round_name}_rag_seed{seed}",
            runtime_config=rag_config,
            log_path=rag_log,
            dataset_path=RUNTIME_DEFAULTS.dataset_path,
            max_sample_nums=COMPARE_MAX_SAMPLE_NUMS,
            log_dir=SCRIPT_CONFIG.log_dir,
            header_fields={"RUN_MODE": "compare", "RUN_BUDGET": COMPARE_MAX_SAMPLE_NUMS},
        )

        baseline = parse_run_log(baseline_log)
        rag = parse_run_log(rag_log)
        acceptance = evaluate_acceptance(
            baseline=baseline,
            rag=rag,
            target_samples=COMPARE_MAX_SAMPLE_NUMS,
        )

        report = build_pair_markdown(
            baseline_log=baseline_log,
            rag_log=rag_log,
            baseline=baseline,
            rag=rag,
            target_samples=COMPARE_MAX_SAMPLE_NUMS,
        )
        report_path.write_text(report, encoding="utf-8")

        baseline_best = baseline.best
        rag_best = rag.best
        delta = (rag_best - baseline_best) if baseline_best is not None and rag_best is not None else None
        seed_results.append({
            "seed": seed,
            "baseline_log": baseline_log.as_posix(),
            "rag_log": rag_log.as_posix(),
            "report": report_path.as_posix(),
            "baseline_best": baseline_best,
            "rag_best": rag_best,
            "delta": delta,
            "accepted": acceptance["accepted"],
            "baseline_valid_eval_ratio": baseline.valid_eval_ratio,
            "rag_valid_eval_ratio": rag.valid_eval_ratio,
            "baseline_samples": baseline.sample_lines,
            "rag_samples": rag.sample_lines,
        })

    aggregate = _aggregate_seed_results(seed_results)
    return {
        "round": round_name,
        "config": asdict(round_config),
        "seeds": seed_results,
        "aggregate": aggregate,
    }


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = make_timestamp()
    rounds_executed: list[dict[str, object]] = []
    early_stop_reason = ""

    for round_name in ["round1", "round2", "round3"]:
        if round_name == "round3":
            round2_aggregate = rounds_executed[1]["aggregate"] if len(rounds_executed) >= 2 else {}
            round2_passed = should_stop_after_round(round2_aggregate)
            planned = determine_round_plan(round2_passed=round2_passed)
            if "round3" not in planned:
                early_stop_reason = "Round 2 already met aggregate win criteria; skip Round 3."
                break

        round_result = _run_round(round_name=round_name, timestamp=timestamp)
        rounds_executed.append(round_result)

        if should_stop_after_round(round_result["aggregate"]):
            early_stop_reason = f"{round_name} met aggregate win criteria."
            break

    summary = {
        "timestamp": timestamp,
        "seeds": DEFAULT_SEEDS,
        "budget": COMPARE_MAX_SAMPLE_NUMS,
        "base_model": build_runtime_config().llm_model,
        "rounds": rounds_executed,
        "early_stop_reason": early_stop_reason,
    }

    summary_path = RESULTS_DIR / f"multi_round_summary_{timestamp}.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Summary written: {summary_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
