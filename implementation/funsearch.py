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

"""A single-threaded implementation of the FunSearch pipeline."""
from __future__ import annotations

# from collections.abc import Sequence

# RZ: there are multiple errors in the original code
# we should use typing.xxx rather than collections.abc.xxx
from typing import Any, Tuple, Sequence
import json
import random

import numpy as np

from implementation import code_manipulation
from implementation import config as config_lib
from implementation import evaluator
from implementation import programs_database
from implementation import retrieval
from implementation import sampler
from implementation import log_formatter


def _extract_function_names(specification: str) -> Tuple[str, str]:
    """Returns the name of the function to evolve and of the function to run.

    RZ: The so-called specification refers to the boilerplate code template for a task.
    The template MUST have two important functions decorated with '@funsearch.run', '@funsearch.evolve' respectively.
    The function labeled with '@funsearch.run' is going to evaluate the generated code (like fitness evaluation).
    The function labeled with '@funsearch.evolve' is the function to be searched (like 'greedy' in cap-set).
    This function (_extract_function_names) makes sure that these decorators appears in the specification.
    """
    run_functions = list(code_manipulation.yield_decorated(specification, 'funsearch', 'run'))
    if len(run_functions) != 1:
        raise ValueError('Expected 1 function decorated with `@funsearch.run`.')
    evolve_functions = list(code_manipulation.yield_decorated(specification, 'funsearch', 'evolve'))
    if len(evolve_functions) != 1:
        raise ValueError('Expected 1 function decorated with `@funsearch.evolve`.')
    return evolve_functions[0], run_functions[0]


def build_run_metadata(
        config_obj: config_lib.Config,
        dataset_path: str,
        max_sample_nums: int | None,
) -> dict[str, Any]:
    return {
        "seed": config_obj.random_seed,
        "llm_model": config_obj.llm_model,
        "model_track": config_obj.model_track,
        "model_upgrade_name": config_obj.model_upgrade_name,
        "run_mode": config_obj.run_mode,
        "dataset_path": dataset_path,
        "max_sample_nums": max_sample_nums,
        "effective_max_sample_nums": max_sample_nums,
        "samples_per_prompt": config_obj.samples_per_prompt,
        "evaluate_timeout_seconds": config_obj.evaluate_timeout_seconds,
        "num_samplers": config_obj.num_samplers,
        "num_evaluators": config_obj.num_evaluators,
        "api_base_url_explicit": bool(config_obj.api.base_url),
        "api_key_explicit": bool(config_obj.api.api_key),
        "api_timeout_seconds": config_obj.api.timeout_seconds,
        "api_max_retries": config_obj.api.max_retries,
        "rag_enabled": config_obj.rag.enabled,
        "rag_corpus_root": config_obj.rag.corpus_root,
        "rag_chunk_size": config_obj.rag.chunk_size,
        "rag_chunk_overlap": config_obj.rag.chunk_overlap,
        "rag_top_k": config_obj.rag.top_k,
        "rag_retrieval_mode": config_obj.rag.retrieval_mode,
        "rag_score_threshold": config_obj.rag.score_threshold,
        "rag_max_context_chars": config_obj.rag.max_context_chars,
        "rag_diagnostics_enabled": config_obj.rag.enable_diagnostics,
        "rag_use_intent_query": config_obj.rag.use_intent_query,
        "rag_embedding_model": config_obj.rag.embedding_model,
        "rag_embedding_base_url_explicit": bool(config_obj.rag.embedding_base_url),
        "rag_embedding_api_key_explicit": bool(config_obj.rag.embedding_api_key),
    }


def main(
        specification: str,
        inputs: Sequence[Any],
        config: config_lib.Config,
        max_sample_nums: int | None,
        class_config: config_lib.ClassConfig,
        **kwargs
):
    """Launches a FunSearch experiment.
    RZ:
    Args:
        specification: the boilerplate code for the problem.
        inputs       : the data instances for the current problem.
        config       : config file.
        max_sample_nums: the maximum samples nums from LLM. 'None' refers to no stop.
    """
    if config.random_seed is not None:
        random.seed(config.random_seed)
        np.random.seed(config.random_seed)

    # Reset shared class-level sampler counter for each run to avoid cross-run leakage.
    sampler.Sampler._global_samples_nums = 0

    run_metadata = build_run_metadata(
        config_obj=config,
        dataset_path=kwargs.get('dataset_path', ''),
        max_sample_nums=max_sample_nums,
    )
    print(log_formatter.format_divider())
    print(f"RUN_METADATA: {json.dumps(run_metadata, ensure_ascii=False)}")

    function_to_evolve, function_to_run = _extract_function_names(specification)
    template = code_manipulation.text_to_program(specification)
    database = programs_database.ProgramsDatabase(config.programs_database, template, function_to_evolve)

    rag_config = config.rag
    external_retriever = None
    if rag_config.enabled:
        external_retriever = retrieval.ExternalKnowledgeIndex.from_paths(
            rag_config.corpus_root,
            chunk_size=rag_config.chunk_size,
            chunk_overlap=rag_config.chunk_overlap,
            enable_vector_index=(rag_config.retrieval_mode == "vector"),
            embedding_model=rag_config.embedding_model,
            embedding_base_url=rag_config.embedding_base_url,
            embedding_api_key=rag_config.embedding_api_key,
            embedding_timeout_seconds=config.api.timeout_seconds,
        )

    # get log_dir and create profiler
    log_dir = kwargs.get('log_dir', None)
    if log_dir is None:
        profiler = None
    else:
        from implementation import profile as profile_lib
        profiler = profile_lib.Profiler(log_dir)

    evaluators = []
    for _ in range(config.num_evaluators):
        evaluators.append(evaluator.Evaluator(
            database,
            template,
            function_to_evolve,
            function_to_run,
            inputs,
            timeout_seconds=config.evaluate_timeout_seconds,
            sandbox_class=class_config.sandbox_class
        ))

    # We send the initial implementation to be analysed by one of the evaluators.
    initial = template.get_function(function_to_evolve).body
    evaluators[0].analyse(initial, island_id=None, version_generated=None, profiler=profiler)

    # Set global max sample nums.
    samplers = [
        sampler.Sampler(
            database,
            evaluators,
            config.samples_per_prompt,
            max_sample_nums=max_sample_nums,
            llm_class=class_config.llm_class,
            external_retriever=external_retriever,
            rag_top_k=rag_config.top_k,
            llm_model=config.llm_model,
            api_base_url=config.api.base_url,
            api_key=config.api.api_key,
            api_timeout_seconds=config.api.timeout_seconds,
            api_max_retries=config.api.max_retries,
            retrieval_mode=rag_config.retrieval_mode,
            retrieval_score_threshold=rag_config.score_threshold,
            retrieval_max_context_chars=rag_config.max_context_chars,
            retrieval_diagnostics=rag_config.enable_diagnostics,
            retrieval_use_intent_query=rag_config.use_intent_query,
        )
        for _ in range(config.num_samplers)
    ]

    # This loop can be executed in parallel on remote sampler machines. As each
    # sampler enters an infinite loop, without parallelization only the first
    # sampler will do any work.
    for s in samplers:
        s.sample(profiler=profiler)
