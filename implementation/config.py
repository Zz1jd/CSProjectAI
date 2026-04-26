# Copyright 2023 DeepMind Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Configuration of a FunSearch experiment."""
from __future__ import annotations

import dataclasses
import os
from pathlib import Path
from typing import Type

from implementation import sampler
from implementation import evaluator


_DOTENV_FILE = Path(__file__).resolve().parents[1] / ".env"
_DOTENV_CACHE: dict[str, str] | None = None


def _load_dotenv_map(dotenv_file: Path = _DOTENV_FILE) -> dict[str, str]:
    """Load key/value pairs from a local .env file.

    Values from the process environment remain authoritative and are applied
    separately by `_read_env_str`.
    """

    if not dotenv_file.exists():
        return {}

    result: dict[str, str] = {}
    for raw_line in dotenv_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if value:
            result[key] = value
    return result


def _dotenv_values() -> dict[str, str]:
    global _DOTENV_CACHE
    if _DOTENV_CACHE is None:
        _DOTENV_CACHE = _load_dotenv_map()
    return _DOTENV_CACHE


@dataclasses.dataclass(frozen=True)
class ProgramsDatabaseConfig:
    """Configuration of a ProgramsDatabase.

    Attributes:
      functions_per_prompt: Number of previous programs to include in prompts.
      num_islands: Number of islands to maintain as a diversity mechanism.
      reset_period: How often (in seconds) the weakest islands should be reset.
      cluster_sampling_temperature_init: Initial temperature for softmax sampling
          of clusters within an island.
      cluster_sampling_temperature_period: Period of linear decay of the cluster
          sampling temperature.
    """

    functions_per_prompt: int = 2
    num_islands: int = 10
    reset_period: int = 4 * 60 * 60
    cluster_sampling_temperature_init: float = 0.1
    cluster_sampling_temperature_period: int = 30_000


@dataclasses.dataclass(frozen=True)
class RAGConfig:
    """Configuration for external knowledge retrieval."""

    enabled: bool = False
    corpus_root: str = "corpus/"
    chunk_size: int = 1200
    chunk_overlap: int = 200
    top_k: int = 3
    retrieval_mode: str = "vector"
    score_threshold: float = 0.0
    max_context_chars: int = 1200
    enable_diagnostics: bool = False
    use_intent_query: bool = False
    embedding_model: str = "BAAI/bge-large-zh-v1.5"
    embedding_base_url: str = "https://api.siliconflow.cn/v1"
    embedding_api_key: str | None = None


@dataclasses.dataclass(frozen=True)
class APIConfig:
    """Configuration for API-based LLM calls."""

    # base_url: str = "https://api.bltcy.ai/v1"
    base_url: str = "https://api.chatanywhere.com.cn/v1"
    api_key: str | None = None
    timeout_seconds: int = 60
    max_retries: int = 2


@dataclasses.dataclass(frozen=True)
class RuntimeDefaults:
    """Single-source runtime defaults for `main.py`."""

    dataset_path: str = "./cvrplib/setB"
    log_dir: str = "../logs/funsearch_llm_api"
    max_sample_nums: int = 100
    compare_max_sample_nums: int = 10


@dataclasses.dataclass(frozen=True)
class CompareReportConfig:
    """Single-source defaults for `scripts/compare_rag.py`."""

    results_dir: str = "results"
    baseline_log_path: str = ""
    rag_log_path: str = ""
    output_path: str = "results/RAG_vs_baseline_report.md"
    target_samples: int = dataclasses.field(
        default_factory=lambda: RuntimeDefaults().compare_max_sample_nums
    )


