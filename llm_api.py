import time
import json
import multiprocessing
from typing import Collection, Any
import http.client
from implementation import sampler


def _trim_preface_of_body(sample: str) -> str:
    lines = sample.splitlines()
    func_body_lineno = 0
    find_def_declaration = False
    for lineno, line in enumerate(lines):
        if line[:3] == 'def':
            func_body_lineno = lineno
            find_def_declaration = True
            break
    if find_def_declaration:
        code = ''
        for line in lines[func_body_lineno + 1:]:
            code += line + '\n'
        return code
    return sample


class LLMAPI(sampler.LLM):
    def __init__(self, samples_per_prompt: int, trim=True):
        super().__init__(samples_per_prompt)
        additional_prompt = ('You are an expert in optimization of CVRP, generate a specific improvement strategy based on the current state of the solution.'
                             'Complete a different and more complex Python function. '
                             'Be creative and you can insert multiple if-else and for-loop in the code logic.'
                             'Only output the Python code, no descriptions.')
        self._additional_prompt = additional_prompt
        self._trim = trim

    def draw_samples(self, prompt: str) -> Collection[str]:
        return [self._draw_sample(prompt) for _ in range(self._samples_per_prompt)]

    def _draw_sample(self, content: str) -> str:
        prompt = '\n'.join([content, self._additional_prompt])
        auth_header = 'Bearer [replace with your own API key]'
        while True:
            try:
                conn = http.client.HTTPSConnection("api.chatanywhere.com.cn")
                payload = json.dumps({
                    "max_tokens": 512,
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
                headers = {
                    'Authorization': auth_header,
                    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
                    'Content-Type': 'application/json'
                }
                conn.request("POST", "/v1/chat/completions", payload, headers)
                res = conn.getresponse()
                data = res.read().decode("utf-8")
                data = json.loads(data)
                response = data['choices'][0]['message']['content']
                if self._trim:
                    response = _trim_preface_of_body(response)
                return response
            except Exception:
                time.sleep(2)
                continue
