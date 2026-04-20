import tempfile
import unittest
from pathlib import Path

from scripts.audit_legacy_corpus import audit_legacy_corpus


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


if __name__ == "__main__":
    unittest.main()