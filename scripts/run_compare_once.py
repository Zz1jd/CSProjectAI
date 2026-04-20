#!/usr/bin/env python3
"""Run exactly one baseline-vs-RAG compare pair with strict lightweight policy."""

from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import COMPARE_MAX_SAMPLE_NUMS
from implementation import config as config_lib
from scripts._runner import build_runtime_variant
from scripts._runner import make_timestamp
from scripts._runner import run_logged_experiment
from scripts.compare_rag import build_pair_markdown
from scripts.compare_rag import parse_run_log
from scripts.compare_rag import print_cli_summary


SCRIPT_CONFIG = config_lib.CompareScriptConfig()
RUNTIME_DEFAULTS = config_lib.RuntimeDefaults()
RESULTS_DIR = Path(SCRIPT_CONFIG.results_dir)


def _build_compare_config(enable_rag: bool) -> config_lib.Config:
    return build_runtime_variant(enable_rag=enable_rag, run_mode="compare")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = make_timestamp()
    baseline_log = RESULTS_DIR / f"compare_baseline_{timestamp}.log"
    rag_log = RESULTS_DIR / f"compare_rag_{timestamp}.log"
    report_path = RESULTS_DIR / f"RAG_vs_baseline_compare_{timestamp}.md"

    run_logged_experiment(
        label="BASELINE",
        runtime_config=_build_compare_config(enable_rag=False),
        log_path=baseline_log,
        dataset_path=RUNTIME_DEFAULTS.dataset_path,
        max_sample_nums=COMPARE_MAX_SAMPLE_NUMS,
        log_dir=SCRIPT_CONFIG.log_dir,
        header_fields={"RUN_MODE": "compare", "RUN_EFFECTIVE_BUDGET": COMPARE_MAX_SAMPLE_NUMS},
    )
    run_logged_experiment(
        label="RAG",
        runtime_config=_build_compare_config(enable_rag=True),
        log_path=rag_log,
        dataset_path=RUNTIME_DEFAULTS.dataset_path,
        max_sample_nums=COMPARE_MAX_SAMPLE_NUMS,
        log_dir=SCRIPT_CONFIG.log_dir,
        header_fields={"RUN_MODE": "compare", "RUN_EFFECTIVE_BUDGET": COMPARE_MAX_SAMPLE_NUMS},
    )

    baseline = parse_run_log(baseline_log)
    rag = parse_run_log(rag_log)
    print_cli_summary(baseline=baseline, rag=rag, target_samples=COMPARE_MAX_SAMPLE_NUMS)

    report = build_pair_markdown(
        baseline_log=baseline_log,
        rag_log=rag_log,
        baseline=baseline,
        rag=rag,
        target_samples=COMPARE_MAX_SAMPLE_NUMS,
    )
    report_path.write_text(report, encoding="utf-8")
    print(f"REPORT: {report_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
