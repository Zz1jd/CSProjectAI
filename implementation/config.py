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
from typing import Type

from implementation import sampler
from implementation import evaluator


_AUTO_CORPUS_ROOTS_SENTINEL: tuple[str, ...] = ("__AUTO_CORPUS_ROOTS__",)


def build_governed_corpus_root(corpus_version: str) -> str:
    """Build the governed corpus root path from a version string."""

    return f"external_corpus/{corpus_version}"


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
    # Single-source active governed corpus version shared by runtime and build scripts.
    corpus_version: str = "v3.0.0_official_foundation"
    corpus_roots: tuple[str, ...] = _AUTO_CORPUS_ROOTS_SENTINEL
    chunk_size: int = 1200
    chunk_overlap: int = 200
    top_k: int = 3
    retrieval_mode: str = "vector"
    score_threshold: float = 0.0
    max_context_chars: int = 1200
    enable_diagnostics: bool = False
    use_intent_query: bool = True
    embedding_model: str = "BAAI/bge-large-zh-v1.5"
    embedding_base_url: str = "https://api.siliconflow.cn/v1"
    embedding_api_key: str | None = "sk-jwbxcbszdqdinhqofxikohzyjisdvwnkljbrzkfqufuxcbyy"

    def __post_init__(self) -> None:
        if self.corpus_roots == _AUTO_CORPUS_ROOTS_SENTINEL:
            object.__setattr__(
                self,
                "corpus_roots",
                (build_governed_corpus_root(self.corpus_version),),
            )


def default_governed_corpus_roots() -> tuple[str, ...]:
    """Return single-source governed corpus roots for round presets."""

    return RAGConfig().corpus_roots


@dataclasses.dataclass(frozen=True)
class APIConfig:
    """Configuration for API-based LLM calls."""

    base_url: str = "https://api.chatanywhere.com.cn/v1"
    api_key: str | None = "sk-vWpzPgcJaoamJOr998VvL5H4Z2uTt6jNmPk0SftpmCQJYZ5C"
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
class CompareScriptConfig:
    """Single-source defaults for `scripts/run_compare_once.py`."""

    results_dir: str = "results"
    log_dir: str = "../logs/funsearch_compare"


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
class HistoricalReportConfig:
    """Single-source defaults for `scripts/summarize_rag_run.py`."""

    results_dir: str = "results"
    run_log_path: str = ""
    run_log_glob: str = "funsearch_rag_run_*.log"
    historical_log_path: str = "results/mjwade_results_from_funsearch_cvrp_hjr.txt"
    output_path: str = "results/RAG_vs_historical_report.md"
    target_samples: int = dataclasses.field(
        default_factory=lambda: RuntimeDefaults().max_sample_nums
    )


@dataclasses.dataclass(frozen=True)
class MultiRoundPreset:
    """Single-source round definition for multi-seed orchestration."""

    name: str
    corpus_roots: tuple[str, ...]
    retrieval_mode: str
    retrieval_score_threshold: float
    retrieval_intent_query: bool
    retrieval_diagnostics: bool
    model_track: str = "baseline"
    model_upgrade_name: str | None = None


def _default_multi_round_presets() -> tuple[MultiRoundPreset, ...]:
    """Build multi-round presets without duplicating governed corpus root strings."""

    governed_corpus_roots = default_governed_corpus_roots()
    return (
        MultiRoundPreset(
            name="round1",
            corpus_roots=("external_knowledge",),
            retrieval_mode="vector",
            retrieval_score_threshold=0.0,
            retrieval_intent_query=False,
            retrieval_diagnostics=False,
        ),
        MultiRoundPreset(
            name="round2",
            corpus_roots=governed_corpus_roots,
            retrieval_mode="vector",
            retrieval_score_threshold=0.05,
            retrieval_intent_query=True,
            retrieval_diagnostics=True,
        ),
        MultiRoundPreset(
            name="round3",
            corpus_roots=governed_corpus_roots,
            retrieval_mode="hybrid",
            retrieval_score_threshold=0.05,
            retrieval_intent_query=True,
            retrieval_diagnostics=True,
            model_track="upgrade",
            model_upgrade_name=None,
        ),
    )


@dataclasses.dataclass(frozen=True)
class MultiRoundScriptConfig:
    """Single-source defaults for `scripts/run_multi_seed_compare.py`."""

    seeds: tuple[int, ...] = (41, 42, 43)
    results_dir: str = "results"
    log_dir: str = "../logs/funsearch_multi_round"
    rounds: tuple[MultiRoundPreset, ...] = dataclasses.field(default_factory=_default_multi_round_presets)


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
    programs_database: ProgramsDatabaseConfig = dataclasses.field(default_factory=ProgramsDatabaseConfig)
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


@dataclasses.dataclass()
class ClassConfig:
    """Implemented by RZ. Configuration of 'class LLM' and 'class SandBox' used in this implementation.
    """
    llm_class: Type[sampler.LLM]
    sandbox_class: Type[evaluator.Sandbox]
