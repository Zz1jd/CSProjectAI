import tempfile
import unittest
from pathlib import Path

from implementation import config as config_lib
from scripts.summarize_rag_run import _resolve_run_log_path


class SummarizeRagRunTests(unittest.TestCase):
    def test_resolve_run_log_path_prefers_explicit_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            explicit = root / "manual.log"
            explicit.write_text("x", encoding="utf-8")
            report_config = config_lib.HistoricalReportConfig(
                results_dir=str(root),
                run_log_path=str(explicit),
            )

            self.assertEqual(_resolve_run_log_path(report_config), explicit)

    def test_resolve_run_log_path_falls_back_to_latest_match(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            older = root / "funsearch_rag_run_20260101_000000.log"
            newer = root / "funsearch_rag_run_20260102_000000.log"
            older.write_text("old", encoding="utf-8")
            newer.write_text("new", encoding="utf-8")

            report_config = config_lib.HistoricalReportConfig(
                results_dir=str(root),
                run_log_path="",
                run_log_glob="funsearch_rag_run_*.log",
            )

            self.assertEqual(_resolve_run_log_path(report_config), newer)


if __name__ == "__main__":
    unittest.main()
