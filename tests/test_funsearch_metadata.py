import unittest

from implementation import config as config_lib
from implementation import funsearch


class FunsearchMetadataTests(unittest.TestCase):
    def test_build_run_metadata_contains_core_fields(self) -> None:
        config_obj = config_lib.Config(
            samples_per_prompt=4,
            evaluate_timeout_seconds=30,
            api=config_lib.APIConfig(
                base_url="https://api.example.test/v1",
                api_key="placeholder-key",
                timeout_seconds=60,
                max_retries=2,
            ),
            rag=config_lib.RAGConfig(
                enabled=True,
                corpus_root="corpus/",
                top_k=3,
                retrieval_mode="hybrid",
                score_threshold=0.1,
                max_context_chars=1600,
                enable_diagnostics=True,
                use_intent_query=False,
                embedding_model="text-embedding-3-large",
                embedding_base_url="https://embed.example.test/v1",
                embedding_api_key="embed-key",
            ),
            random_seed=42,
            llm_model="gpt-4o-mini",
            run_mode="compare",
            model_track="upgrade",
            model_upgrade_name="gpt-4.1-mini",
        )

        metadata = funsearch.build_run_metadata(
            config_obj=config_obj,
            dataset_path="./cvrplib/setB",
            max_sample_nums=100,
        )

        self.assertEqual(metadata["seed"], 42)
        self.assertEqual(metadata["llm_model"], "gpt-4o-mini")
        self.assertTrue(metadata["rag_enabled"])
        self.assertEqual(metadata["rag_top_k"], 3)
        self.assertEqual(metadata["dataset_path"], "./cvrplib/setB")
        self.assertEqual(metadata["max_sample_nums"], 100)
        self.assertEqual(metadata["effective_max_sample_nums"], 100)
        self.assertEqual(metadata["run_mode"], "compare")
        self.assertTrue(metadata["api_base_url_explicit"])
        self.assertTrue(metadata["api_key_explicit"])
        self.assertEqual(metadata["model_track"], "upgrade")
        self.assertEqual(metadata["model_upgrade_name"], "gpt-4.1-mini")
        self.assertEqual(metadata["rag_retrieval_mode"], "hybrid")
        self.assertAlmostEqual(metadata["rag_score_threshold"], 0.1)
        self.assertEqual(metadata["rag_max_context_chars"], 1600)
        self.assertTrue(metadata["rag_diagnostics_enabled"])
        self.assertFalse(metadata["rag_use_intent_query"])
        self.assertEqual(metadata["rag_embedding_model"], "text-embedding-3-large")
        self.assertTrue(metadata["rag_embedding_base_url_explicit"])
        self.assertTrue(metadata["rag_embedding_api_key_explicit"])
        self.assertNotIn("api_key", metadata)


if __name__ == "__main__":
    unittest.main()
