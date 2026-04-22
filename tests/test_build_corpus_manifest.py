import dataclasses
import tempfile
import unittest
from pathlib import Path

from implementation import config as config_lib
from scripts import build_corpus_manifest


class BuildCorpusManifestScriptTests(unittest.TestCase):
    def test_resolve_corpus_target_uses_config_version(self) -> None:
        runtime_config = config_lib.Config(
            rag=dataclasses.replace(
                config_lib.RAGConfig(),
                corpus_version="v9.9.9",
            )
        )

        corpus_root, version = build_corpus_manifest.resolve_corpus_target(runtime_config)

        self.assertEqual(version, "v9.9.9")
        self.assertEqual(corpus_root, Path("external_corpus") / "v9.9.9")

    def test_discover_corpus_targets_returns_sorted_version_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            (root / "v2.2.0_dynamic_history").mkdir()
            (root / "v2.0.0_foundation").mkdir()
            (root / "notes.txt").write_text("ignore", encoding="utf-8")

            discovered = build_corpus_manifest.discover_corpus_targets(root)

        self.assertEqual(
            discovered,
            (
                (Path(temporary_dir) / "v2.0.0_foundation", "v2.0.0_foundation"),
                (Path(temporary_dir) / "v2.2.0_dynamic_history", "v2.2.0_dynamic_history"),
            ),
        )

    def test_discover_corpus_targets_can_be_filtered_to_v3_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            (root / "v2.0.0_foundation").mkdir()
            (root / "v3.0.0_official_foundation").mkdir()
            (root / "v3.2.0_dynamic_history").mkdir()
            (root / "v3.3.0_official_full").mkdir()

            discovered = build_corpus_manifest.discover_active_governed_targets(root)

        self.assertEqual(
            discovered,
            (
                (Path(temporary_dir) / "v3.0.0_official_foundation", "v3.0.0_official_foundation"),
                (Path(temporary_dir) / "v3.3.0_official_full", "v3.3.0_official_full"),
            ),
        )

    def test_discover_corpus_targets_returns_empty_for_missing_root(self) -> None:
        discovered = build_corpus_manifest.discover_corpus_targets(Path("missing_external_corpus_root"))
        self.assertEqual(discovered, ())


if __name__ == "__main__":
    unittest.main()