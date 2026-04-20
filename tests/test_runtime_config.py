import unittest
from unittest import mock

from main import COMPARE_MAX_SAMPLE_NUMS
from main import apply_compare_policy
from main import build_runtime_config
from main import validate_runtime_config

from implementation import config as config_lib


class RuntimeConfigTests(unittest.TestCase):
    def test_build_runtime_config_uses_single_source_defaults(self) -> None:
        config_obj = build_runtime_config()
        expected = config_lib.Config()
        self.assertEqual(config_obj.llm_model, expected.llm_model)
        self.assertEqual(config_obj.rag.corpus_version, "v3.0.0_official_foundation")
        self.assertEqual(config_obj.rag.corpus_roots, ("external_corpus/v3.0.0_official_foundation",))
        self.assertEqual(config_obj.rag.retrieval_mode, expected.rag.retrieval_mode)
        self.assertEqual(config_obj.api.base_url, expected.api.base_url)
        self.assertEqual(config_obj.rag.embedding_base_url, expected.rag.embedding_base_url)

    def test_apply_compare_policy_caps_budget(self) -> None:
        capped = apply_compare_policy(run_mode="compare", requested_budget=100)
        self.assertEqual(capped, COMPARE_MAX_SAMPLE_NUMS)

    def test_apply_compare_policy_keeps_full_mode_budget(self) -> None:
        kept = apply_compare_policy(run_mode="full", requested_budget=100)
        self.assertEqual(kept, 100)

    def test_validate_runtime_config_requires_upgrade_model_name(self) -> None:
        config_obj = config_lib.Config(model_track="upgrade", model_upgrade_name=None)
        with self.assertRaises(ValueError):
            validate_runtime_config(config_obj)

    def test_validate_runtime_config_accepts_baseline_track(self) -> None:
        config_obj = config_lib.Config(model_track="baseline", model_upgrade_name=None)
        validate_runtime_config(config_obj)

    def test_report_script_configs_are_centralized(self) -> None:
        compare_report = config_lib.CompareReportConfig()
        historical_report = config_lib.HistoricalReportConfig()
        runtime_defaults = config_lib.RuntimeDefaults()

        self.assertEqual(compare_report.target_samples, runtime_defaults.compare_max_sample_nums)
        self.assertEqual(historical_report.target_samples, runtime_defaults.max_sample_nums)

    def test_rag_config_defaults_derive_corpus_root_from_version(self) -> None:
        rag_config = config_lib.RAGConfig(corpus_version="v9.9.9")
        self.assertEqual(rag_config.corpus_roots, ("external_corpus/v9.9.9",))

    def test_multi_round_uses_default_governed_corpus_roots_provider(self) -> None:
        with mock.patch.object(
                config_lib,
                "default_governed_corpus_roots",
                return_value=("external_corpus/v9.9.9",),
        ):
            multi_round = config_lib.MultiRoundScriptConfig()

        self.assertEqual(multi_round.rounds[1].corpus_roots, ("external_corpus/v9.9.9",))
        self.assertEqual(multi_round.rounds[2].corpus_roots, ("external_corpus/v9.9.9",))



if __name__ == "__main__":
    unittest.main()
