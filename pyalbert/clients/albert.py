import json
from datetime import datetime, timedelta
from typing import Iterable

import requests

from pyalbert.config import (
    API_ROUTE_VER,
    API_URL,
    EMBEDDING_MODEL,
    FIRST_ADMIN_PASSWORD,
    FIRST_ADMIN_USERNAME,
    LLM_TABLE,
)


class AlbertClient:
    def __init__(self):
        # Default client
        url = API_URL.rstrip("/") + "/" + API_ROUTE_VER.strip("/")
        username = FIRST_ADMIN_USERNAME
        password = FIRST_ADMIN_PASSWORD

        # @IMPROVE: ALBERT_API_TOKEN token could be passed/read here,
        #           to avoid doing incessnt signin request.
        #           Related to #132

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

    def create_embeddings(
        self,
        texts: str | list[str],
        doc_type: str | None = None,
        model: str | None = None,
    ) -> dict:
        json_data = {"input": texts}
        if doc_type:
            json_data["doc_type"] = doc_type
        if model:
            json_data["model"] = model
        response = self._signed_in_fetch("POST", "/embeddings", json_data=json_data)
        response.raise_for_status()
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
        # @IMPROVE: this function suppose that the client that use this class has access to the url
        # given in the LLM_TABLE which expose llm-api that is not intended to be publicly open.
        # Thus, to make this function usable by client outside the private network of Albert,
        # the albert-api should implement a bridge route to /get_prompt_config.
        headers = {}
        response = requests.get(f"{url}/get_prompt_config", headers=headers)
        response.raise_for_status()
        return response.json()


class LlmClient:
    def __init__(self, model: str, url=None):
        model = next((m for m in LLM_TABLE if m[0] == model), None)
        if not model:
            raise ValueError("LLM model not found: %s" % model)

        if model[1]:
            url = model[1]

        self.model = model
        self.url = url

    @staticmethod
    def _get_response(response: requests.Response) -> str:
        data = json.loads(response.content)
        output = data["text"]
        # Beams ignored
        return output[0].strip()

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

    # TODO: turn into async
    def generate(
        self, prompt, max_tokens=512, temperature=20, top_p=1, stream=False
    ) -> str | Iterable[str]:
        url = f"{self.url}/generate"
        data = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature / 100,  # I think its better to keep value in [0,2] to stay compatible with opanai api.
            "top_p": top_p,  # not intended to final user but for dev and research.
            "stream": stream,
        }  # fmt: skip
        response = requests.post(url, json=data, stream=stream)

        if stream:
            return self._get_streaming_response(response)
        else:
            return self._get_response(response)

    # Only one embedding model supported for now
    @classmethod
    def create_embeddings(
        cls,
        texts: str | list[str],
        doc_type: str | None = None,
        model: str | None = None,
        openai_format: bool = False,
    ) -> list[float] | list[list[float]] | dict:
        # client = cls(*EMBEDDING_MODEL)  # let's see that later !
        # url = client.url
        model, url = EMBEDDING_MODEL
        json_data = {"input": texts}
        if doc_type:
            json_data["doc_type"] = doc_type
        if model:
            json_data["model"] = model
        response = requests.post(url.rstrip("/") + "/v1/embeddings", json=json_data)
        response.raise_for_status()
        results = response.json()
        if openai_format:
            return results

        if isinstance(texts, str):
            results = results["data"][0]["embedding"]
        else:
            results = [x["embedding"] for x in results["data"]]

        return results
