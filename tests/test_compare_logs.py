import tempfile
import unittest
from pathlib import Path

from scripts.compare_rag import AcceptanceConfig
from scripts.compare_rag import ComparePolicyConfig
from scripts.compare_rag import ParsedRun
from scripts.compare_rag import _resolve_log_path
from scripts.compare_rag import build_pair_markdown
from scripts.compare_rag import evaluate_acceptance
from scripts.compare_rag import evaluate_compare_policy
from scripts.compare_rag import parse_run_log


class CompareLogsTests(unittest.TestCase):
    def test_resolve_log_path_prefers_explicit_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            results_dir = Path(temporary_dir)
            explicit = results_dir / "explicit.log"
            explicit.write_text("x", encoding="utf-8")

            resolved = _resolve_log_path(
                explicit_path=str(explicit),
                results_dir=results_dir,
                pattern="compare_baseline_*.log",
                label="baseline",
            )
            self.assertEqual(resolved, explicit)

    def test_resolve_log_path_falls_back_to_latest_match(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            results_dir = Path(temporary_dir)
            older = results_dir / "compare_baseline_20260101_000000.log"
            newer = results_dir / "compare_baseline_20260102_000000.log"
            older.write_text("old", encoding="utf-8")
            newer.write_text("new", encoding="utf-8")

            resolved = _resolve_log_path(
                explicit_path="",
                results_dir=results_dir,
                pattern="compare_baseline_*.log",
                label="baseline",
            )
            self.assertEqual(resolved, newer)

    def test_parse_run_log_extracts_metadata_best_and_progress(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            log_path = Path(temporary_dir) / "rag.log"
            log_path.write_text(
                "RUN_METADATA: {\"seed\": 42, \"llm_model\": \"gpt-4o-mini\", \"rag_enabled\": true, \"run_mode\": \"compare\", \"max_sample_nums\": 10}\n"
                " Best score of island %d increased to %s 0 -1161.98\n"
                " Best score of island %d increased to %s 2 -1106.40\n"
                "DEBUG: Sample 0 prefix: ...\n"
                "DEBUG: Sample 1 prefix: ...\n",
                encoding="utf-8",
            )

            parsed = parse_run_log(log_path)

            self.assertEqual(parsed.metadata.get("seed"), 42)
            self.assertEqual(parsed.metadata.get("llm_model"), "gpt-4o-mini")
            self.assertEqual(parsed.metadata.get("run_mode"), "compare")
            self.assertEqual(parsed.metadata.get("max_sample_nums"), 10)
            self.assertAlmostEqual(parsed.best, -1106.40, places=6)
            self.assertEqual(parsed.sample_lines, 2)

    def test_parse_run_log_counts_blank_or_too_short_samples(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            log_path = Path(temporary_dir) / "rag.log"
            log_path.write_text(
                "RUN_METADATA: {\"seed\": 42, \"llm_model\": \"gpt-4o-mini\", \"rag_enabled\": true, \"run_mode\": \"compare\", \"max_sample_nums\": 10}\n"
                "DEBUG: Sample 0 is empty or too short!\n"
                "DEBUG: Sample 1 prefix: ...\n",
                encoding="utf-8",
            )

            parsed = parse_run_log(log_path)
            self.assertEqual(parsed.sample_lines, 2)

    def test_parse_run_log_extracts_eval_and_retrieval_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            log_path = Path(temporary_dir) / "rag.log"
            log_path.write_text(
                "RUN_METADATA: {\"seed\": 42, \"llm_model\": \"gpt-4o-mini\", \"rag_enabled\": true, \"run_mode\": \"compare\", \"max_sample_nums\": 10}\n"
                "EVAL_SUMMARY: valid=12 total=20 ratio=0.600000\n"
                "EVAL_SUMMARY: valid=18 total=20 ratio=0.900000\n"
                "RETRIEVAL_DIAGNOSTICS: {\"top_score\": 0.72}\n"
                "RETRIEVAL_DIAGNOSTICS: {\"top_score\": 0.48}\n"
                "DEBUG: Sample 0 prefix: ...\n",
                encoding="utf-8",
            )

            parsed = parse_run_log(log_path)
            self.assertEqual(parsed.valid_eval_events, 2)
            self.assertEqual(parsed.total_valid_evals, 30)
            self.assertEqual(parsed.total_eval_attempts, 40)
            self.assertAlmostEqual(parsed.valid_eval_ratio or 0.0, 0.75, places=6)
            self.assertEqual(parsed.retrieval_events, 2)
            self.assertAlmostEqual(parsed.retrieval_mean_top_score or 0.0, 0.60, places=6)

    def test_build_pair_markdown_reports_delta_and_improvement(self) -> None:
        baseline = ParsedRun(
            best_scores=[-1200.0],
            sample_lines=10,
            metadata={
                "seed": 42,
                "llm_model": "gpt-4o-mini",
                "rag_enabled": False,
                "run_mode": "compare",
                "max_sample_nums": 10,
            },
        )
        rag = ParsedRun(
            best_scores=[-1100.0],
            sample_lines=10,
            metadata={
                "seed": 42,
                "llm_model": "gpt-4o-mini",
                "rag_enabled": True,
                "run_mode": "compare",
                "max_sample_nums": 10,
            },
        )

        markdown = build_pair_markdown(
            baseline_log=Path("results/baseline.log"),
            rag_log=Path("results/rag.log"),
            baseline=baseline,
            rag=rag,
            target_samples=10,
        )

        self.assertIn("Delta (rag - baseline): 100.000000", markdown)
        self.assertIn("Improved vs baseline: Yes", markdown)
        self.assertIn("Seed match: Yes", markdown)
        self.assertIn("Model match: Yes", markdown)
        self.assertIn("Policy compliant: Yes", markdown)

    def test_compare_policy_reports_violation_for_full_budget(self) -> None:
        baseline = ParsedRun(
            best_scores=[-1200.0],
            sample_lines=100,
            metadata={
                "seed": 42,
                "llm_model": "gpt-4o-mini",
                "rag_enabled": False,
                "run_mode": "compare",
                "max_sample_nums": 100,
            },
        )
        rag = ParsedRun(
            best_scores=[-1100.0],
            sample_lines=100,
            metadata={
                "seed": 42,
                "llm_model": "gpt-4o-mini",
                "rag_enabled": True,
                "run_mode": "compare",
                "max_sample_nums": 100,
            },
        )

        policy = evaluate_compare_policy(baseline=baseline, rag=rag)
        self.assertFalse(policy["policy_compliant"])

        markdown = build_pair_markdown(
            baseline_log=Path("results/baseline.log"),
            rag_log=Path("results/rag.log"),
            baseline=baseline,
            rag=rag,
            target_samples=10,
        )
        self.assertIn("Policy compliant: No", markdown)
        self.assertIn("Policy warnings", markdown)

    def test_compare_policy_reports_violation_when_sample_evidence_exceeds_budget(self) -> None:
        baseline = ParsedRun(
            best_scores=[-1200.0],
            sample_lines=12,
            metadata={
                "seed": 42,
                "llm_model": "gpt-4o-mini",
                "rag_enabled": False,
                "run_mode": "compare",
                "max_sample_nums": 10,
            },
        )
        rag = ParsedRun(
            best_scores=[-1100.0],
            sample_lines=11,
            metadata={
                "seed": 42,
                "llm_model": "gpt-4o-mini",
                "rag_enabled": True,
                "run_mode": "compare",
                "max_sample_nums": 10,
            },
        )

        policy = evaluate_compare_policy(baseline=baseline, rag=rag)
        self.assertFalse(policy["sample_evidence_compliant"])
        self.assertFalse(policy["policy_compliant"])

        markdown = build_pair_markdown(
            baseline_log=Path("results/baseline.log"),
            rag_log=Path("results/rag.log"),
            baseline=baseline,
            rag=rag,
            target_samples=10,
        )
        self.assertIn("Sample evidence within budget: No", markdown)
        self.assertIn("Observed sample evidence exceeds declared compare budget.", markdown)

    def test_acceptance_requires_same_model_budget_and_score_win(self) -> None:
        baseline = ParsedRun(
            best_scores=[-1200.0],
            sample_lines=10,
            metadata={
                "seed": 42,
                "llm_model": "gpt-4o-mini",
                "rag_enabled": False,
                "run_mode": "compare",
                "max_sample_nums": 10,
            },
            total_valid_evals=85,
            total_eval_attempts=100,
        )
        rag = ParsedRun(
            best_scores=[-1100.0],
            sample_lines=10,
            metadata={
                "seed": 42,
                "llm_model": "gpt-4o-mini",
                "rag_enabled": True,
                "run_mode": "compare",
                "max_sample_nums": 10,
            },
            total_valid_evals=90,
            total_eval_attempts=100,
        )

        acceptance = evaluate_acceptance(baseline=baseline, rag=rag, target_samples=10)
        self.assertTrue(acceptance["accepted"])
        self.assertEqual(acceptance["warnings"], [])

    def test_acceptance_requires_same_seed(self) -> None:
        baseline = ParsedRun(
            best_scores=[-1200.0],
            sample_lines=10,
            metadata={
                "seed": 41,
                "llm_model": "gpt-4o-mini",
                "rag_enabled": False,
                "run_mode": "compare",
                "max_sample_nums": 10,
            },
            total_valid_evals=90,
            total_eval_attempts=100,
        )
        rag = ParsedRun(
            best_scores=[-1000.0],
            sample_lines=10,
            metadata={
                "seed": 42,
                "llm_model": "gpt-4o-mini",
                "rag_enabled": True,
                "run_mode": "compare",
                "max_sample_nums": 10,
            },
            total_valid_evals=92,
            total_eval_attempts=100,
        )

        acceptance = evaluate_acceptance(baseline=baseline, rag=rag, target_samples=10)
        self.assertFalse(acceptance["accepted"])
        self.assertFalse(acceptance["same_seed"])
        self.assertIn("Seed mismatch: acceptance requires same seed.", acceptance["warnings"])

    def test_acceptance_supports_stage_eval_with_relative_gain_threshold(self) -> None:
        baseline = ParsedRun(
            best_scores=[-1200.0],
            sample_lines=20,
            metadata={
                "seed": 42,
                "llm_model": "gpt-4o-mini",
                "rag_enabled": False,
                "run_mode": "stage_eval",
                "max_sample_nums": 20,
            },
            total_valid_evals=90,
            total_eval_attempts=100,
        )
        rag = ParsedRun(
            best_scores=[-1050.0],
            sample_lines=20,
            metadata={
                "seed": 42,
                "llm_model": "gpt-4o-mini",
                "rag_enabled": True,
                "run_mode": "stage_eval",
                "max_sample_nums": 20,
            },
            total_valid_evals=91,
            total_eval_attempts=100,
        )

        acceptance = evaluate_acceptance(
            baseline=baseline,
            rag=rag,
            target_samples=20,
            acceptance_config=AcceptanceConfig(
                policy=ComparePolicyConfig(
                    allowed_run_modes=("stage_eval",),
                    compare_budget_cap=None,
                ),
                min_relative_gain_pct=10.0,
            ),
        )

        self.assertTrue(acceptance["accepted"])
        self.assertAlmostEqual(acceptance["relative_gain_pct"] or 0.0, 12.5, places=6)
        self.assertTrue(acceptance["relative_gain_guard"])

    def test_parse_run_log_extracts_extended_retrieval_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            log_path = Path(temporary_dir) / "rag.log"
            log_path.write_text(
                "RUN_METADATA: {\"seed\": 42, \"llm_model\": \"gpt-4o-mini\", \"rag_enabled\": true, \"run_mode\": \"stage_eval\", \"max_sample_nums\": 20}\n"
                "RETRIEVAL_DIAGNOSTICS: {\"top_score\": 0.72, \"top_score_gap\": 0.20, \"retrieval_confidence\": 0.61, \"injected_chars\": 480, \"unique_source_count\": 2, \"should_skip_retrieval\": false}\n"
                "RETRIEVAL_DIAGNOSTICS: {\"top_score\": 0.60, \"top_score_gap\": 0.10, \"retrieval_confidence\": 0.35, \"injected_chars\": 320, \"unique_source_count\": 1, \"should_skip_retrieval\": true}\n"
                "DEBUG: Sample 0 prefix: ...\n",
                encoding="utf-8",
            )

            parsed = parse_run_log(log_path)

            self.assertAlmostEqual(parsed.retrieval_mean_top_score or 0.0, 0.66, places=6)
            self.assertAlmostEqual(parsed.retrieval_mean_top_score_gap or 0.0, 0.15, places=6)
            self.assertAlmostEqual(parsed.retrieval_mean_confidence or 0.0, 0.48, places=6)
            self.assertAlmostEqual(parsed.retrieval_mean_injected_chars or 0.0, 400.0, places=6)
            self.assertAlmostEqual(parsed.retrieval_mean_unique_sources or 0.0, 1.5, places=6)
            self.assertAlmostEqual(parsed.retrieval_skip_ratio or 0.0, 0.5, places=6)


if __name__ == "__main__":
    unittest.main()
