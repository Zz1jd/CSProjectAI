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


def main() -> int:
    corpus_targets = tuple(
        (corpus_root, corpus_version)
        for corpus_root, corpus_version in discover_corpus_targets()
        if corpus_version.startswith("v3.")
    )
    if not corpus_targets:
        raise ValueError("No v3 corpus directories found under external_corpus/.")

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
