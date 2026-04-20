import re

from implementation.openai_compat import normalize_openai_base_url


class LLMClient:
    def __init__(
            self,
            model: str = "gpt-3.5-turbo",
            base_url: str | None = None,
            api_key: str | None = None,
            timeout_seconds: int = 60,
            max_retries: int = 2,
            client_factory=None,
    ) -> None:
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

        self.api_key = api_key
        self.base_url = normalize_openai_base_url(base_url) if base_url else base_url

        if not self.api_key or not self.base_url:
            raise ValueError(
                "Missing API configuration. Set APIConfig in implementation/config.py."
            )

        if client_factory is None:
            from openai import OpenAI

            client_factory = OpenAI
        self.client = client_factory(api_key=self.api_key, base_url=self.base_url)

    def call(self, prompt: str) -> str:
        last_error: Exception | None = None
        attempts = max(1, self.max_retries + 1)
        for _ in range(attempts):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
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
                    temperature=0.7,
                    timeout=self.timeout_seconds,
                )
                content = response.choices[0].message.content or ""
                return self._trim_code(content)
            except Exception as error:  # pragma: no cover - exercised via injected fakes
                last_error = error

        raise RuntimeError(f"LLM call failed after {attempts} attempts: {last_error}")

    def _trim_code(self, sample: str) -> str:
        """优化裁剪逻辑：保留缩进，处理 Markdown 代码块"""
        # 1. 优先提取 Markdown 代码块内容
        code_block = re.search(r'```python\n(.*?)\n```', sample, re.DOTALL)
        if code_block:
            sample = code_block.group(1)
        else:
            sample = re.sub(r'```python|```', '', sample)

        lines = sample.splitlines()
        func_body_lineno = -1
        for lineno, line in enumerate(lines):
            if line.strip().startswith('def '):
                func_body_lineno = lineno
                break
        
        if func_body_lineno != -1:
            # 关键修改：不要对整个结果使用 .strip()，只去掉尾部空白
            # 这样能保留第一行代码的开头缩进
            body_lines = lines[func_body_lineno + 1:]
            return "\n".join(body_lines).rstrip()
        
        return sample.rstrip()
