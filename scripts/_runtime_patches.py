from __future__ import annotations

import contextlib
import re
from typing import Iterator, Sequence

from implementation import llm_client as llm_client_lib
from implementation import retrieval as retrieval_lib


_THINKING_TAG_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_ACTIVE_REASONING_PROBE: object | None = None


def _build_reasoning_extra_body(reasoning_probe: object | None) -> dict[str, object]:
    if reasoning_probe is None:
        return {"enable_thinking": True}

    request_mode = getattr(reasoning_probe, "request_mode", None)
    reasoning_effort = getattr(reasoning_probe, "reasoning_effort", None)
    if request_mode == "enable_thinking":
        return {"enable_thinking": True}
    if request_mode == "reasoning_effort":
        if not isinstance(reasoning_effort, str) or not reasoning_effort:
            raise ValueError("reasoning_effort probe requires a non-empty reasoning_effort value.")
        return {"reasoning_effort": reasoning_effort}
    raise ValueError(f"Unsupported reasoning probe mode: {request_mode}")


def _build_completion_request(
    self: llm_client_lib.LLMClient,
    prompt: str,
    *,
    enable_thinking: bool,
    reasoning_probe: object | None,
) -> dict[str, object]:
    request: dict[str, object] = {
        "model": self.model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a professional algorithm expert. "
                    "Output ONLY Python code body with correct indentation. "
                    "No explanations."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "timeout": self.timeout_seconds,
    }
    if enable_thinking:
        request["extra_body"] = _build_reasoning_extra_body(reasoning_probe)
    return request


def _sanitize_response_content(content: str) -> str:
    if _THINKING_TAG_PATTERN.search(content):
        return _THINKING_TAG_PATTERN.sub("", content).strip()
    return content


def _request_completion(
    self: llm_client_lib.LLMClient,
    prompt: str,
    *,
    enable_thinking: bool,
    reasoning_probe: object | None,
) -> str:
    response = self.client.chat.completions.create(
        **_build_completion_request(
            self,
            prompt,
            enable_thinking=enable_thinking,
            reasoning_probe=reasoning_probe,
        )
    )
    content = response.choices[0].message.content or ""
    return self._trim_code(_sanitize_response_content(content))


def _call_with_thinking(self: llm_client_lib.LLMClient, prompt: str) -> str:
    last_error: Exception | None = None
    attempts = max(1, self.max_retries + 1)
    for _ in range(attempts):
        try:
            return _request_completion(
                self,
                prompt,
                enable_thinking=True,
                reasoning_probe=_ACTIVE_REASONING_PROBE,
            )
        except Exception as error:  # pragma: no cover - exercised via injected fakes
            last_error = error

    raise RuntimeError(f"LLM call failed after {attempts} attempts: {last_error}")


def _fit_chunks_with_zero_as_unlimited(
    chunks: Sequence[retrieval_lib.KnowledgeChunk],
    max_chars: int,
) -> list[retrieval_lib.KnowledgeChunk]:
    if max_chars == 0:
        return list(chunks)
    return _ORIGINAL_FIT_CHUNKS_TO_CONTEXT(chunks, max_chars)


_ORIGINAL_FIT_CHUNKS_TO_CONTEXT = retrieval_lib._fit_chunks_to_context


def probe_reasoning_support(
    client: llm_client_lib.LLMClient,
    reasoning_probe: object,
) -> None:
    """Fail-fast probe for provider-specific reasoning request modes."""
    request = _build_completion_request(
        client,
        "Return ok",
        enable_thinking=True,
        reasoning_probe=reasoning_probe,
    )
    client.client.chat.completions.create(**request)


@contextlib.contextmanager
def patched_iteration_runtime(
    *,
    enable_thinking: bool,
    zero_context_means_unlimited: bool,
    reasoning_probe: object | None = None,
) -> Iterator[None]:
    """Apply experiment-only runtime behavior from scripts without editing implementation/."""

    original_call = llm_client_lib.LLMClient.call
    original_fit_chunks = retrieval_lib._fit_chunks_to_context

    global _ACTIVE_REASONING_PROBE
    previous_reasoning_probe = _ACTIVE_REASONING_PROBE

    if enable_thinking:
        _ACTIVE_REASONING_PROBE = reasoning_probe
        llm_client_lib.LLMClient.call = _call_with_thinking
    if zero_context_means_unlimited:
        retrieval_lib._fit_chunks_to_context = _fit_chunks_with_zero_as_unlimited

    try:
        yield
    finally:
        _ACTIVE_REASONING_PROBE = previous_reasoning_probe
        llm_client_lib.LLMClient.call = original_call
        retrieval_lib._fit_chunks_to_context = original_fit_chunks