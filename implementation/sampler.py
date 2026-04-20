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

"""Class for sampling new programs."""
from __future__ import annotations
from abc import ABC, abstractmethod
import json

from typing import Any, Collection, Sequence, Type
import numpy as np
import time

from implementation import evaluator
from implementation import programs_database
from implementation import prompt_engine
from implementation import retrieval
from implementation import llm_client


class LLM(ABC):
    """Language model that predicts continuation of provided source code.

    RZ: The sampled function code must be trimmed! Especially using instruct-based LLM.
    -For example, the sampled function code (with description) is:
    ------------------------------------------------------------------------------------------------------------------
    Here is the function.
    def priority_v2(..., ...) -> Any:
        a = np.array([1, 2, 3])
        if len(a) > 2:
            return a / a.sum()
        else:
            return a / a.mean()
    This function is going to ..., and returns ...[Descriptions by LLM]
    ------------------------------------------------------------------------------------------------------------------
    -The descriptions above the function's signature, and the function's signature must be removed.
    -The above code must be trimmed as follows:
    ------------------------------------------------------------------------------------------------------------------
        a = np.array([1, 2, 3])
            if len(a) > 2:
                return a / a.sum()
            else:
                return a / a.mean()
        Here is the function. This function is going to ..., and returns ...[Descriptions by LLM]
    ------------------------------------------------------------------------------------------------------------------
    Please note that the indent must be preserved. And the additional descriptions can also be preserved,
    which will be trimmed by Evaluator.
    """

    def __init__(self, samples_per_prompt: int) -> None:
        self._samples_per_prompt = samples_per_prompt

    def _draw_sample(self, prompt: str) -> str:
        """Returns a predicted continuation of `prompt`."""
        raise NotImplementedError('Must provide a language model.')

    @abstractmethod
    def draw_samples(self, prompt: str) -> Collection[str]:
        """Returns multiple predicted continuations of `prompt`."""
        return [self._draw_sample(prompt) for _ in range(self._samples_per_prompt)]


class Sampler:
    """Node that samples program continuations and sends them for analysis.
    """
    _global_samples_nums: int = 0  # RZ: this variable records the global sample nums

    def __init__(
            self,
            database: programs_database.ProgramsDatabase,
            evaluators: Sequence[evaluator.Evaluator],
            samples_per_prompt: int,
            max_sample_nums: int | None = None,
            llm_class: Type[LLM] = LLM,
            external_retriever: retrieval.ExternalKnowledgeIndex | None = None,
            rag_top_k: int = 3,
            llm_model: str | None = None,
            api_base_url: str | None = None,
            api_key: str | None = None,
            api_timeout_seconds: int = 60,
            api_max_retries: int = 2,
            retrieval_mode: str = "vector",
            retrieval_score_threshold: float = 0.0,
            retrieval_max_context_chars: int = 1200,
            retrieval_diagnostics: bool = False,
                retrieval_use_intent_query: bool = True,
    ):
        self._samples_per_prompt = samples_per_prompt
        self._database = database
        self._evaluators = evaluators
        self._max_sample_nums = max_sample_nums
        self._external_retriever = external_retriever
        self._rag_top_k = rag_top_k
        self._retrieval_mode = retrieval_mode
        self._retrieval_score_threshold = retrieval_score_threshold
        self._retrieval_max_context_chars = retrieval_max_context_chars
        self._retrieval_diagnostics = retrieval_diagnostics
        self._retrieval_use_intent_query = retrieval_use_intent_query
        # 初始化移植的引擎和客户端
        self._prompt_engine = prompt_engine.PromptEngine(task_type="CVRP")
        self._llm_client = llm_client.LLMClient(
            model=llm_model or "gpt-3.5-turbo",
            base_url=api_base_url,
            api_key=api_key,
            timeout_seconds=api_timeout_seconds,
            max_retries=api_max_retries,
        )

    def sample(self, **kwargs):
        """Continuously gets prompts, samples programs, sends them for analysis.
        """
        while True:
            # stop the search process if hit global max sample nums
            if self._max_sample_nums and self.__class__._global_samples_nums >= self._max_sample_nums:
                break
            try:
                prompt = self._database.get_prompt()

                batch_size = self._samples_per_prompt
                if self._max_sample_nums is not None:
                    remaining_budget = self._max_sample_nums - self.__class__._global_samples_nums
                    if remaining_budget <= 0:
                        break
                    # Clamp the current draw so one loop iteration cannot overshoot budget.
                    batch_size = min(batch_size, remaining_budget)

                # --- 移植核心：使用 CoT 增强后的 Prompt ---
                retrieval_diagnostics = {} if self._retrieval_diagnostics else None
                enhanced_prompt = retrieval.build_enhanced_prompt(
                    base_code=prompt.code,
                    prompt_engine=self._prompt_engine,
                    retriever=self._external_retriever,
                    top_k=self._rag_top_k,
                    retrieval_mode=self._retrieval_mode,
                    score_threshold=self._retrieval_score_threshold,
                    max_context_chars=self._retrieval_max_context_chars,
                    use_intent_query=self._retrieval_use_intent_query,
                    diagnostics=retrieval_diagnostics,
                )

                if retrieval_diagnostics is not None:
                    print(f"RETRIEVAL_DIAGNOSTICS: {json.dumps(retrieval_diagnostics, ensure_ascii=False)}")
                
                reset_time = time.time()
                # 使用 LLMClient 进行采样
                raw_samples = [self._llm_client.call(enhanced_prompt) for _ in range(batch_size)]
                
                # --- 调试：打印前 100 个字符看看裁剪后的样子 ---
                for i, s in enumerate(raw_samples):
                    if not s or len(s.strip()) < 5:
                        print(f"DEBUG: Sample {i} is empty or too short!")
                    else:
                        print(f"DEBUG: Sample {i} prefix: {s[:100].replace('\n', ' ')}...")
                
                samples = raw_samples
                # ---------------------------------------

                sample_time = (time.time() - reset_time) / batch_size
                # This loop can be executed in parallel on remote evaluator machines.
                for sample in samples:
                    self._global_sample_nums_plus_one()  # RZ: add _global_sample_nums
                    cur_global_sample_nums = self._get_global_sample_nums()
                    chosen_evaluator: evaluator.Evaluator = np.random.choice(self._evaluators)
                    chosen_evaluator.analyse(
                        sample,
                        prompt.island_id,
                        prompt.version_generated,
                        **kwargs,
                        global_sample_nums=cur_global_sample_nums,
                        sample_time=sample_time
                    )
            except Exception as error:
                print(f"SAMPLER_ERROR: {error}")
                raise

    def _get_global_sample_nums(self) -> int:
        return self.__class__._global_samples_nums

    def set_global_sample_nums(self, num):
        self.__class__._global_samples_nums = num

    def _global_sample_nums_plus_one(self):
        self.__class__._global_samples_nums += 1
