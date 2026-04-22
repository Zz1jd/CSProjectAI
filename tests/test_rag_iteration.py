import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.experiments.rag_iteration_config import RAGIterationCandidate
from scripts.experiments.rag_iteration_config import RAGIterationConfig
from scripts.experiments.space import build_density_phase_candidates
from scripts.experiments.space import build_primary_candidate_space
from scripts.experiments.space import build_query_phase_candidates
from scripts.experiments.space import build_source_phase_candidates
from scripts.run_rag_iteration import build_stage_acceptance_config
from scripts.run_rag_iteration import evaluate_stage_pair
from scripts.run_rag_iteration import run_all_model_iterations
from scripts.run_rag_iteration import run_iteration


def _write_mock_log(
    *,
    path: Path,
    run_mode: str,
    budget: int,
    rag_enabled: bool,
    best_score: float,
    retrieval_confidence: float = 0.0,
) -> None:
    retrieval_line = ""
    if rag_enabled:
        retrieval_line = (
            "RETRIEVAL_DIAGNOSTICS: "
            f"{{\"top_score\": 0.70, \"top_score_gap\": 0.20, \"retrieval_confidence\": {retrieval_confidence}, "
            "\"injected_chars\": 420, \"unique_source_count\": 1, \"should_skip_retrieval\": false}}\n"
        )

    path.write_text(
        f"RUN_METADATA: {{\"seed\": 42, \"llm_model\": \"gpt-3.5-turbo\", \"rag_enabled\": {str(rag_enabled).lower()}, \"run_mode\": \"{run_mode}\", \"max_sample_nums\": {budget}}}\n"
        f" Best score of island %d increased to %s 0 {best_score}\n"
        "EVAL_SUMMARY: valid=90 total=100 ratio=0.900000\n"
        f"{retrieval_line}"
        "DEBUG: Sample 0 prefix: ...\n",
        encoding="utf-8",
    )


def _patch_reasoning_client():
    """Stub LLM client construction so orchestration tests do not depend on real API credentials."""
    return mock.patch(
        "scripts.run_rag_iteration.llm_client_lib.LLMClient",
        return_value=object(),
    )