@dataclasses.dataclass(frozen=True)
class Config:
    """Configuration of a FunSearch experiment.

    Attributes:
      programs_database: Configuration of the evolutionary algorithm.
      num_samplers: Number of independent Samplers in the experiment. A value
          larger than 1 only has an effect when the samplers are able to execute
          in parallel, e.g. on different machines of a distributed system.
      num_evaluators: Number of independent program Evaluators in the experiment.
          A value larger than 1 is only expected to be useful when the Evaluators
          can execute in parallel as part of a distributed system.
      samples_per_prompt: How many independently sampled program continuations to
          obtain for each prompt.
    """

    programs_database: ProgramsDatabaseConfig = dataclasses.field(
        default_factory=ProgramsDatabaseConfig
    )
    num_samplers: int = 1  # RZ: I just use one samplers
    # num_evaluators: int = 140
    num_evaluators: int = 1  # RZ: I just use one evaluators
    samples_per_prompt: int = 4
    evaluate_timeout_seconds: int = 30  # RZ: add timeout seconds
    api: APIConfig = dataclasses.field(default_factory=APIConfig)
    rag: RAGConfig = dataclasses.field(default_factory=RAGConfig)
    random_seed: int | None = None
    llm_model: str = "gpt-3.5-turbo"
    model_track: str = "baseline"
    model_upgrade_name: str | None = None
    run_mode: str = "full"


def _read_env_str(name: str) -> str | None:
    value = os.environ.get(name)
    if value is not None:
        stripped = value.strip()
        return stripped or None

    dotenv_value = _dotenv_values().get(name)
    if dotenv_value is None:
        return None
    stripped = dotenv_value.strip()
    return stripped or None


def _read_env_int(name: str) -> int | None:
    value = _read_env_str(name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(
            f"Environment variable {name} must be an integer, got {value!r}."
        ) from exc


def apply_runtime_defaults_environment_overrides(
    runtime_defaults: RuntimeDefaults | None = None,
) -> RuntimeDefaults:
    """Returns runtime defaults after applying supported environment overrides."""

    resolved = runtime_defaults or RuntimeDefaults()
    dataset_path = _read_env_str("FUNSEARCH_DATASET_PATH")
    log_dir = _read_env_str("FUNSEARCH_LOG_DIR")
    max_sample_nums = _read_env_int("FUNSEARCH_MAX_SAMPLE_NUMS")
    compare_max_sample_nums = _read_env_int("FUNSEARCH_COMPARE_MAX_SAMPLE_NUMS")
    return dataclasses.replace(
        resolved,
        dataset_path=dataset_path or resolved.dataset_path,
        log_dir=log_dir or resolved.log_dir,
        max_sample_nums=(
            max_sample_nums if max_sample_nums is not None else resolved.max_sample_nums
        ),
        compare_max_sample_nums=(
            compare_max_sample_nums
            if compare_max_sample_nums is not None
            else resolved.compare_max_sample_nums
        ),
    )


def apply_environment_overrides(config_obj: Config | None = None) -> Config:
    """Returns the runtime config after applying supported environment overrides."""

    resolved = config_obj or Config()
    api_base_url = _read_env_str("FUNSEARCH_API_BASE_URL") or _read_env_str(
        "OPENAI_BASE_URL"
    )
    api_key = _read_env_str("FUNSEARCH_API_KEY") or _read_env_str("OPENAI_API_KEY")
    embedding_base_url = _read_env_str("FUNSEARCH_EMBEDDING_BASE_URL")
    embedding_api_key = _read_env_str("FUNSEARCH_EMBEDDING_API_KEY")
    llm_model = _read_env_str("FUNSEARCH_LLM_MODEL")
    run_mode = _read_env_str("FUNSEARCH_RUN_MODE")
    random_seed = _read_env_int("FUNSEARCH_RANDOM_SEED")

    api = dataclasses.replace(
        resolved.api,
        base_url=api_base_url or resolved.api.base_url,
        api_key=api_key or resolved.api.api_key,
    )
    rag = dataclasses.replace(
        resolved.rag,
        embedding_base_url=embedding_base_url or resolved.rag.embedding_base_url,
        embedding_api_key=embedding_api_key or resolved.rag.embedding_api_key,
    )
    return dataclasses.replace(
        resolved,
        api=api,
        rag=rag,
        llm_model=llm_model or resolved.llm_model,
        run_mode=run_mode or resolved.run_mode,
        random_seed=random_seed if random_seed is not None else resolved.random_seed,
    )


@dataclasses.dataclass()
class ClassConfig:
    """Implemented by RZ. Configuration of 'class LLM' and 'class SandBox' used in this implementation."""

    llm_class: Type[sampler.LLM]
    sandbox_class: Type[evaluator.Sandbox]
