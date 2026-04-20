import tempfile
import unittest
from pathlib import Path

from implementation.corpus_governance import build_dedup_report
from implementation.corpus_governance import build_manifest


class CorpusGovernanceTests(unittest.TestCase):
    # Reuse one helper for section-node fixtures so journal package tests stay data-driven.
    def _write_journal_section(
            self,
            corpus_root: Path,
            relative_path: str,
            source_type: str,
            section_ref: str,
            body: str,
            extra_metadata: dict[str, str] | None = None,
    ) -> None:
        metadata = {
            "title": "Adaptive CVRP Study",
            "paper_title": "Adaptive CVRP Study",
            "url": "https://example.test/paper/adaptive-cvrp-study",
            "doi": "10.1000/adaptive-cvrp-study",
            "date": "2024-05-01",
            "license": "Licensed access",
            "topics": "cvrp,heuristics",
            "summary": f"{source_type} node.",
            "source_type": source_type,
            "summary_level": "leaf",
            "journal": "European Journal of Operational Research",
            "paper_type": "research_article",
            "section_ref": section_ref,
        }
        metadata.update(extra_metadata or {})

        file_path = corpus_root / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        header = "".join(f"{key}: {value}\n" for key, value in metadata.items())
        file_path.write_text(f"---\n{header}---\n\n{body}\n", encoding="utf-8")

    def _write_governed_runtime_document(
            self,
            corpus_root: Path,
            relative_path: str,
            body: str,
            extra_metadata: dict[str, str] | None = None,
    ) -> None:
        metadata = {
            "title": "Priority Contract",
            "date": "2026-04-20",
            "license": "repository_source",
            "topics": "cvrp,api_contracts,priority",
            "summary": "Runtime contract summary.",
            "source_type": "runtime_contract",
            "summary_level": "summary",
            "source_scope": "repository",
            "source_paths": "specification.py",
            "source_anchor": "priority",
            "distilled_from": "specification.py",
        }
        metadata.update(extra_metadata or {})

        file_path = corpus_root / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        header = "".join(f"{key}: {value}\n" for key, value in metadata.items())
        file_path.write_text(f"---\n{header}---\n\n{body}\n", encoding="utf-8")

    def test_manifest_extracts_source_metadata_and_topics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            corpus_root = Path(temporary_dir) / "v2.0.0_foundation"
            (corpus_root / "capacity").mkdir(parents=True)

            (corpus_root / "capacity" / "cvrp_capacity.md").write_text(
                "---\n"
                "title: OR-Tools CVRP Guide\n"
                "url: https://developers.google.com/optimization/routing/cvrp\n"
                "date: 2025-01-15\n"
                "license: CC BY 4.0\n"
                "topics: capacity,feasibility\n"
                "summary: Capacity constraints in CVRP.\n"
                "---\n\n"
                "Use capacity dimensions to enforce load feasibility.\n",
                encoding="utf-8",
            )

            manifest = build_manifest(corpus_root=corpus_root, version="v2.0.0_foundation")
            self.assertEqual(manifest["version"], "v2.0.0_foundation")
            self.assertEqual(manifest["document_count"], 1)
            self.assertEqual(manifest["topic_distribution"]["capacity"], 1)
            self.assertEqual(manifest["topic_distribution"]["feasibility"], 1)
            entry = manifest["documents"][0]
            self.assertEqual(entry["title"], "OR-Tools CVRP Guide")
            self.assertEqual(entry["license"], "CC BY 4.0")
            self.assertIn("content_hash", entry)

    def test_manifest_extracts_extended_source_quality_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            corpus_root = Path(temporary_dir) / "v2.3.0_full_corpus"
            (corpus_root / "distance").mkdir(parents=True)

            (corpus_root / "distance" / "doc.md").write_text(
                "---\n"
                "title: Authority Doc\n"
                "url: https://example.test/doc\n"
                "date: 2026-04-18\n"
                "license: CC BY 4.0\n"
                "topics: distance,feasibility\n"
                "summary: Ranked source.\n"
                "source_type: documentation\n"
                "authority_score: 0.9\n"
                "algorithm_family: greedy,local_search\n"
                "complexity_class: O(n^2)\n"
                "applicability_tags: constructive,capacity_sensitive\n"
                "scenario_tags: dense_customers,mid_capacity\n"
                "evidence_level: reference\n"
                "summary_level: summary\n"
                "distilled_from: external_knowledge/local_search_moves.md\n"
                "anti_pattern: false\n"
                "---\n\n"
                "Distance-aware summary node.\n",
                encoding="utf-8",
            )

            manifest = build_manifest(corpus_root=corpus_root, version="v2.3.0_full_corpus")
            entry = manifest["documents"][0]

            self.assertEqual(entry["source_type"], "documentation")
            self.assertAlmostEqual(entry["authority_score"] or 0.0, 0.9, places=6)
            self.assertEqual(entry["algorithm_family"], ["greedy", "local_search"])
            self.assertEqual(entry["complexity_class"], "O(n^2)")
            self.assertEqual(entry["summary_level"], "summary")
            self.assertFalse(entry["anti_pattern"])

    def test_dedup_report_marks_exact_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            corpus_root = Path(temporary_dir) / "v2.1.0_solver_atoms"
            (corpus_root / "distance").mkdir(parents=True)

            shared_body = "Distance-aware nearest-customer priority with capacity checks.\n"
            header = (
                "---\n"
                "title: Source\n"
                "url: https://example.test/source\n"
                "date: 2025-02-01\n"
                "license: CC BY 4.0\n"
                "topics: distance\n"
                "summary: test\n"
                "---\n\n"
            )
            (corpus_root / "distance" / "doc_a.md").write_text(header + shared_body, encoding="utf-8")
            (corpus_root / "distance" / "doc_b.md").write_text(header + shared_body, encoding="utf-8")

            manifest = build_manifest(corpus_root=corpus_root, version="v2.1.0_solver_atoms")
            report = build_dedup_report(manifest["documents"], near_duplicate_threshold=0.9)

            self.assertEqual(report["exact_duplicate_count"], 1)
            duplicate_record = report["exact_duplicates"][0]
            self.assertIn("canonical", duplicate_record)
            self.assertIn("duplicate", duplicate_record)

    def test_manifest_extracts_journal_metadata_and_requires_complete_package(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            corpus_root = Path(temporary_dir) / "v3.0.0_official_foundation"

            self._write_journal_section(
                corpus_root,
                "journals/paper_01/abstract.md",
                "journal_abstract",
                "Abstract",
                "Abstract evidence for adaptive CVRP search.",
                extra_metadata={"summary_level": "summary"},
            )
            self._write_journal_section(
                corpus_root,
                "journals/paper_01/introduction.md",
                "journal_introduction",
                "1 Introduction",
                "Introduction evidence for adaptive CVRP search.",
            )
            self._write_journal_section(
                corpus_root,
                "journals/paper_01/methodology.md",
                "journal_methodology",
                "3 Methodology",
                "Methodology evidence for adaptive CVRP search.",
                extra_metadata={"algorithm_ref": "Algorithm 1"},
            )
            self._write_journal_section(
                corpus_root,
                "journals/paper_01/experiments.md",
                "journal_experiments",
                "4 Experiments",
                "Experiment evidence for adaptive CVRP search.",
                extra_metadata={
                    "benchmark_family": "cvrplib-x,uchoa",
                    "metrics": "distance,gap",
                    "baseline": "alns,hgs",
                    "table_ref": "Table 2",
                },
            )
            self._write_journal_section(
                corpus_root,
                "journals/paper_01/results.md",
                "journal_results",
                "5 Results",
                "Result evidence for adaptive CVRP search.",
                extra_metadata={
                    "benchmark_family": "cvrplib-x,uchoa",
                    "metrics": "distance,gap",
                    "baseline": "alns,hgs",
                    "figure_ref": "Figure 3",
                },
            )
            self._write_journal_section(
                corpus_root,
                "journals/paper_01/flow.md",
                "journal_flow_description",
                "3.2 Method Flow",
                "Flow description for adaptive CVRP search.",
                extra_metadata={"algorithm_ref": "Algorithm 1"},
            )

            manifest = build_manifest(corpus_root=corpus_root, version="v3.0.0_official_foundation")

            self.assertEqual(manifest["document_count"], 6)
            methodology_entry = next(
                entry for entry in manifest["documents"] if entry["source_type"] == "journal_methodology"
            )
            results_entry = next(
                entry for entry in manifest["documents"] if entry["source_type"] == "journal_results"
            )

            self.assertEqual(methodology_entry["journal_name"], "European Journal of Operational Research")
            self.assertEqual(methodology_entry["paper_title"], "Adaptive CVRP Study")
            self.assertEqual(methodology_entry["paper_year"], "2024")
            self.assertEqual(methodology_entry["section_ref"], "3 Methodology")
            self.assertEqual(methodology_entry["algorithm_ref"], "Algorithm 1")
            self.assertEqual(results_entry["benchmark_family"], ["cvrplib-x", "uchoa"])
            self.assertEqual(results_entry["metrics"], ["distance", "gap"])
            self.assertEqual(results_entry["baseline"], ["alns", "hgs"])
            self.assertTrue(results_entry["journal_paper_key"].startswith("doi:"))

    def test_manifest_rejects_journal_nodes_missing_required_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            corpus_root = Path(temporary_dir) / "v3.0.0_official_foundation"

            self._write_journal_section(
                corpus_root,
                "journals/paper_02/abstract.md",
                "journal_abstract",
                "Abstract",
                "Abstract evidence.",
                extra_metadata={"summary_level": "summary"},
            )
            self._write_journal_section(
                corpus_root,
                "journals/paper_02/introduction.md",
                "journal_introduction",
                "1 Introduction",
                "Introduction evidence.",
            )
            self._write_journal_section(
                corpus_root,
                "journals/paper_02/methodology.md",
                "journal_methodology",
                "3 Methodology",
                "Methodology evidence.",
            )
            self._write_journal_section(
                corpus_root,
                "journals/paper_02/experiments.md",
                "journal_experiments",
                "4 Experiments",
                "Experiment evidence.",
                extra_metadata={"benchmark_family": "cvrplib-x"},
            )
            self._write_journal_section(
                corpus_root,
                "journals/paper_02/results.md",
                "journal_results",
                "5 Results",
                "Result evidence.",
                extra_metadata={
                    "benchmark_family": "cvrplib-x",
                    "metrics": "distance",
                },
            )

            with self.assertRaisesRegex(ValueError, "metrics"):
                build_manifest(corpus_root=corpus_root, version="v3.0.0_official_foundation")

    def test_manifest_rejects_incomplete_journal_core_package(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            corpus_root = Path(temporary_dir) / "v3.0.0_official_foundation"

            self._write_journal_section(
                corpus_root,
                "journals/paper_03/abstract.md",
                "journal_abstract",
                "Abstract",
                "Abstract evidence.",
                extra_metadata={"summary_level": "summary"},
            )
            self._write_journal_section(
                corpus_root,
                "journals/paper_03/introduction.md",
                "journal_introduction",
                "1 Introduction",
                "Introduction evidence.",
            )
            self._write_journal_section(
                corpus_root,
                "journals/paper_03/methodology.md",
                "journal_methodology",
                "3 Methodology",
                "Methodology evidence.",
            )

            with self.assertRaisesRegex(ValueError, "journal_experiments"):
                build_manifest(corpus_root=corpus_root, version="v3.0.0_official_foundation")

    def test_manifest_accepts_v3_repository_source_document(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            workspace_root = Path(temporary_dir)
            (workspace_root / "specification.py").write_text("def priority():\n    return 0\n", encoding="utf-8")
            corpus_root = workspace_root / "v3.0.0_official_foundation"

            self._write_governed_runtime_document(
                corpus_root,
                "runtime_contracts/priority_function_contract.md",
                "The runtime expects a score vector aligned with node indices.",
            )

            manifest = build_manifest(corpus_root=corpus_root, version="v3.0.0_official_foundation")

            self.assertEqual(manifest["document_count"], 1)
            entry = manifest["documents"][0]
            self.assertEqual(entry["source_scope"], "repository")
            self.assertEqual(entry["source_paths"], ["specification.py"])
            self.assertEqual(entry["source_anchor"], "priority")

    def test_manifest_rejects_blocked_v3_license_and_design_doc_distillation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            workspace_root = Path(temporary_dir)
            (workspace_root / "specification.py").write_text("def priority():\n    return 0\n", encoding="utf-8")
            corpus_root = workspace_root / "v3.0.0_official_foundation"

            self._write_governed_runtime_document(
                corpus_root,
                "runtime_contracts/bad_contract.md",
                "Invalid governed document.",
                extra_metadata={
                    "license": "Internal synthesis",
                    "distilled_from": "Corpus Design.md",
                },
            )

            with self.assertRaisesRegex(ValueError, "blocked governed license value"):
                build_manifest(corpus_root=corpus_root, version="v3.0.0_official_foundation")


if __name__ == "__main__":
    unittest.main()
