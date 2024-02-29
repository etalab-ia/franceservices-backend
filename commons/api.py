import json
from datetime import datetime, timedelta
from typing import Iterable

import requests
from requests.exceptions import ConnectionError

# @IMPROVE: commons & app.config unification (relative imports...)
try:
    from app.config import (
        API_ROUTE_VER,
        API_URL,
        FIRST_ADMIN_PASSWORD,
        FIRST_ADMIN_USERNAME,
        LLM_TABLE,
    )
except ModuleNotFoundError:
    from api.app.config import (
        API_ROUTE_VER,
        API_URL,
        FIRST_ADMIN_PASSWORD,
        FIRST_ADMIN_USERNAME,
        LLM_TABLE,
    )


class ApiClient:
    def __init__(self, url, username, password):
        self.url = url.rstrip("/")
        self.username = username
        self.password = password

        # Token:
        self.token = None
        self.token_dt = None
        self.token_ttl = 3600 * 23  # seconds

    def _fetch(self, method, route, headers=None, json_data=None):
        d = {
            "POST": requests.post,
            "GET": requests.get,
            "PUT": requests.put,
            "DELETE": requests.delete,
        }
        response = d[method](f"{self.url}{route}", headers=headers, json=json_data)
        response.raise_for_status()
        return response

    def _is_token_expired(self):
        if self.token is None or self.token_dt is None:
            return True
        dt_ttl = datetime.utcnow() - timedelta(seconds=self.token_ttl)
        return self.token_dt < dt_ttl

    def _sign_in(self):
        json_data = {"username": self.username, "password": self.password}
        response = self._fetch("POST", "/sign_in", json_data=json_data)
        self.token = response.json()["token"]
        self.token_dt = datetime.utcnow()

    def _signed_in_fetch(self, method, route, json_data=None):
        if self._is_token_expired():
            self._sign_in()
        headers = {"Authorization": f"Bearer {self.token}"}
        return self._fetch(method, route, headers=headers, json_data=json_data)

    def create_embedding(self, text):
        json_data = {"text": text}
        response = self._signed_in_fetch("POST", "/embeddings", json_data=json_data)
        return response.json()

    def search(
        self,
        index_name,
        query,
        limit=10,
        similarity="bm25",
        institution=None,
        sources=None,
        should_sids=None,
        must_not_sids=None,
    ):
        json_data = {
            "name": index_name,
            "query": query,
            "limit": limit,
            "similarity": similarity,
            "institution": institution,
            "sources": sources,
            "should_sids": should_sids,
            "must_not_sids": must_not_sids,
        }
        response = self._signed_in_fetch("POST", "/indexes", json_data=json_data)
        return response.json()

    def get_prompt_config(self, url):
        headers = {}

        response = requests.get(f"{url}/get_prompt_config", headers=headers)
        response.raise_for_status()

        return response.json()


class ApiVllmClient:
    def __init__(self, url):
        self.url = url

    # TODO: turn into async
    def generate(
        self, prompt, max_tokens=512, temperature=20, top_p=1, streaming=False
    ) -> str | Iterable[str]:
        url = f"{self.url}/generate"
        data = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
            / 100,  # it thinks its better to keep [0,2] value to stay compatible with opanai api. The client can do this operation, if it implement a slider... # fmt: skip
            "top_p": top_p,  # not intended to final user but for dev and research.
            "stream": streaming,
        }
        response = requests.post(url, json=data, stream=streaming)

        if streaming:
            return self._get_streaming_response(response)
        else:
            return self._get_response(response)

    @staticmethod
    def _get_response(response: requests.Response) -> str:
        data = json.loads(response.content)
        output = data["text"]
        # Beams ignored
        return output[0]

    @staticmethod
    def _get_streaming_response(response: requests.Response) -> Iterable[str]:
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


def get_legacy_client() -> ApiClient:
    return ApiClient(
        API_URL.rstrip("/") + "/" + API_ROUTE_VER.strip("/"),
        FIRST_ADMIN_USERNAME,
        FIRST_ADMIN_PASSWORD,
    )


def get_llm_client(model_name: str) -> ApiVllmClient:
    model = next((m for m in LLM_TABLE if m[0] == model_name), None)
    if not model:
        raise ValueError("LLM model not found: %s" % model_name)

    model_url = model[1]
    return ApiVllmClient(model_url)
