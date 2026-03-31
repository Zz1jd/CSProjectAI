import openai
import os
import re
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self, model="gpt-3.5-turbo"):
        self.api_key = os.getenv("API_KEY", "sk-vWpzPgcJaoamJOr998VvL5H4Z2uTt6jNmPk0SftpmCQJYZ5C")
        self.base_url = os.getenv("BASE_URL", "https://api.chatanywhere.com.cn/v1")
        self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.model = model

    def call(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional algorithm expert. Output ONLY Python code body with correct indentation. No explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            content = response.choices[0].message.content
            return self._trim_code(content)
        except Exception as e:
            print(f"LLM Error: {e}")
            return ""

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
