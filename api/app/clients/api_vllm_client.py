import json
import requests
from typing import Iterable, List

from app.config import API_VLLM_URL


def get_response(response: requests.Response) -> str:
    data = json.loads(response.content)
    output = data["text"]
    # Beams ignored
    return output[0]


def get_streaming_response(response: requests.Response) -> Iterable[str]:
    prev_len = 0
    chunks = response.iter_lines(chunk_size=8192, delimiter=b"\0")
    for chunk in chunks:
        if not chunk:
            continue

        data = json.loads(chunk.decode("utf-8"))
        # Beams ignored
        output = data["text"][0]
        yield output[prev_len:]
        prev_len = len(output)


class ApiVllmClient:
    def __init__(self, url=None):
        if not url:
            url = API_VLLM_URL

        self.url = url

    # TODO: turn into async
    def generate(
        self, prompt, max_tokens=512, temperature=20, top_p=1, streaming=True
    ) -> str | Iterable[str]:
        url = f"{self.url}/generate"
        data = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
            / 100,  # it thinks its better to keep [0,2] value to stay compatible with opanai api. The client can do this operation, if it implement a slider...
            "top_p": top_p,  # not intended to final user but for dev and research.
            "stream": streaming,
        }
        response = requests.post(url, json=data, stream=streaming)

        if streaming:
            return get_streaming_response(response)
        else:
            return get_response(response)
