import json
from datetime import datetime, timedelta
from typing import Generator

import lz4.frame
import requests

from pyalbert.config import (
    ACCESS_TOKEN_TTL,
    API_PREFIX_V1,
    API_PREFIX_V2,
    API_ROUTE_VER,
    API_URL,
    FIRST_ADMIN_PASSWORD,
    FIRST_ADMIN_USERNAME,
    LLM_TABLE,
    RAG_EMBEDDING_MODEL,
)


def log_and_raise_for_status(response):
    if not response.ok:
        try:
            error_detail = response.json().get("detail")
        except Exception:
            error_detail = response.text
        print(f"Error: Albert API Error Detail: {error_detail}")
        response.raise_for_status()


class AlbertClient:
    CONFIG = {
        "base_url": API_URL,
        "username": FIRST_ADMIN_USERNAME,
        "password": FIRST_ADMIN_PASSWORD,
    }

    def __init__(self, api_key=None, **user_config):
        if api_key is not None and (user_config.get("username") or user_config.get("password")):
            print(
                "Error: You need to either set the api_key or the username/password couple, but not both at the same time."
            )
            exit(2)

        config = self.CONFIG
        if user_config:
            config.update(user_config)

        self.url = (
            config["base_url"].rstrip("/") + "/" + API_PREFIX_V2.strip("/") if API_PREFIX_V2 else ""
        )
        self.username = config["username"]
        self.password = config["password"]

        # Token:
        self.token = None
        self.token_dt = None
        self.token_ttl = ACCESS_TOKEN_TTL - 2
        self.api_key = api_key

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

    def _fetch(self, method, route, headers=None, json_data=None, stream=None):
        d = {
            "POST": requests.post,
            "GET": requests.get,
            "PUT": requests.put,
            "DELETE": requests.delete,
        }
        response = d[method](
            f"{self.url}{route}", headers=headers, json=json_data, stream=stream
        )
        log_and_raise_for_status(response)
        return response

    def _signed_in_fetch(self, method, route, json_data=None, stream=None):
        if self.api_key:
            self.token = self.api_key
        elif self._is_token_expired():
            self._sign_in()
        headers = {"Authorization": f"Bearer {self.token}"}
        return self._fetch(method, route, headers=headers, json_data=json_data, stream=stream)

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
        log_and_raise_for_status(response)
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
    ) -> list:
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

    def get_prompt_config(self, url: str) -> dict:
        # @IMPROVE: this function suppose that the client that use this class has access to the url
        # given in the LLM_TABLE which expose llm-api that is not intended to be publicly open.
        # Thus, to make this function usable by client outside the private network of Albert,
        # the albert-api should implement a bridge route to /get_prompt_config.
        headers = {}
        response = requests.get(f"{url}/get_prompt_config", headers=headers)
        log_and_raise_for_status(response)
        return response.json()

    def get_stream(self, stream_id: int) -> dict:
        # Get stream data
        response = self._signed_in_fetch("GET", f"/stream/{stream_id}")
        stream = response.json()
        return stream

    def review_prompt(self, stream_id: int) -> str | None:
        """Get the raw prompt used for the given stream id"""
        stream = self.get_stream(stream_id)
        if not stream["prompt"]:
            return None
        return lz4.frame.decompress(bytes.fromhex(stream["prompt"])).decode("utf-8")

    def new_chat(self, chat_type: str) -> int:
        response = self._signed_in_fetch("POST", "/chat", json={"chat_type": chat_type})
        chat_id = response.json()["id"]
        return chat_id

    def new_stream(self, chat_id: None | str = None, **kwargs) -> int:
        if chat_id:
            response = self._signed_in_fetch("POST", f"/stream/chat/{chat_id}", json=kwargs)
        else:
            response = self._signed_in_fetch("POST", "/stream", json=kwargs)
        stream_id = response.json()["id"]
        return stream_id

    def generate(self, stream_id, stream=False) -> str | Generator:
        response = self._signed_in_fetch("GET", "/stream/{stream_id}/start", stream=stream)
        if stream:
            for chunk in response.iter_lines():
                if not chunk:
                    continue

                decoded_line = chunk.decode("utf-8")
                _, _, data = decoded_line.partition("data: ")
                try:
                    text = json.loads(data)
                    if text == "[DONE]":
                        break
                    yield text
                except json.decoder.JSONDecodeError as e:
                    # Should never happen...
                    print("\nDATA: " + data)
                    print("\nERROR:")
                    raise e
        else:
            # @TODO
            text = json.loads(response.content)
            return text


    @staticmethod
    def _get_streaming_response(response: requests.Response) -> Generator[str, None, None]:
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

class LlmClient:
    def __init__(self, model: str, url=None):
        model = next((m for m in LLM_TABLE if m["model"] == model), None)
        if not model:
            raise ValueError("LLM model not found: %s" % model)

        self.url = model["url"]

    @staticmethod
    def _get_response(response: requests.Response) -> str:
        data = json.loads(response.content)
        output = data["text"]
        # Beams ignored
        return output[0].strip()

    @staticmethod
    def _get_streaming_response(response: requests.Response) -> Generator[str, None, None]:
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
        self,
        prompt: str,
        stream=False,
        **sampling_params,
    ) -> str | Generator:
        url = f"{self.url}/generate"
        data = sampling_params.copy()
        data["prompt"] = prompt
        data["stream"] = stream
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
        model = model or RAG_EMBEDDING_MODEL
        default_model, default_url = LLM_TABLE[0]["model"], LLM_TABLE[0]["url"]
        model, url = next(
            ((d["model"], d["url"]) for d in LLM_TABLE if d["model"] == model),
            (default_model, default_url),
        )
        json_data = {"input": texts}
        if doc_type:
            json_data["doc_type"] = doc_type
        if model:
            json_data["model"] = model
        response = requests.post(url.rstrip("/") + "/embeddings", json=json_data)
        log_and_raise_for_status(response)
        results = response.json()
        if openai_format:
            return results

        if isinstance(texts, str):
            results = results["data"][0]["embedding"]
        else:
            results = [x["embedding"] for x in results["data"]]

        return results
