import unittest
from unittest import mock
from pathlib import Path

from scripts.compare_rag import ParsedRun
from scripts.compare_rag import _resolve_log_path
from scripts.compare_rag import build_pair_markdown
from scripts.compare_rag import parse_run_log


class CompareLogsTests(unittest.TestCase):
    def test_resolve_log_path_prefers_explicit_path(self) -> None:
        results_dir = mock.Mock()
        explicit = Path("results/explicit.log")

        resolved = _resolve_log_path(
            explicit_path=str(explicit),
            results_dir=results_dir,
            pattern="compare_baseline_*.log",
            label="baseline",
        )
        self.assertEqual(resolved, explicit)

    def test_resolve_log_path_falls_back_to_latest_match(self) -> None:
        older = Path("results/compare_baseline_20260101_000000.log")
        newer = Path("results/compare_baseline_20260102_000000.log")
        results_dir = mock.Mock()
        results_dir.glob.return_value = [older, newer]

        resolved = _resolve_log_path(
            explicit_path="",
            results_dir=results_dir,
            pattern="compare_baseline_*.log",
            label="baseline",
        )
        self.assertEqual(resolved, newer)

    def test_parse_run_log_extracts_metadata_best_and_progress(self) -> None:
        log_path = mock.Mock()
        log_path.read_text.return_value = (
            "RUN_METADATA: {\"seed\": 42, \"llm_model\": \"gpt-4o-mini\", \"rag_enabled\": true, \"run_mode\": \"compare\", \"max_sample_nums\": 10}\n"
            " Best score of island %d increased to %s 0 -1161.98\n"
            " Best score of island %d increased to %s 2 -1106.40\n"
            "DEBUG: Sample 0 prefix: ...\n"
            "DEBUG: Sample 1 prefix: ...\n"
        )

        parsed = parse_run_log(log_path)

        self.assertEqual(parsed.metadata.get("seed"), 42)
        self.assertEqual(parsed.metadata.get("llm_model"), "gpt-4o-mini")
        self.assertEqual(parsed.metadata.get("run_mode"), "compare")
        self.assertEqual(parsed.metadata.get("max_sample_nums"), 10)
        self.assertAlmostEqual(parsed.best, -1106.40, places=6)
        self.assertEqual(parsed.sample_lines, 2)

    def test_parse_run_log_extracts_eval_and_retrieval_diagnostics(self) -> None:
        log_path = mock.Mock()
        log_path.read_text.return_value = (
            "RUN_METADATA: {\"seed\": 42, \"llm_model\": \"gpt-4o-mini\", \"rag_enabled\": true, \"run_mode\": \"compare\", \"max_sample_nums\": 10}\n"
            "EVAL_SUMMARY: valid=12 total=20 ratio=0.600000\n"
            "EVAL_SUMMARY: valid=18 total=20 ratio=0.900000\n"
            "RETRIEVAL_DIAGNOSTICS: {\"top_score\": 0.72, \"injected_source_count\": 1, \"applied_retrieval_policy\": \"summary_only\"}\n"
            "RETRIEVAL_DIAGNOSTICS: {\"top_score\": 0.48, \"injected_source_count\": 2, \"applied_retrieval_policy\": \"summary_plus_leaf\"}\n"
            "DEBUG: Sample 0 prefix: ...\n"
        )

        parsed = parse_run_log(log_path)
        self.assertEqual(parsed.valid_eval_events, 2)
        self.assertEqual(parsed.total_valid_evals, 30)
        self.assertEqual(parsed.total_eval_attempts, 40)
        self.assertAlmostEqual(parsed.valid_eval_ratio or 0.0, 0.75, places=6)
        self.assertEqual(parsed.retrieval_events, 2)
        self.assertAlmostEqual(parsed.retrieval_mean_top_score or 0.0, 0.60, places=6)
        self.assertAlmostEqual(parsed.retrieval_mean_injected_sources or 0.0, 1.5, places=6)
        self.assertAlmostEqual(parsed.retrieval_multi_source_hit_rate or 0.0, 0.5, places=6)
        self.assertEqual(parsed.retrieval_policy_counts, {"summary_only": 1, "summary_plus_leaf": 1})

    def test_build_pair_markdown_reports_metrics_without_acceptance_sections(self) -> None:
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
            retrieval_events=2,
            retrieval_mean_injected_sources=1.5,
            retrieval_multi_source_hit_rate=0.5,
            retrieval_policy_counts={"summary_only": 1, "summary_plus_leaf": 1},
        )

        markdown = build_pair_markdown(
            baseline_log=Path("results/baseline.log"),
            rag_log=Path("results/rag.log"),
            baseline=baseline,
            rag=rag,
            target_samples=10,
        )

        self.assertIn("Delta (rag - baseline): 100.000000", markdown)
        self.assertIn("RAG mean injected sources: 1.500000", markdown)
        self.assertIn("RAG multi-source hit rate: 50.00%", markdown)
        self.assertNotIn("## Acceptance", markdown)
        self.assertNotIn("## Policy Compliance", markdown)

    def test_parse_run_log_extracts_extended_retrieval_diagnostics(self) -> None:
        log_path = mock.Mock()
        log_path.read_text.return_value = (
            "RUN_METADATA: {\"seed\": 42, \"llm_model\": \"gpt-4o-mini\", \"rag_enabled\": true, \"run_mode\": \"compare\", \"max_sample_nums\": 20}\n"
            "RETRIEVAL_DIAGNOSTICS: {\"top_score\": 0.72, \"top_score_gap\": 0.20, \"retrieval_confidence\": 0.61, \"injected_chars\": 480, \"unique_source_count\": 2, \"should_skip_retrieval\": false}\n"
            "RETRIEVAL_DIAGNOSTICS: {\"top_score\": 0.60, \"top_score_gap\": 0.10, \"retrieval_confidence\": 0.35, \"injected_chars\": 320, \"unique_source_count\": 1, \"should_skip_retrieval\": true}\n"
            "DEBUG: Sample 0 prefix: ...\n"
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
