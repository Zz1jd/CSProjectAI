import unittest

from implementation.llm_client import LLMClient


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, content: str) -> None:
        self._content = content
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeResponse(self._content)


class _FakeChat:
    def __init__(self, content: str) -> None:
        self.completions = _FakeCompletions(content)


class _FakeOpenAIClient:
    def __init__(self, content: str) -> None:
        self.chat = _FakeChat(content)


class LLMClientTests(unittest.TestCase):
    def test_explicit_config_is_used(self) -> None:
        factory_calls: list[dict[str, str]] = []

        def fake_factory(api_key: str, base_url: str):
            factory_calls.append({"api_key": api_key, "base_url": base_url})
            return _FakeOpenAIClient("    return 1")

        client = LLMClient(
            model="gpt-4o-mini",
            base_url="https://cli.example/v1",
            api_key="cli-key",
            client_factory=fake_factory,
        )
        self.assertEqual(client.model, "gpt-4o-mini")
        self.assertEqual(factory_calls[0]["api_key"], "cli-key")
        self.assertEqual(factory_calls[0]["base_url"], "https://cli.example/v1")

    def test_missing_api_config_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            LLMClient(model="gpt-4o-mini", client_factory=lambda **_: _FakeOpenAIClient("x"))

    def test_call_uses_chat_completion_and_trims_markdown(self) -> None:
        fake_client = _FakeOpenAIClient("```python\n    scores = distance_data[current_node]\n    return -scores\n```")

        def fake_factory(api_key: str, base_url: str):
            return fake_client

        client = LLMClient(
            model="gpt-4o-mini",
            base_url="https://cli.example/v1",
            api_key="cli-key",
            client_factory=fake_factory,
        )

        result = client.call("improve this")
        self.assertIn("scores = distance_data[current_node]", result)
        self.assertIn("return -scores", result)
        self.assertEqual(len(fake_client.chat.completions.calls), 1)

    def test_endpoint_style_base_url_is_normalized(self) -> None:
        factory_calls: list[dict[str, str]] = []

        def fake_factory(api_key: str, base_url: str):
            factory_calls.append({"api_key": api_key, "base_url": base_url})
            return _FakeOpenAIClient("    return 1")

        LLMClient(
            model="gpt-4o-mini",
            base_url="api.chatanywhere.com.cn/v1/chat/completions",
            api_key="cli-key",
            client_factory=fake_factory,
        )

        self.assertEqual(factory_calls[0]["base_url"], "https://api.chatanywhere.com.cn/v1")


if __name__ == "__main__":
    unittest.main()
