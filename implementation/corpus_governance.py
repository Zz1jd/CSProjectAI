from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import datetime, UTC
from pathlib import Path
from typing import Any


_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")
SUPPORTED_CORPUS_SUFFIXES = frozenset({".md", ".markdown", ".txt", ".rst"})
IGNORED_CORPUS_FILENAMES = frozenset({"manifest.json", "dedup_report.json"})
_JOURNAL_SOURCE_TYPES = {
    "journal_abstract",
    "journal_introduction",
    "journal_methodology",
    "journal_experiments",
    "journal_results",
    "journal_flow_description",
    "journal_pseudocode",
}
_JOURNAL_CORE_SOURCE_TYPES = {
    "journal_abstract",
    "journal_introduction",
    "journal_methodology",
    "journal_experiments",
    "journal_results",
}
_JOURNAL_EVIDENCE_SOURCE_TYPES = {"journal_experiments", "journal_results"}
_GOVERNED_VERSION_PREFIX = "v3."
_BLOCKED_LICENSE_VALUES = {"internal synthesis"}
_BLOCKED_DISTILLED_FROM_REFERENCES = ("corpus design.md",)


def _parse_csv(value: str) -> list[str]:
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def _parse_csv_preserve_case(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_optional_float(value: str) -> float | None:
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return float(stripped)
    except ValueError:
        return None


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}


