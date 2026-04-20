#!/usr/bin/env python3
"""Audit legacy v2 corpus documents and emit a red-list report."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from implementation.corpus_governance import is_corpus_document_path
from implementation.corpus_governance import parse_front_matter


LEGACY_CORPUS_ROOT = Path("external_corpus")
LEGACY_VERSION_PREFIX = "v2."
OUTPUT_DIR = Path("results") / "corpus_audit"
JSON_REPORT_PATH = OUTPUT_DIR / "legacy_v2_audit.json"
MARKDOWN_REPORT_PATH = OUTPUT_DIR / "legacy_v2_audit.md"


def _iter_legacy_documents(corpus_root: Path) -> list[Path]:
    documents: list[Path] = []
    if not corpus_root.exists():
        return documents

    for version_dir in sorted(corpus_root.iterdir()):
        if not version_dir.is_dir() or not version_dir.name.startswith(LEGACY_VERSION_PREFIX):
            continue
        for file_path in sorted(version_dir.rglob("*")):
            if is_corpus_document_path(file_path):
                documents.append(file_path)
    return documents


def _classify_legacy_document(file_path: Path, corpus_root: Path) -> dict[str, Any]:
    metadata, _ = parse_front_matter(file_path.read_text(encoding="utf-8", errors="ignore"))
    reasons: list[str] = []

    if not metadata:
        reasons.append("missing_front_matter")

    license_value = metadata.get("license", "").strip()
    if license_value.lower() == "internal synthesis":
        reasons.append("internal_synthesis_license")

    url_value = metadata.get("url", "").strip()
    if not url_value and not metadata.get("source_paths", "").strip():
        reasons.append("missing_source_locator")

    distilled_from = metadata.get("distilled_from", "").strip().lower()
    if "corpus design.md" in distilled_from:
        reasons.append("design_doc_distillation")

    return {
        "relative_path": file_path.relative_to(corpus_root).as_posix(),
        "version": file_path.relative_to(corpus_root).parts[0],
        "license": license_value,
        "url": url_value,
        "source_type": metadata.get("source_type", "").strip(),
        "distilled_from": metadata.get("distilled_from", "").strip(),
        "reasons": reasons,
        "is_flagged": bool(reasons),
    }


def audit_legacy_corpus(corpus_root: Path = LEGACY_CORPUS_ROOT) -> dict[str, Any]:
    documents = [_classify_legacy_document(file_path, corpus_root) for file_path in _iter_legacy_documents(corpus_root)]
    flagged_documents = [document for document in documents if document["is_flagged"]]

    reason_counts: Counter[str] = Counter()
    for document in flagged_documents:
        for reason in document["reasons"]:
            reason_counts[reason] += 1

    return {
        "audit_version": "2026-04-20",
        "legacy_version_prefix": LEGACY_VERSION_PREFIX,
        "document_count": len(documents),
        "flagged_count": len(flagged_documents),
        "reason_counts": dict(sorted(reason_counts.items())),
        "documents": flagged_documents,
    }


def _build_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Legacy V2 Corpus Audit",
        "",
        f"- Legacy versions scanned: {report['legacy_version_prefix']}*",
        f"- Documents scanned: {report['document_count']}",
        f"- Flagged documents: {report['flagged_count']}",
        "",
        "## Reason Counts",
    ]

    reason_counts = report.get("reason_counts", {})
    if reason_counts:
        for reason, count in reason_counts.items():
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- none")

    lines.extend([
        "",
        "## Flagged Documents",
        "| Path | Reasons | License | Distilled From |",
        "| --- | --- | --- | --- |",
    ])

    for document in report.get("documents", []):
        reasons = ", ".join(document["reasons"]) if document["reasons"] else "none"
        distilled_from = str(document.get("distilled_from", "")).replace("|", "/")
        lines.append(
            "| "
            f"{document['relative_path']} | "
            f"{reasons} | "
            f"{document.get('license', '') or 'NA'} | "
            f"{distilled_from or 'NA'} |"
        )

    return "\n".join(lines) + "\n"


def write_audit_reports(
        report: dict[str, Any],
        output_dir: Path = OUTPUT_DIR,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / JSON_REPORT_PATH.name
    markdown_path = output_dir / MARKDOWN_REPORT_PATH.name
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_path.write_text(_build_markdown_report(report), encoding="utf-8")
    return json_path, markdown_path


def main() -> int:
    report = audit_legacy_corpus()
    json_path, markdown_path = write_audit_reports(report)
    print(f"Legacy audit JSON: {json_path.as_posix()}")
    print(f"Legacy audit Markdown: {markdown_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())