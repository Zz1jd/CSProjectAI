import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_legacy_corpus import audit_legacy_corpus
from scripts.audit_legacy_corpus import write_audit_reports


class LegacyCorpusAuditTests(unittest.TestCase):
    def test_audit_flags_internal_synthesis_missing_locator_and_design_doc_distillation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            corpus_root = Path(temporary_dir) / "external_corpus"
            legacy_root = corpus_root / "v2.0.0_foundation" / "theory"
            legacy_root.mkdir(parents=True)

            (legacy_root / "legacy_doc.md").write_text(
                "---\n"
                "title: Legacy Doc\n"
                "license: Internal synthesis\n"
                "summary: Invalid legacy doc.\n"
                "source_type: survey\n"
                "distilled_from: Corpus Design.md\n"
                "---\n\n"
                "Legacy content.\n",
                encoding="utf-8",
            )

            report = audit_legacy_corpus(corpus_root)

            self.assertEqual(report["document_count"], 1)
            self.assertEqual(report["flagged_count"], 1)
            self.assertEqual(report["reason_counts"]["internal_synthesis_license"], 1)
            self.assertEqual(report["reason_counts"]["missing_source_locator"], 1)
            self.assertEqual(report["reason_counts"]["design_doc_distillation"], 1)

    def test_write_audit_reports_emits_machine_redlist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            corpus_root = Path(temporary_dir) / "external_corpus"
            first_root = corpus_root / "v2.0.0_foundation" / "theory"
            second_root = corpus_root / "v2.2.0_dynamic_history" / "internal_history"
            first_root.mkdir(parents=True)
            second_root.mkdir(parents=True)

            for file_path in (
                first_root / "legacy_a.md",
                second_root / "legacy_b.md",
            ):
                file_path.write_text(
                    "---\n"
                    "title: Legacy Doc\n"
                    "license: Internal synthesis\n"
                    "summary: Invalid legacy doc.\n"
                    "source_type: survey\n"
                    "distilled_from: Corpus Design.md\n"
                    "---\n\n"
                    "Legacy content.\n",
                    encoding="utf-8",
                )

            report = audit_legacy_corpus(corpus_root)
            _, _, redlist_path = write_audit_reports(report, Path(temporary_dir) / "results")
            redlist = json.loads(redlist_path.read_text(encoding="utf-8"))

            self.assertEqual(redlist["blocked_versions"], ["v2.0.0_foundation", "v2.2.0_dynamic_history"])
            self.assertEqual(redlist["flagged_document_count"], 2)
            self.assertEqual(redlist["version_counts"]["v2.0.0_foundation"]["document_count"], 1)
            self.assertEqual(redlist["version_counts"]["v2.2.0_dynamic_history"]["flagged_count"], 1)
            self.assertEqual(
                sorted(redlist["flagged_paths"]),
                [
                    "v2.0.0_foundation/theory/legacy_a.md",
                    "v2.2.0_dynamic_history/internal_history/legacy_b.md",
                ],
            )
            self.assertEqual(redlist["by_version"]["v2.0.0_foundation"]["flagged_count"], 1)


if __name__ == "__main__":
    unittest.main()