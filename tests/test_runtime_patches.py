import unittest

from implementation.llm_client import LLMClient
from scripts._runtime_patches import patched_iteration_runtime


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeChoice(content)]


class _RejectThinkingCompletions:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        raise RuntimeError("Unrecognized request argument supplied: enable_thinking")


class _FakeChat:
    def __init__(self, completions: _RejectThinkingCompletions) -> None:
        self.completions = completions


class _FakeOpenAIClient:
    def __init__(self, completions: _RejectThinkingCompletions) -> None:
        self.chat = _FakeChat(completions)


class RuntimePatchesTests(unittest.TestCase):
    def test_thinking_patch_propagates_provider_rejection_without_fallback(self) -> None:
        completions = _RejectThinkingCompletions()
        original_call = LLMClient.call

        client = LLMClient(
            model="gpt-4o-mini",
            base_url="https://cli.example/v1",
            api_key="cli-key",
            max_retries=0,
            client_factory=lambda **_: _FakeOpenAIClient(completions),
        )

        with self.assertRaisesRegex(RuntimeError, "enable_thinking"):
            with patched_iteration_runtime(enable_thinking=True, zero_context_means_unlimited=False):
                client.call("improve this")

        self.assertEqual(len(completions.calls), 1)
        self.assertEqual(completions.calls[0]["extra_body"], {"enable_thinking": True})
        self.assertIs(LLMClient.call, original_call)


if __name__ == "__main__":
    unittest.main()