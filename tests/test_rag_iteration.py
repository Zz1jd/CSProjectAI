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


class RAGIterationTests(unittest.TestCase):
    def test_primary_candidate_space_uses_explicit_v3_source_variants(self) -> None:
        config = RAGIterationConfig(
            max_attempts=10,
            source_variant_versions=(
                "v3.2.0_dynamic_history",
                "v3.3.0_full_corpus",
            ),
        )

        with mock.patch("scripts.experiments.space._governed_corpus_exists", return_value=True):
            candidates = build_primary_candidate_space(config)

        candidate_names = [candidate.name for candidate in candidates]
        self.assertIn("v3.2.0_dynamic_history_hybrid_raw_top2_ctx900", candidate_names)
        self.assertIn("v3.3.0_full_corpus_hybrid_raw_top2_ctx900", candidate_names)
        self.assertEqual(len(candidates), 9)

    def test_density_phase_candidates_inherit_best_query_strategy(self) -> None:
        best_query_candidate = RAGIterationCandidate(
            name="best_query",
            corpus_version="v3.0.0_official_foundation",
            retrieval_mode="vector",
            use_intent_query=False,
            top_k=2,
            score_threshold=0.0,
            max_context_chars=800,
        )

        density_candidates = build_density_phase_candidates(best_query_candidate)

        self.assertTrue(all(candidate.retrieval_mode == "vector" for candidate in density_candidates))
        self.assertTrue(all(candidate.use_intent_query is False for candidate in density_candidates))
        self.assertEqual([candidate.top_k for candidate in density_candidates], [1, 2, 3])

    def test_source_phase_candidates_inherit_control_thresholds_but_disable_intent_query(self) -> None:
        config = RAGIterationConfig(
            source_variant_versions=(
                "v3.2.0_dynamic_history",
                "v3.3.0_full_corpus",
            ),
        )
        best_control_candidate = RAGIterationCandidate(
            name="best_control",
            corpus_version=config.control_corpus_version,
            retrieval_mode="vector",
            use_intent_query=False,
            top_k=2,
            score_threshold=0.1,
            max_context_chars=700,
        )

        with mock.patch("scripts.experiments.space._governed_corpus_exists", return_value=True):
            source_candidates = build_source_phase_candidates(config, best_control_candidate)

        self.assertEqual(len(source_candidates), 2)
        self.assertTrue(all(candidate.retrieval_mode == "vector" for candidate in source_candidates))
        self.assertTrue(all(candidate.use_intent_query is False for candidate in source_candidates))
        self.assertTrue(all(candidate.score_threshold == 0.1 for candidate in source_candidates))
        self.assertTrue(all(candidate.corpus_version.startswith("v3.") for candidate in source_candidates))

    def test_source_phase_candidates_disable_intent_query_even_when_best_control_uses_it(self) -> None:
        config = RAGIterationConfig(
            source_variant_versions=(
                "v3.2.0_dynamic_history",
                "v3.3.0_full_corpus",
            ),
        )
        best_control_candidate = RAGIterationCandidate(
            name="best_control_intent",
            corpus_version=config.control_corpus_version,
            retrieval_mode="hybrid",
            use_intent_query=True,
            top_k=2,
            score_threshold=0.05,
            max_context_chars=900,
        )

        with mock.patch("scripts.experiments.space._governed_corpus_exists", return_value=True):
            source_candidates = build_source_phase_candidates(config, best_control_candidate)

        self.assertEqual(
            [candidate.name for candidate in source_candidates],
            [
                "v3.2.0_dynamic_history_hybrid_raw_top2_ctx900",
                "v3.3.0_full_corpus_hybrid_raw_top2_ctx900",
            ],
        )
        self.assertTrue(all(candidate.use_intent_query is False for candidate in source_candidates))

    def test_source_phase_candidates_preserve_intent_query_for_other_variants(self) -> None:
        config = RAGIterationConfig(source_variant_versions=("v3.9.0_future_variant",))
        best_control_candidate = RAGIterationCandidate(
            name="best_control_intent",
            corpus_version=config.control_corpus_version,
            retrieval_mode="hybrid",
            use_intent_query=True,
            top_k=2,
            score_threshold=0.05,
            max_context_chars=900,
        )

        with mock.patch("scripts.experiments.space._governed_corpus_exists", return_value=True):
            source_candidates = build_source_phase_candidates(config, best_control_candidate)

        self.assertEqual(len(source_candidates), 1)
        self.assertEqual(source_candidates[0].name, "v3.9.0_future_variant_hybrid_intent_top2_ctx900")
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
                    score_threshold=0.05,
                    max_context_chars=900,
                ),
                RAGIterationCandidate(
                    name="should_not_run",
                    corpus_version=config.control_corpus_version,
                    retrieval_mode="vector",
                    use_intent_query=True,
                    top_k=2,
                    score_threshold=0.0,
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
                    score_threshold=0.05,
                    max_context_chars=900,
                ),
                RAGIterationCandidate(
                    name="candidate_b",
                    corpus_version=config.control_corpus_version,
                    retrieval_mode="vector",
                    use_intent_query=True,
                    top_k=2,
                    score_threshold=0.00,
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


if __name__ == "__main__":
    unittest.main()