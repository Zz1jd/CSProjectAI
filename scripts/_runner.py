#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import dataclasses
from datetime import datetime
from pathlib import Path
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import build_runtime_config
from main import run_experiment
from implementation import config as config_lib
from implementation import log_formatter


_UNSET = object()


class TeeWriter:
    def __init__(self, *streams) -> None:
        self._streams = streams

    def write(self, data: str) -> int:
        for stream in self._streams:
            stream.write(data)
        return len(data)

    def flush(self) -> None:
        for stream in self._streams:
            stream.flush()


def make_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def build_runtime_variant(
    *,
    enable_rag: bool,
    run_mode: str,
    base_config: config_lib.Config | None = None,
    random_seed: int | None | object = _UNSET,
    model_track: str | object = _UNSET,
    model_upgrade_name: str | None | object = _UNSET,
    rag_overrides: dict[str, Any] | None = None,
) -> config_lib.Config:
    resolved_base = base_config or build_runtime_config()
    resolved_rag_overrides = dict(rag_overrides or {})
    rag_config = dataclasses.replace(
        resolved_base.rag,
        enabled=enable_rag,
        **resolved_rag_overrides,
    )

    config_updates: dict[str, Any] = {
        "run_mode": run_mode,
        "rag": rag_config,
    }
    if random_seed is not _UNSET:
        config_updates["random_seed"] = random_seed
    if model_track is not _UNSET:
        config_updates["model_track"] = model_track
    if model_upgrade_name is not _UNSET:
        config_updates["model_upgrade_name"] = model_upgrade_name
    return dataclasses.replace(resolved_base, **config_updates)


def run_logged_experiment(
    *,
    label: str,
    runtime_config: config_lib.Config,
    log_path: Path,
    dataset_path: str,
    max_sample_nums: int,
    log_dir: str,
    header_fields: dict[str, Any] | None = None,
) -> None:
    print(
        f"[{label}] start | mode={runtime_config.run_mode} | "
        f"seed={runtime_config.random_seed} | budget={max_sample_nums} | rag={runtime_config.rag.enabled}"
    )
    with log_path.open("w", encoding="utf-8") as log_file:
        tee_stdout = TeeWriter(sys.__stdout__, log_file)
        tee_stderr = TeeWriter(sys.__stderr__, log_file)
        with contextlib.redirect_stdout(tee_stdout), contextlib.redirect_stderr(tee_stderr):
            print(log_formatter.format_main_header("EXPERIMENT START"))
            print(f"RUN_LABEL: {label}")
            for key, value in (header_fields or {}).items():
                print(f"{key}: {value}")
            print(log_formatter.format_divider())
            run_experiment(
                runtime_config=runtime_config,
                dataset_path=dataset_path,
                max_sample_nums=max_sample_nums,
                log_dir=log_dir,
            )
            print(log_formatter.format_main_header("EXPERIMENT END"))
    print(f"[{label}] complete | log={log_path.as_posix()}")
