import unittest
from pathlib import Path
from unittest import mock

from scripts.run_rag_compare_repro_20260420_133019 import CompareCandidate
from scripts.run_rag_compare_repro_20260420_133019 import CompareRunConfig
from scripts.run_rag_compare_repro_20260420_133019 import ModelSpec
from scripts.run_rag_compare_repro_20260420_133019 import RUN_LOG_SUFFIX
from scripts.run_rag_compare_repro_20260420_133019 import run_compare_suite
from scripts.run_rag_compare_repro_20260420_133019 import run_single_rag_candidate


class CompareRunnerTests(unittest.TestCase):
    def test_compare_runner_uses_txt_log_suffix(self) -> None:
        self.assertEqual(RUN_LOG_SUFFIX, ".txt")

    def test_run_compare_suite_records_both_rag_results_without_acceptance(self) -> None:
        config = CompareRunConfig(
            seed=42,
            run_mode="compare",
            budget=2,
            results_dir="results/test_suite",
            log_dir="logs/test_suite",
        )
        candidates = (
            CompareCandidate(
                name="smoke_v32_dynamic_history",
                corpus_version="v3.2.0_dynamic_history",
                retrieval_mode="hybrid",
                use_intent_query=False,
                top_k=2,
                score_threshold=0.05,
                max_context_chars=900,
                chunk_size=1200,
                chunk_overlap=200,
            ),
            CompareCandidate(
                name="smoke_v33_full_corpus",
                corpus_version="v3.3.0_full_corpus",
                retrieval_mode="hybrid",
                use_intent_query=False,
                top_k=2,
                score_threshold=0.05,
                max_context_chars=900,
                chunk_size=1200,
                chunk_overlap=200,
            ),
        )
        model_spec = ModelSpec(model_name="gpt-3.5-turbo", result_label="repro_gpt_3_5_turbo_20260420")
        baseline_run = mock.Mock(best=-1200.0, sample_lines=2, valid_eval_ratio=0.9, evals_per_sample=1.0, retrieval_events=0, retrieval_mean_top_score=None, retrieval_mean_top_score_gap=None, retrieval_mean_confidence=None, retrieval_mean_injected_chars=None, retrieval_mean_injected_sources=None, retrieval_mean_unique_sources=None, retrieval_multi_source_hit_rate=None, retrieval_policy_counts={}, retrieval_skip_ratio=None)
        rag_v32 = mock.Mock(best=-1190.0, sample_lines=2, valid_eval_ratio=0.9, evals_per_sample=1.0, retrieval_events=1, retrieval_mean_top_score=0.7, retrieval_mean_top_score_gap=0.2, retrieval_mean_confidence=0.2, retrieval_mean_injected_chars=420.0, retrieval_mean_injected_sources=1.0, retrieval_mean_unique_sources=1.0, retrieval_multi_source_hit_rate=0.0, retrieval_policy_counts={"summary_only": 1}, retrieval_skip_ratio=0.0)
        rag_v33 = mock.Mock(best=-1180.0, sample_lines=2, valid_eval_ratio=0.9, evals_per_sample=1.0, retrieval_events=1, retrieval_mean_top_score=0.8, retrieval_mean_top_score_gap=0.3, retrieval_mean_confidence=0.3, retrieval_mean_injected_chars=520.0, retrieval_mean_injected_sources=1.0, retrieval_mean_unique_sources=1.0, retrieval_multi_source_hit_rate=0.0, retrieval_policy_counts={"summary_plus_leaf": 1}, retrieval_skip_ratio=0.0)

        with mock.patch(
            "scripts.run_rag_compare_repro_20260420_133019._load_runtime_bindings",
            return_value=(None, None, None, mock.Mock(return_value="20260425_010101"), None),
        ), mock.patch(
            "scripts.run_rag_compare_repro_20260420_133019._resolve_results_dir",
            return_value=Path("results/test_suite"),
        ), mock.patch(
            "scripts.run_rag_compare_repro_20260420_133019.Path.mkdir",
        ), mock.patch(
            "scripts.run_rag_compare_repro_20260420_133019._run_baseline",
            return_value=(Path("results/test_suite/baseline.txt"), baseline_run),
        ), mock.patch(
            "scripts.run_rag_compare_repro_20260420_133019._run_rag_candidate",
            side_effect=[
                (Path("results/test_suite/rag_smoke_v32_dynamic_history.txt"), rag_v32),
                (Path("results/test_suite/rag_smoke_v33_full_corpus.txt"), rag_v33),
            ],
        ), mock.patch(
            "scripts.run_rag_compare_repro_20260420_133019.Path.write_text",
        ), mock.patch(
            "scripts.run_rag_compare_repro_20260420_133019._write_json",
        ):
            summary = run_compare_suite(
                compare_config=config,
                candidate_space=candidates,
                model_spec=model_spec,
            )

        self.assertEqual(summary["budget"], 2)
        self.assertNotIn("acceptance", summary)
        self.assertEqual(summary["baseline"]["best"], -1200.0)
        self.assertEqual(len(summary["rag_runs"]), 2)
        self.assertEqual(summary["rag_runs"][0]["candidate"]["name"], "smoke_v32_dynamic_history")
        self.assertEqual(summary["rag_runs"][1]["candidate"]["name"], "smoke_v33_full_corpus")
        self.assertEqual(summary["best_rag"]["candidate"]["name"], "smoke_v33_full_corpus")

    def test_run_single_rag_candidate_skips_baseline(self) -> None:
        config = CompareRunConfig(
            seed=42,
            run_mode="compare",
            budget=1,
            results_dir="results/test_single",
            log_dir="logs/test_single",
        )
        candidate = CompareCandidate(
            name="smoke_v33_full_corpus",
            corpus_version="v3.3.0_full_corpus",
            retrieval_mode="hybrid",
            use_intent_query=False,
            top_k=2,
            score_threshold=0.05,
            max_context_chars=900,
            chunk_size=1200,
            chunk_overlap=200,
        )
        model_spec = ModelSpec(model_name="gpt-3.5-turbo", result_label="repro_gpt_3_5_turbo_20260420")
        rag_run = mock.Mock(best=-1180.0, sample_lines=1, valid_eval_ratio=0.9, evals_per_sample=1.0, retrieval_events=1, retrieval_mean_top_score=0.7, retrieval_mean_top_score_gap=0.2, retrieval_mean_confidence=0.2, retrieval_mean_injected_chars=420.0, retrieval_mean_injected_sources=1.0, retrieval_mean_unique_sources=1.0, retrieval_multi_source_hit_rate=0.0, retrieval_policy_counts={"summary_only": 1}, retrieval_skip_ratio=0.0)

        with mock.patch(
            "scripts.run_rag_compare_repro_20260420_133019._load_runtime_bindings",
            return_value=(None, None, None, mock.Mock(return_value="20260425_020202"), None),
        ), mock.patch(
            "scripts.run_rag_compare_repro_20260420_133019._resolve_results_dir",
            return_value=Path("results/test_single"),
        ), mock.patch(
            "scripts.run_rag_compare_repro_20260420_133019.Path.mkdir",
        ), mock.patch(
            "scripts.run_rag_compare_repro_20260420_133019._run_rag_candidate",
            return_value=(Path("results/test_single/rag_smoke_v33_full_corpus.txt"), rag_run),
        ), mock.patch(
            "scripts.run_rag_compare_repro_20260420_133019._write_json",
        ):
            summary = run_single_rag_candidate(
                compare_config=config,
                candidate=candidate,
                model_spec=model_spec,
            )

        self.assertEqual(summary["budget"], 1)
        self.assertEqual(summary["candidate"]["name"], "smoke_v33_full_corpus")
        self.assertNotIn("baseline", summary)


if __name__ == "__main__":
    unittest.main()
