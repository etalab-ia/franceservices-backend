import json
import requests

from app.config import API_VLLM_URL


class ApiVllmClient:
    def __init__(self):
        self.url = API_VLLM_URL

    # TODO: turn into async
    def generate(self, prompt, max_tokens=500, temp=20, streaming=True):
        url = f"{self.url}/generate"
        data = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temp / 100,
            "stream": streaming,
        }
        response = requests.post(url, json=data, stream=streaming)

        prev_len = 0
        chunks = response.iter_lines(chunk_size=8192, delimiter=b"\0")
        for chunk in chunks:
            if not chunk:
                continue

            data = json.loads(chunk.decode("utf-8"))
            output = data["text"][0]
            yield output[prev_len:]
            prev_len = len(output)