class RAGIterationTests(unittest.TestCase):
    def test_evaluate_stage_pair_marks_identical_logs_as_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            baseline_log = Path(temporary_dir) / "baseline.log"
            rag_log = Path(temporary_dir) / "rag.log"
            report_path = Path(temporary_dir) / "report.md"
            log_content = (
                "RUN_METADATA: {\"seed\": 42, \"llm_model\": \"gpt-3.5-turbo\", \"rag_enabled\": false, \"run_mode\": \"stage_eval\", \"max_sample_nums\": 20}\n"
                " Best score of island %d increased to %s 0 -1200.0\n"
                "EVAL_SUMMARY: valid=90 total=100 ratio=0.900000\n"
                "DEBUG: Sample 0 prefix: ...\n"
            )
            baseline_log.write_text(log_content, encoding="utf-8")
            rag_log.write_text(log_content, encoding="utf-8")

            acceptance_config = build_stage_acceptance_config(RAGIterationConfig())
            stage = evaluate_stage_pair(
                baseline_log=baseline_log,
                rag_log=rag_log,
                report_path=report_path,
                target_samples=20,
                acceptance_config=acceptance_config,
            )

            self.assertTrue(stage["logs_identical"])
            self.assertEqual(stage["baseline_log_sha256"], stage["rag_log_sha256"])
            self.assertFalse(stage["acceptance"]["accepted"])
            self.assertFalse(stage["acceptance"]["log_identity_guard"])
            self.assertIn("byte-identical", " ".join(stage["acceptance"]["warnings"]))

    def test_primary_candidate_space_stays_on_fixed_v3_3_corpus(self) -> None:
        config = RAGIterationConfig(max_attempts=10)

        candidates = build_primary_candidate_space(config)

        candidate_names = [candidate.name for candidate in candidates]
        self.assertIn("control_hybrid_intent_top3", candidate_names)
        self.assertIn("v3.3.0_official_full_density_top10_threshold05_chunk1500_overlap300", candidate_names)
        self.assertTrue(all(candidate.corpus_version == "v3.3.0_official_full" for candidate in candidates))
        self.assertEqual(len(candidates), 6)

    def test_source_variant_ablation_is_disabled_by_default(self) -> None:
        self.assertEqual(RAGIterationConfig().source_variant_versions, ())

    def test_density_phase_candidates_inherit_best_query_strategy(self) -> None:
        best_query_candidate = RAGIterationCandidate(
            name="best_query",
            corpus_version="v3.0.0_official_foundation",
            retrieval_mode="vector",
            use_intent_query=False,
            top_k=2,
            score_threshold=0.4,
            max_context_chars=800,
        )

        density_candidates = build_density_phase_candidates(best_query_candidate)

        # retrieval_mode is now fixed to hybrid regardless of the input candidate.
        self.assertTrue(all(candidate.retrieval_mode == "hybrid" for candidate in density_candidates))
        # use_intent_query and density params are inherited from the best query candidate.
        self.assertTrue(all(candidate.use_intent_query is False for candidate in density_candidates))
        self.assertEqual([candidate.top_k for candidate in density_candidates], [3, 5, 5, 10])
        self.assertEqual([candidate.score_threshold for candidate in density_candidates], [0.05, 0.05, 0.05, 0.05])
        self.assertEqual([candidate.chunk_size for candidate in density_candidates], [None, None, 900, 1500])
        self.assertEqual([candidate.chunk_overlap for candidate in density_candidates], [None, None, 150, 300])

    def test_source_phase_helper_inherits_control_thresholds_when_opted_in(self) -> None:
        config = RAGIterationConfig(
            source_variant_versions=(
                "v3.2.0_official_plus_history",
                "v3.3.0_official_full",
            ),
        )
        best_control_candidate = RAGIterationCandidate(
            name="best_control",
            corpus_version=config.control_corpus_version,
            retrieval_mode="vector",
            use_intent_query=False,
            top_k=2,
            score_threshold=0.5,
            max_context_chars=700,
            chunk_size=900,
            chunk_overlap=150,
        )

        with mock.patch("scripts.experiments.space._governed_corpus_exists", return_value=True):
            source_candidates = build_source_phase_candidates(config, best_control_candidate)

        self.assertEqual(len(source_candidates), 2)
        # retrieval_mode is now fixed to hybrid regardless of the control candidate.
        self.assertTrue(all(candidate.retrieval_mode == "hybrid" for candidate in source_candidates))
        # use_intent_query is inherited from the control candidate (False here).
        self.assertTrue(all(candidate.use_intent_query is False for candidate in source_candidates))
        self.assertTrue(all(candidate.score_threshold == 0.5 for candidate in source_candidates))
        self.assertTrue(all(candidate.corpus_version.startswith("v3.") for candidate in source_candidates))
        self.assertTrue(all(candidate.chunk_size == 900 for candidate in source_candidates))
        self.assertTrue(all(candidate.chunk_overlap == 150 for candidate in source_candidates))

    def test_source_phase_helper_appends_chunk_suffix_for_custom_chunking(self) -> None:
        config = RAGIterationConfig(source_variant_versions=("v3.2.0_official_plus_history",))
        best_control_candidate = RAGIterationCandidate(
            name="best_control_chunked",
            corpus_version=config.control_corpus_version,
            retrieval_mode="hybrid",
            use_intent_query=False,
            top_k=2,
            score_threshold=0.4,
            max_context_chars=900,
            chunk_size=900,
            chunk_overlap=150,
        )

        with mock.patch("scripts.experiments.space._governed_corpus_exists", return_value=True):
            source_candidates = build_source_phase_candidates(config, best_control_candidate)

        # ctx is no longer included in source candidate names.
        self.assertEqual(
            [candidate.name for candidate in source_candidates],
            ["v3.2.0_official_plus_history_hybrid_raw_top2_chunk900_overlap150"],
        )

    def test_source_phase_helper_inherits_intent_query_from_control(self) -> None:
        """Optional source ablations inherit use_intent_query from the best control candidate."""
        config = RAGIterationConfig(
            source_variant_versions=(
                "v3.2.0_official_plus_history",
                "v3.3.0_official_full",
            ),
        )
        best_control_candidate = RAGIterationCandidate(
            name="best_control_intent",
            corpus_version=config.control_corpus_version,
            retrieval_mode="hybrid",
            use_intent_query=True,
            top_k=2,
            score_threshold=0.4,
            max_context_chars=900,
        )

        with mock.patch("scripts.experiments.space._governed_corpus_exists", return_value=True):
            source_candidates = build_source_phase_candidates(config, best_control_candidate)

        # ctx is no longer in the name; use_intent_query is inherited (True here).
        self.assertEqual(
            [candidate.name for candidate in source_candidates],
            [
                "v3.2.0_official_plus_history_hybrid_intent_top2",
                "v3.3.0_official_full_hybrid_intent_top2",
            ],
        )
        self.assertTrue(all(candidate.use_intent_query is True for candidate in source_candidates))

    def test_source_phase_helper_preserves_intent_query_for_other_variants(self) -> None:
        config = RAGIterationConfig(source_variant_versions=("v3.9.0_future_variant",))
        best_control_candidate = RAGIterationCandidate(
            name="best_control_intent",
            corpus_version=config.control_corpus_version,
            retrieval_mode="hybrid",
            use_intent_query=True,
            top_k=2,
            score_threshold=0.4,
            max_context_chars=900,
        )

        with mock.patch("scripts.experiments.space._governed_corpus_exists", return_value=True):
            source_candidates = build_source_phase_candidates(config, best_control_candidate)

        # ctx is no longer in the name.
        self.assertEqual(len(source_candidates), 1)
        self.assertEqual(source_candidates[0].name, "v3.9.0_future_variant_hybrid_intent_top2")
        self.assertTrue(source_candidates[0].use_intent_query)

    def test_run_iteration_reuses_baselines_and_stops_after_stage2_success(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            config = RAGIterationConfig(
                results_dir=temporary_dir,
                log_dir=str(Path(temporary_dir) / "logs"),
                max_attempts=2,
            )
            candidates = [
                RAGIterationCandidate(
                    name="winner",
                    corpus_version=config.control_corpus_version,
                    retrieval_mode="hybrid",
                    use_intent_query=True,
                    top_k=2,
                    score_threshold=0.4,
                    max_context_chars=900,
                ),
                RAGIterationCandidate(
                    name="should_not_run",
                    corpus_version=config.control_corpus_version,
                    retrieval_mode="vector",
                    use_intent_query=True,
                    top_k=2,
                    score_threshold=0.35,
                    max_context_chars=800,
                ),
            ]

            call_labels: list[str] = []

            def fake_run_logged_experiment(*, label, runtime_config, log_path, dataset_path, max_sample_nums, log_dir, header_fields):
                call_labels.append(label)
                if label == "BASELINE_STAGE1":
                    _write_mock_log(path=log_path, run_mode="stage_eval", budget=max_sample_nums, rag_enabled=False, best_score=-1200.0)
                elif label == "BASELINE_STAGE2":
                    _write_mock_log(path=log_path, run_mode="stage_eval", budget=max_sample_nums, rag_enabled=False, best_score=-1180.0)
                elif label.endswith("RAG_STAGE1"):
                    _write_mock_log(path=log_path, run_mode="stage_eval", budget=max_sample_nums, rag_enabled=True, best_score=-1000.0, retrieval_confidence=0.61)
                elif label.endswith("RAG_STAGE2"):
                    _write_mock_log(path=log_path, run_mode="stage_eval", budget=max_sample_nums, rag_enabled=True, best_score=-1040.0, retrieval_confidence=0.63)
                else:
                    raise AssertionError(f"Unexpected label: {label}")

            with mock.patch("scripts.run_rag_iteration.run_logged_experiment", side_effect=fake_run_logged_experiment), mock.patch(
                "scripts.run_rag_iteration.probe_reasoning_support",
                return_value=None,
            ), _patch_reasoning_client(), mock.patch(
                "scripts.run_rag_iteration.make_timestamp",
                return_value="20260418_010203",
            ), mock.patch(
                "scripts.run_rag_iteration.make_timestamp",
                return_value="20260418_010203",
            ):
                summary = run_iteration(iteration_config=config, candidate_space=candidates)

            self.assertTrue(summary["success"])
            self.assertEqual(summary["winner"], "winner")
            self.assertEqual(len(summary["attempts"]), 1)
            self.assertEqual(call_labels.count("BASELINE_STAGE1"), 1)
            self.assertEqual(call_labels.count("BASELINE_STAGE2"), 1)
            self.assertNotIn("ATTEMPT_02_RAG_STAGE1", call_labels)
            self.assertEqual(summary["baseline_stage1_source"], "generated")
            self.assertEqual(summary["baseline_stage2_source"], "generated")

    def test_run_iteration_reuses_cached_baselines_across_repeated_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            config = RAGIterationConfig(
                results_dir=temporary_dir,
                log_dir=str(Path(temporary_dir) / "logs"),
                max_attempts=1,
            )
            candidates = [
                RAGIterationCandidate(
                    name="candidate_a",
                    corpus_version=config.control_corpus_version,
                    retrieval_mode="hybrid",
                    use_intent_query=True,
                    top_k=2,
                    score_threshold=0.4,
                    max_context_chars=900,
                ),
            ]

            call_labels: list[str] = []

            def fake_run_logged_experiment(*, label, runtime_config, log_path, dataset_path, max_sample_nums, log_dir, header_fields):
                call_labels.append(label)
                if label == "BASELINE_STAGE1":
                    _write_mock_log(path=log_path, run_mode="stage_eval", budget=max_sample_nums, rag_enabled=False, best_score=-1200.0)
                elif label == "BASELINE_STAGE2":
                    _write_mock_log(path=log_path, run_mode="stage_eval", budget=max_sample_nums, rag_enabled=False, best_score=-1180.0)
                elif label.endswith("RAG_STAGE1"):
                    _write_mock_log(path=log_path, run_mode="stage_eval", budget=max_sample_nums, rag_enabled=True, best_score=-1195.0, retrieval_confidence=0.20)
                else:
                    raise AssertionError(f"Unexpected label: {label}")

            with mock.patch("scripts.run_rag_iteration.run_logged_experiment", side_effect=fake_run_logged_experiment), mock.patch(
                "scripts.run_rag_iteration.probe_reasoning_support",
                return_value=None,
            ), _patch_reasoning_client(), mock.patch(
                "scripts.run_rag_iteration.make_timestamp",
                side_effect=["20260422_111111", "20260422_222222"],
            ), mock.patch(
                "scripts.run_rag_iteration.make_timestamp",
                side_effect=["20260422_111111", "20260422_222222"],
            ):
                first_summary = run_iteration(iteration_config=config, candidate_space=candidates)
                second_summary = run_iteration(iteration_config=config, candidate_space=candidates)

            self.assertEqual(call_labels.count("BASELINE_STAGE1"), 1)
            self.assertEqual(call_labels.count("BASELINE_STAGE2"), 1)
            self.assertEqual(call_labels.count("ATTEMPT_01_RAG_STAGE1"), 2)
            self.assertEqual(first_summary["baseline_stage1_source"], "generated")
            self.assertEqual(first_summary["baseline_stage2_source"], "generated")
            self.assertEqual(second_summary["baseline_stage1_source"], "cache")
            self.assertEqual(second_summary["baseline_stage2_source"], "cache")
            self.assertTrue((Path(second_summary["experiment_dir"]) / "baseline_stage1.log").exists())
            self.assertTrue((Path(second_summary["experiment_dir"]) / "baseline_stage2.log").exists())

    def test_run_iteration_stops_after_max_attempts_without_stage2(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            config = RAGIterationConfig(
                results_dir=temporary_dir,
                log_dir=str(Path(temporary_dir) / "logs"),
                max_attempts=2,
            )
            candidates = [
                RAGIterationCandidate(
                    name="candidate_a",
                    corpus_version=config.control_corpus_version,
                    retrieval_mode="hybrid",
                    use_intent_query=True,
                    top_k=2,
                    score_threshold=0.4,
                    max_context_chars=900,
                ),
                RAGIterationCandidate(
                    name="candidate_b",
                    corpus_version=config.control_corpus_version,
                    retrieval_mode="vector",
                    use_intent_query=True,
                    top_k=2,
                    score_threshold=0.35,
                    max_context_chars=800,
                ),
            ]

            call_labels: list[str] = []

            def fake_run_logged_experiment(*, label, runtime_config, log_path, dataset_path, max_sample_nums, log_dir, header_fields):
                call_labels.append(label)
                if label == "BASELINE_STAGE1":
                    _write_mock_log(path=log_path, run_mode="stage_eval", budget=max_sample_nums, rag_enabled=False, best_score=-1200.0)
                elif label == "BASELINE_STAGE2":
                    _write_mock_log(path=log_path, run_mode="stage_eval", budget=max_sample_nums, rag_enabled=False, best_score=-1180.0)
                elif label.endswith("RAG_STAGE1"):
                    _write_mock_log(path=log_path, run_mode="stage_eval", budget=max_sample_nums, rag_enabled=True, best_score=-1195.0, retrieval_confidence=0.20)
                else:
                    raise AssertionError(f"Unexpected label: {label}")

            with mock.patch("scripts.run_rag_iteration.run_logged_experiment", side_effect=fake_run_logged_experiment), mock.patch(
                "scripts.run_rag_iteration.probe_reasoning_support",
                return_value=None,
            ), _patch_reasoning_client(), mock.patch(
                "scripts.run_rag_iteration.make_timestamp",
                return_value="20260418_020304",
            ), mock.patch(
                "scripts.run_rag_iteration.make_timestamp",
                return_value="20260418_020304",
            ):
                summary = run_iteration(iteration_config=config, candidate_space=candidates)

            self.assertFalse(summary["success"])
            self.assertEqual(summary["stop_reason"], "max_attempts_reached")
            self.assertEqual(len(summary["attempts"]), 2)
            self.assertEqual(call_labels.count("BASELINE_STAGE1"), 1)
            self.assertEqual(call_labels.count("BASELINE_STAGE2"), 1)
            self.assertNotIn("ATTEMPT_01_RAG_STAGE2", call_labels)
            self.assertNotIn("ATTEMPT_02_RAG_STAGE2", call_labels)

    def test_run_iteration_marks_candidate_space_exhausted_when_adaptive_space_ends_early(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            config = RAGIterationConfig(
                results_dir=temporary_dir,
                log_dir=str(Path(temporary_dir) / "logs"),
                max_attempts=10,
            )

            call_labels: list[str] = []

            def fake_run_logged_experiment(*, label, runtime_config, log_path, dataset_path, max_sample_nums, log_dir, header_fields):
                call_labels.append(label)
                if label == "BASELINE_STAGE1":
                    _write_mock_log(path=log_path, run_mode="stage_eval", budget=max_sample_nums, rag_enabled=False, best_score=-1200.0)
                elif label == "BASELINE_STAGE2":
                    _write_mock_log(path=log_path, run_mode="stage_eval", budget=max_sample_nums, rag_enabled=False, best_score=-1180.0)
                elif label.endswith("RAG_STAGE1"):
                    _write_mock_log(path=log_path, run_mode="stage_eval", budget=max_sample_nums, rag_enabled=True, best_score=-1195.0, retrieval_confidence=0.20)
                else:
                    raise AssertionError(f"Unexpected label: {label}")

            with mock.patch("scripts.run_rag_iteration.run_logged_experiment", side_effect=fake_run_logged_experiment), mock.patch(
                "scripts.run_rag_iteration.probe_reasoning_support",
                return_value=None,
            ), _patch_reasoning_client(), mock.patch(
                "scripts.run_rag_iteration.make_timestamp",
                return_value="20260422_113904",
            ), mock.patch(
                "scripts.run_rag_iteration.make_timestamp",
                return_value="20260422_113904",
            ):
                summary = run_iteration(iteration_config=config)

            self.assertFalse(summary["success"])
            self.assertEqual(summary["stop_reason"], "candidate_space_exhausted")
            self.assertEqual(len(summary["attempts"]), 6)
            self.assertEqual(call_labels.count("BASELINE_STAGE1"), 1)
            self.assertEqual(call_labels.count("BASELINE_STAGE2"), 1)

    def test_run_iteration_records_attempt_error_and_continues(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            config = RAGIterationConfig(
                results_dir=temporary_dir,
                log_dir=str(Path(temporary_dir) / "logs"),
                max_attempts=2,
            )
            candidates = [
                RAGIterationCandidate(
                    name="broken_candidate",
                    corpus_version=config.control_corpus_version,
                    retrieval_mode="hybrid",
                    use_intent_query=True,
                    top_k=2,
                    score_threshold=0.4,
                    max_context_chars=900,
                ),
                RAGIterationCandidate(
                    name="recovered_winner",
                    corpus_version=config.control_corpus_version,
                    retrieval_mode="vector",
                    use_intent_query=False,
                    top_k=2,
                    score_threshold=0.35,
                    max_context_chars=800,
                ),
            ]

            def fake_run_logged_experiment(*, label, runtime_config, log_path, dataset_path, max_sample_nums, log_dir, header_fields):
                if label == "BASELINE_STAGE1":
                    _write_mock_log(path=log_path, run_mode="stage_eval", budget=max_sample_nums, rag_enabled=False, best_score=-1200.0)
                elif label == "BASELINE_STAGE2":
                    _write_mock_log(path=log_path, run_mode="stage_eval", budget=max_sample_nums, rag_enabled=False, best_score=-1180.0)
                elif label == "ATTEMPT_01_RAG_STAGE1":
                    raise RuntimeError("stage1 boom")
                elif label == "ATTEMPT_02_RAG_STAGE1":
                    _write_mock_log(path=log_path, run_mode="stage_eval", budget=max_sample_nums, rag_enabled=True, best_score=-1000.0, retrieval_confidence=0.60)
                elif label == "ATTEMPT_02_RAG_STAGE2":
                    _write_mock_log(path=log_path, run_mode="stage_eval", budget=max_sample_nums, rag_enabled=True, best_score=-1020.0, retrieval_confidence=0.62)
                else:
                    raise AssertionError(f"Unexpected label: {label}")

            with mock.patch("scripts.run_rag_iteration.run_logged_experiment", side_effect=fake_run_logged_experiment), mock.patch(
                "scripts.run_rag_iteration.probe_reasoning_support",
                return_value=None,
            ), _patch_reasoning_client(), mock.patch(
                "scripts.run_rag_iteration.make_timestamp",
                return_value="20260418_030405",
            ), mock.patch(
                "scripts.run_rag_iteration.make_timestamp",
                return_value="20260418_030405",
            ):
                summary = run_iteration(iteration_config=config, candidate_space=candidates)

            self.assertTrue(summary["success"])
            self.assertEqual(summary["winner"], "recovered_winner")
            self.assertEqual(len(summary["attempts"]), 2)
            self.assertEqual(summary["attempts"][0]["status"], "failed")
            self.assertEqual(summary["attempts"][0]["failed_stage"], "stage1")
            self.assertEqual(summary["attempts"][0]["error"]["type"], "RuntimeError")
            self.assertEqual(summary["attempts"][1]["status"], "stage2_accepted")
            self.assertTrue((Path(temporary_dir) / "20260418_030405_qwen3_5_397b_a17b" / "attempt_01.json").exists())

    def test_run_iteration_blocks_when_reasoning_precheck_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            config = RAGIterationConfig(
                results_dir=temporary_dir,
                log_dir=str(Path(temporary_dir) / "logs"),
                max_attempts=1,
            )

            with mock.patch(
                "scripts.run_rag_iteration.probe_reasoning_support",
                side_effect=RuntimeError("reasoning unsupported"),
            ), _patch_reasoning_client(), mock.patch(
                "scripts.run_rag_iteration.make_timestamp",
                return_value="20260422_010101",
            ), mock.patch(
                "scripts.run_rag_iteration.make_timestamp",
                return_value="20260422_010101",
            ), mock.patch("scripts.run_rag_iteration.run_logged_experiment") as run_logged_experiment_mock:
                summary = run_iteration(iteration_config=config, candidate_space=())

            self.assertFalse(summary["success"])
            self.assertEqual(summary["stop_reason"], "reasoning_precheck_failed")
            self.assertFalse(summary["reasoning_precheck"]["passed"])
            self.assertEqual(summary["reasoning_precheck"]["attempts"][0]["probe"]["request_mode"], "enable_thinking")
            run_logged_experiment_mock.assert_not_called()

    def test_run_all_model_iterations_writes_suite_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            config = RAGIterationConfig(results_dir=temporary_dir)

            fake_summaries = [
                {
                    "experiment_dir": str(Path(temporary_dir) / "20260422_020202_qwen3_5_397b_a17b"),
                    "success": False,
                    "winner": None,
                    "stop_reason": "reasoning_precheck_failed",
                    "reasoning_precheck": {"passed": False},
                },
                {
                    "experiment_dir": str(Path(temporary_dir) / "20260422_020202_gpt_5_4"),
                    "success": True,
                    "winner": "candidate_a",
                    "stop_reason": "attempt_01_passed_stage2",
                    "reasoning_precheck": {"passed": True},
                },
            ]

            with mock.patch(
                "scripts.run_rag_iteration.make_timestamp",
                return_value="20260422_020202",
            ), mock.patch(
                "scripts.run_rag_iteration.run_iteration",
                side_effect=fake_summaries,
            ) as run_iteration_mock:
                summary = run_all_model_iterations(iteration_config=config, candidate_space=())

            self.assertEqual(summary["timestamp"], "20260422_020202")
            self.assertEqual(len(summary["model_runs"]), 2)
            self.assertEqual(run_iteration_mock.call_count, 2)
            self.assertTrue((Path(temporary_dir) / "20260422_020202_suite_summary.json").exists())


if __name__ == "__main__":
    unittest.main()