def _parse_optional_year(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        return ""

    match = re.search(r"\b(?:19|20)\d{2}\b", stripped)
    return match.group(0) if match else ""


def _parse_first_present(metadata: dict[str, str], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = metadata.get(key, "").strip()
        if value:
            return value
    return ""


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text.strip()

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break

    if end_index is None:
        return {}, text.strip()

    metadata: dict[str, str] = {}
    for line in lines[1:end_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip().lower()] = value.strip()

    body = "\n".join(lines[end_index + 1:]).strip()
    return metadata, body


def is_corpus_document_path(file_path: Path) -> bool:
    # Reuse the same filter in manifest building and legacy audits.
    return (
        file_path.is_file()
        and file_path.name not in IGNORED_CORPUS_FILENAMES
        and file_path.suffix.lower() in SUPPORTED_CORPUS_SUFFIXES
    )


def normalize_source_metadata(metadata: dict[str, str]) -> dict[str, Any]:
    topics = _parse_csv(metadata.get("topics", ""))
    applicability_tags = _parse_csv(metadata.get("applicability_tags", ""))
    scenario_tags = _parse_csv(metadata.get("scenario_tags", ""))
    algorithm_family = _parse_csv(metadata.get("algorithm_family", ""))
    authority_score = _parse_optional_float(metadata.get("authority_score", ""))
    journal_name = _parse_first_present(metadata, ("journal", "venue", "journal_name"))
    paper_year = _parse_optional_year(
        _parse_first_present(metadata, ("paper_year", "year", "date"))
    )
    benchmark_family = _parse_csv(metadata.get("benchmark_family", ""))
    metrics = _parse_csv(metadata.get("metrics", ""))
    baseline = _parse_csv(metadata.get("baseline", ""))
    source_paths = _parse_csv_preserve_case(metadata.get("source_paths", ""))

    return {
        "title": metadata.get("title", ""),
        "url": metadata.get("url", ""),
        "date": metadata.get("date", ""),
        "license": metadata.get("license", ""),
        "summary": metadata.get("summary", ""),
        "topics": topics,
        "source_type": metadata.get("source_type", ""),
        "authority_score": authority_score,
        "algorithm_family": algorithm_family,
        "complexity_class": metadata.get("complexity_class", ""),
        "applicability_tags": applicability_tags,
        "scenario_tags": scenario_tags,
        "evidence_level": metadata.get("evidence_level", ""),
        "summary_level": metadata.get("summary_level", "leaf"),
        "distilled_from": metadata.get("distilled_from", ""),
        "anti_pattern": _parse_bool(metadata.get("anti_pattern", "false")),
        "source_id": metadata.get("source_id", ""),
        "source_scope": metadata.get("source_scope", ""),
        "source_paths": source_paths,
        "source_anchor": metadata.get("source_anchor", ""),
        "paper_title": metadata.get("paper_title", "") or metadata.get("title", ""),
        "journal_name": journal_name,
        "paper_year": paper_year,
        "doi": metadata.get("doi", ""),
        "paper_type": metadata.get("paper_type", ""),
        "section_ref": metadata.get("section_ref", ""),
        "figure_ref": metadata.get("figure_ref", ""),
        "table_ref": metadata.get("table_ref", ""),
        "algorithm_ref": metadata.get("algorithm_ref", ""),
        "benchmark_family": benchmark_family,
        "metrics": metrics,
        "baseline": baseline,
    }


def _is_journal_source_type(source_type: str) -> bool:
    return source_type.strip().lower() in _JOURNAL_SOURCE_TYPES


def _is_governed_version(version: str) -> bool:
    return version.strip().lower().startswith(_GOVERNED_VERSION_PREFIX)


def _resolve_validation_root(corpus_root: Path) -> Path:
    if corpus_root.parent.name == "external_corpus":
        return corpus_root.parent.parent
    return corpus_root.parent


def _contains_blocked_distillation_source(distilled_from: str) -> bool:
    lowered = distilled_from.strip().lower()
    return any(reference in lowered for reference in _BLOCKED_DISTILLED_FROM_REFERENCES)


def _validate_repository_source_paths(
        file_path: Path,
        source_paths: list[str],
        validation_root: Path,
) -> None:
    invalid_paths: list[str] = []
    resolved_root = validation_root.resolve()

    for source_path in source_paths:
        candidate = Path(source_path)
        if candidate.is_absolute():
            invalid_paths.append(source_path)
            continue

        resolved_candidate = (validation_root / candidate).resolve()
        try:
            resolved_candidate.relative_to(resolved_root)
        except ValueError:
            invalid_paths.append(source_path)
            continue

        if not resolved_candidate.exists():
            invalid_paths.append(source_path)

    if invalid_paths:
        raise ValueError(
            f"{file_path.as_posix()} references missing repository sources: {', '.join(invalid_paths)}"
        )


def _validate_governed_document(
        file_path: Path,
        metadata: dict[str, str],
        normalized_metadata: dict[str, Any],
        version: str,
        validation_root: Path,
) -> None:
    if not _is_governed_version(version):
        return

    missing_fields: list[str] = []
    has_url = bool(str(normalized_metadata.get("url", "")).strip())
    source_paths = list(normalized_metadata.get("source_paths", []))
    source_scope = str(normalized_metadata.get("source_scope", "")).strip().lower()

    if not metadata.get("summary", "").strip():
        missing_fields.append("summary")
    if not metadata.get("source_type", "").strip():
        missing_fields.append("source_type")
    if not metadata.get("summary_level", "").strip():
        missing_fields.append("summary_level")
    if not metadata.get("license", "").strip():
        missing_fields.append("license")
    if not has_url and not source_paths:
        missing_fields.append("url|source_paths")
    if source_paths and not source_scope:
        missing_fields.append("source_scope")
    if source_scope == "repository" and not source_paths:
        missing_fields.append("source_paths")
    if source_scope == "repository" and not str(normalized_metadata.get("source_anchor", "")).strip():
        missing_fields.append("source_anchor")

    if missing_fields:
        raise ValueError(
            f"{file_path.as_posix()} is missing required governed metadata: {', '.join(missing_fields)}"
        )

    license_value = str(normalized_metadata.get("license", "")).strip().lower()
    if license_value in _BLOCKED_LICENSE_VALUES:
        raise ValueError(
            f"{file_path.as_posix()} uses blocked governed license value: {normalized_metadata['license']}"
        )

    distilled_from = str(normalized_metadata.get("distilled_from", ""))
    if _contains_blocked_distillation_source(distilled_from):
        raise ValueError(
            f"{file_path.as_posix()} references blocked planning sources in distilled_from."
        )

    if source_scope == "repository":
        _validate_repository_source_paths(file_path, source_paths, validation_root)


# Centralize journal identity rules so per-file and package validation share one source of truth.
def _build_journal_paper_key(metadata: dict[str, Any]) -> str:
    doi = str(metadata.get("doi", "")).strip().lower()
    if doi:
        return f"doi:{doi}"

    url = str(metadata.get("url", "")).strip().lower()
    if url:
        return f"url:{url}"

    paper_title = str(metadata.get("paper_title", "")).strip().lower()
    journal_name = str(metadata.get("journal_name", "")).strip().lower()
    paper_year = str(metadata.get("paper_year", "")).strip().lower()
    fallback_parts = [part for part in (paper_title, journal_name, paper_year) if part]
    return "paper:" + "|".join(fallback_parts) if fallback_parts else ""


def _validate_journal_document(
        file_path: Path,
        metadata: dict[str, str],
        normalized_metadata: dict[str, Any],
) -> None:
    source_type = str(normalized_metadata.get("source_type", "")).strip().lower()
    if source_type not in _JOURNAL_SOURCE_TYPES:
        return

    missing_fields: list[str] = []
    if not metadata.get("summary_level", "").strip():
        missing_fields.append("summary_level")
    if not str(normalized_metadata.get("section_ref", "")).strip():
        missing_fields.append("section_ref")
    if not str(normalized_metadata.get("journal_name", "")).strip():
        missing_fields.append("journal")
    if not str(normalized_metadata.get("paper_type", "")).strip():
        missing_fields.append("paper_type")
    if not (
            metadata.get("doi", "").strip()
            or str(normalized_metadata.get("url", "")).strip()
            or metadata.get("paper_title", "").strip()
    ):
        missing_fields.append("doi|url|paper_title")
    if source_type in _JOURNAL_EVIDENCE_SOURCE_TYPES:
        if not normalized_metadata.get("benchmark_family"):
            missing_fields.append("benchmark_family")
        if not normalized_metadata.get("metrics"):
            missing_fields.append("metrics")

    if missing_fields:
        missing_summary = ", ".join(missing_fields)
        raise ValueError(
            f"{file_path.as_posix()} is missing required journal metadata: {missing_summary}"
        )


def _validate_journal_section_packages(documents: list[dict[str, Any]]) -> None:
    grouped_source_types: dict[str, set[str]] = {}
    grouped_labels: dict[str, str] = {}
    for document in documents:
        source_type = str(document.get("source_type", "")).strip().lower()
        if source_type not in _JOURNAL_SOURCE_TYPES:
            continue

        paper_key = str(document.get("journal_paper_key", "")).strip()
        if not paper_key:
            raise ValueError(
                f"{document['relative_path']} is missing a stable journal paper identity."
            )

        grouped_source_types.setdefault(paper_key, set()).add(source_type)
        grouped_labels.setdefault(
            paper_key,
            str(document.get("paper_title") or document.get("title") or paper_key),
        )

    package_errors: list[str] = []
    for paper_key, source_types in sorted(grouped_source_types.items()):
        missing_core_types = sorted(_JOURNAL_CORE_SOURCE_TYPES - source_types)
        if missing_core_types:
            package_errors.append(
                f"{grouped_labels[paper_key]} missing core journal nodes: "
                f"{', '.join(missing_core_types)}"
            )

    if package_errors:
        raise ValueError(
            "Journal section package validation failed: " + "; ".join(package_errors)
        )


def build_manifest(corpus_root: Path, version: str) -> dict[str, Any]:
    documents = _collect_documents(corpus_root, version)

    topic_distribution: Counter[str] = Counter()
    for document in documents:
        for topic in document["topics"]:
            topic_distribution[topic] += 1

    manifest = {
        "version": version,
        "built_at_utc": datetime.now(UTC).isoformat(),
        "document_count": len(documents),
        "topic_distribution": dict(sorted(topic_distribution.items())),
        "documents": documents,
    }
    return manifest


def build_dedup_report(
        documents: list[dict[str, Any]],
        near_duplicate_threshold: float = 0.92,
) -> dict[str, Any]:
    grouped_by_hash: dict[str, list[dict[str, Any]]] = {}
    for document in documents:
        grouped_by_hash.setdefault(document["content_hash"], []).append(document)

    exact_duplicates: list[dict[str, str]] = []
    canonical_map: dict[str, str] = {}
    for group in grouped_by_hash.values():
        if len(group) <= 1:
            continue

        sorted_group = sorted(group, key=lambda item: item["relative_path"])
        canonical = sorted_group[0]["relative_path"]
        for duplicate in sorted_group[1:]:
            duplicate_path = duplicate["relative_path"]
            exact_duplicates.append({"canonical": canonical, "duplicate": duplicate_path})
            canonical_map[duplicate_path] = canonical

    near_duplicates: list[dict[str, Any]] = []
    for left_index in range(len(documents)):
        left_document = documents[left_index]
        left_tokens = set(_tokenize(left_document.get("_normalized_text", "")))
        if not left_tokens:
            continue

        for right_index in range(left_index + 1, len(documents)):
            right_document = documents[right_index]
            if left_document["content_hash"] == right_document["content_hash"]:
                continue

            right_tokens = set(_tokenize(right_document.get("_normalized_text", "")))
            if not right_tokens:
                continue

            similarity = _jaccard_similarity(left_tokens, right_tokens)
            if similarity >= near_duplicate_threshold:
                near_duplicates.append({
                    "left": left_document["relative_path"],
                    "right": right_document["relative_path"],
                    "similarity": round(similarity, 6),
                })

    return {
        "near_duplicate_threshold": near_duplicate_threshold,
        "exact_duplicate_count": len(exact_duplicates),
        "exact_duplicates": exact_duplicates,
        "canonical_map": canonical_map,
        "near_duplicate_count": len(near_duplicates),
        "near_duplicates": near_duplicates,
    }


def write_corpus_artifacts(corpus_root: Path, version: str) -> tuple[Path, Path]:
    manifest = build_manifest(corpus_root=corpus_root, version=version)
    dedup_report = build_dedup_report(manifest["documents"])

    # Keep normalized text only for in-memory dedup; do not persist heavy internals.
    for document in manifest["documents"]:
        document.pop("_normalized_text", None)

    manifest_path = corpus_root / "manifest.json"
    dedup_path = corpus_root / "dedup_report.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    dedup_path.write_text(json.dumps(dedup_report, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path, dedup_path


def _collect_documents(corpus_root: Path, version: str) -> list[dict[str, Any]]:
    if not corpus_root.exists():
        return []

    documents: list[dict[str, Any]] = []
    validation_root = _resolve_validation_root(corpus_root)
    for file_path in sorted(corpus_root.rglob("*")):
        if not is_corpus_document_path(file_path):
            continue

        raw_text = file_path.read_text(encoding="utf-8", errors="ignore")
        metadata, body = parse_front_matter(raw_text)
        if not metadata:
            continue
        normalized_text = _normalize_text(body)

        normalized_metadata = normalize_source_metadata(metadata)
        _validate_governed_document(file_path, metadata, normalized_metadata, version, validation_root)
        _validate_journal_document(file_path, metadata, normalized_metadata)
        source_type = str(normalized_metadata.get("source_type", ""))
        journal_paper_key = (
            _build_journal_paper_key(normalized_metadata)
            if _is_journal_source_type(source_type)
            else ""
        )
        topics = normalized_metadata["topics"]
        document = {
            "relative_path": file_path.relative_to(corpus_root).as_posix(),
            "title": normalized_metadata["title"] or file_path.stem,
            "url": normalized_metadata["url"],
            "date": normalized_metadata["date"],
            "license": normalized_metadata["license"],
            "topics": topics,
            "summary": normalized_metadata["summary"],
            "source_type": normalized_metadata["source_type"],
            "source_id": normalized_metadata["source_id"],
            "source_scope": normalized_metadata["source_scope"],
            "source_paths": normalized_metadata["source_paths"],
            "source_anchor": normalized_metadata["source_anchor"],
            "authority_score": normalized_metadata["authority_score"],
            "algorithm_family": normalized_metadata["algorithm_family"],
            "complexity_class": normalized_metadata["complexity_class"],
            "applicability_tags": normalized_metadata["applicability_tags"],
            "scenario_tags": normalized_metadata["scenario_tags"],
            "evidence_level": normalized_metadata["evidence_level"],
            "summary_level": normalized_metadata["summary_level"],
            "distilled_from": normalized_metadata["distilled_from"],
            "anti_pattern": normalized_metadata["anti_pattern"],
            "paper_title": normalized_metadata["paper_title"],
            "journal_name": normalized_metadata["journal_name"],
            "paper_year": normalized_metadata["paper_year"],
            "doi": normalized_metadata["doi"],
            "paper_type": normalized_metadata["paper_type"],
            "section_ref": normalized_metadata["section_ref"],
            "figure_ref": normalized_metadata["figure_ref"],
            "table_ref": normalized_metadata["table_ref"],
            "algorithm_ref": normalized_metadata["algorithm_ref"],
            "benchmark_family": normalized_metadata["benchmark_family"],
            "metrics": normalized_metadata["metrics"],
            "baseline": normalized_metadata["baseline"],
            "journal_paper_key": journal_paper_key,
            "content_hash": _sha256(normalized_text),
            "char_count": len(body),
            "token_count": len(_tokenize(normalized_text)),
            "_normalized_text": normalized_text,
        }
        documents.append(document)

    _validate_journal_section_packages(documents)
    return documents


def _normalize_text(text: str) -> str:
    return " ".join(_tokenize(text))


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_PATTERN.findall(text)]


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _jaccard_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)
