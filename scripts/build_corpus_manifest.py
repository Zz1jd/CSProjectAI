#!/usr/bin/env python3
"""Build corpus manifest and dedup report for the governed CVRP corpus."""

from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from implementation import config as config_lib
from implementation.corpus_governance import write_corpus_artifacts


ACTIVE_GOVERNED_VERSIONS = (
    "v3.0.0_official_foundation",
    "v3.1.0_official_solver_atoms",
    "v3.2.0_official_plus_history",
    "v3.3.0_official_full",
)


def resolve_corpus_target(runtime_config: config_lib.Config | None = None) -> tuple[Path, str]:
    """Resolve corpus target from single-source config to avoid duplicated script constants."""
    config_obj = runtime_config or config_lib.Config()
    version = config_obj.rag.corpus_version
    return Path("external_corpus") / version, version


def discover_corpus_targets(corpus_root: Path | None = None) -> tuple[tuple[Path, str], ...]:
    resolved_root = corpus_root or Path("external_corpus")
    if not resolved_root.exists():
        return ()

    targets: list[tuple[Path, str]] = []
    for child in sorted(resolved_root.iterdir()):
        if child.is_dir():
            targets.append((child, child.name))
    return tuple(targets)


def discover_active_governed_targets(corpus_root: Path | None = None) -> tuple[tuple[Path, str], ...]:
    """Return only the governed corpus versions that are active in the phased v3 family."""
    discovered = discover_corpus_targets(corpus_root)
    return tuple(
        (resolved_root, version)
        for resolved_root, version in discovered
        if version in ACTIVE_GOVERNED_VERSIONS
    )


def main() -> int:
    corpus_targets = discover_active_governed_targets()
    if not corpus_targets:
        raise ValueError("No active v3 corpus directories found under external_corpus/.")

    for corpus_root, corpus_version in corpus_targets:
        manifest_path, dedup_path = write_corpus_artifacts(
            corpus_root=corpus_root,
            version=corpus_version,
        )
        print(f"Manifest written: {manifest_path.as_posix()}")
        print(f"Dedup report written: {dedup_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
