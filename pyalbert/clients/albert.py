import json
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Generator

import lz4.frame
import requests
from elasticsearch import Elasticsearch
from qdrant_client import QdrantClient
from qdrant_client import models as QdrantModels

from pyalbert import collate_ix_name
from pyalbert.config import (
    ACCESS_TOKEN_TTL,
    ALBERT_MODELS_API_KEY,
    API_PREFIX_V2,
    API_URL,
    ELASTICSEARCH_CREDS,
    ELASTICSEARCH_IX_VER,
    ELASTICSEARCH_URL,
    FIRST_ADMIN_PASSWORD,
    FIRST_ADMIN_USERNAME,
    HYBRID_COLLECTIONS,
    LLM_API_VER,
    LLM_TABLE,
    QDRANT_GRPC_PORT,
    QDRANT_IX_VER,
    QDRANT_REST_PORT,
    QDRANT_URL,
    QDRANT_USE_GRPC,
    RAG_EMBEDDING_MODEL,
)
from pyalbert.lexicon import expand_acronyms
from pyalbert.schemas import RagChatCompletionResponse, RagParams
from pyalbert.utils import log_and_raise_for_status, retry, sse_decoder


# @TODO: Will be renamed as MfsClient ?
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
        response = d[method](f"{self.url}{route}", headers=headers, json=json_data, stream=stream)
        log_and_raise_for_status(response, "Albert API error")
        return response

    def _signed_in_fetch(self, method, route, json_data=None, stream=None):
        if self.api_key:
            self.token = self.api_key
        elif self._is_token_expired():
            self._sign_in()
        headers = {"Authorization": f"Bearer {self.token}"}
        return self._fetch(method, route, headers=headers, json_data=json_data, stream=stream)

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

    def get_stream(self, stream_id: int) -> dict:
        """Get the given stream data"""
        response = self._signed_in_fetch("GET", f"/stream/{stream_id}")
        stream = response.json()
        return stream

    def get_full_chat(self, chat_id: int) -> dict:
        """Get the so-called chat archive"""
        response = self._signed_in_fetch("GET", f"/chat/archive/{chat_id}")
        chat = response.json()
        return chat

    def review_prompt(self, stream_id: int) -> str | None:
        """Get the raw prompt used for the given stream id"""
        stream = self.get_stream(stream_id)
        if not stream["prompt"]:
            return None
        return lz4.frame.decompress(bytes.fromhex(stream["prompt"])).decode("utf-8")

    def review_chat(self, chat_id: int) -> str | None:
        """Get the raw prompt used for the given stream id"""
        chat = self.get_full_chat(chat_id)
        return chat

    def new_chat(self, chat_type: str) -> int:
        response = self._signed_in_fetch("POST", "/chat", json_data={"chat_type": chat_type})
        chat_id = response.json()["id"]
        return chat_id

    def new_stream(self, chat_id: None | str = None, **kwargs) -> int:
        if chat_id:
            response = self._signed_in_fetch("POST", f"/stream/chat/{chat_id}", json_data=kwargs)
        else:
            response = self._signed_in_fetch("POST", "/stream", json_data=kwargs)
        stream_id = response.json()["id"]
        return stream_id

    def generate(self, stream_id, stream=False) -> str | Generator:
        response = self._signed_in_fetch("GET", f"/stream/{stream_id}/start", stream=stream)
        if stream:
            for chunk in sse_decoder(response.iter_content(chunk_size=1024)):
                yield chunk["text"]
        else:
            # @TODO
            text = json.loads(response.content)
            return text


class LlmClient:
    def __init__(self, model: str, api_key=None, base_url=None):
        self.model = model
        self.api_key = api_key
        if not base_url:
            model_ = next((m for m in LLM_TABLE if m["model"] == model), None)
            if not model_:
                raise ValueError("LLM model not found: %s" % model)

            self.url = model_["url"]
            self.url = f"{self.url}/{LLM_API_VER}" if LLM_API_VER else self.url
        else:
            self.url = base_url

        self.url = self.url.rstrip("/")

    @staticmethod
    def _get_streaming_response(response: requests.Response) -> Generator[bytes, None, None]:
        for chunk in response.iter_content(chunk_size=1024):
            yield chunk

    # TODO: turn into async
    @retry(tries=3, delay=2)
    def generate(
        self,
        messages: str | list[dict] | None = None,
        stream: bool = False,
        path: str = "/chat/completions",
        rag: dict | None = None,
        **sampling_params,
    ) -> RagChatCompletionResponse | Generator:
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        elif isinstance(messages, list):
            # Assume ChatCompletionRequest
            pass
        else:
            raise ValueError("messages type not supported. Messages must be str of list[dict]")

        json_data = sampling_params.copy()
        json_data["messages"] = messages
        json_data["model"] = self.model
        json_data["stream"] = stream
        if rag:
            json_data["rag"] = RagParams(**rag).model_dump()

        headers = None
        if self.api_key:
            headers = {"Authorization": f"Bearer {self.api_key}"}
        elif ALBERT_MODELS_API_KEY:
            headers = {"Authorization": f"Bearer {ALBERT_MODELS_API_KEY}"}
        url = f"{self.url}{path}"
        response = requests.post(url, headers=headers, json=json_data, stream=stream)
        log_and_raise_for_status(response, "Albert API error")

        if stream:
            return self._get_streaming_response(response)

        r = response.json()
        return RagChatCompletionResponse(**r)

    # TODO: turn into async
    @classmethod
    @retry(tries=3, delay=2)
    def create_embeddings(
        cls,
        texts: str | list[str],
        doc_type: str | None = None,
        model: str | None = None,
        path: str = "/embeddings",
        openai_format: bool = False,
        api_key=None,
    ) -> list[float] | list[list[float]] | dict:
        """Simple interface to create an embedding vector from a text input or a list of texd inputs."""
        model = model or RAG_EMBEDDING_MODEL
        model, url = next(
            ((d["model"], d["url"]) for d in LLM_TABLE if d["model"] == model),
            (None, None),
        )

        if not model:
            raise ValueError("Embedgging model unknown. Please use an available embedding model.")

        json_data = {"input": texts}
        if doc_type:
            json_data["doc_type"] = doc_type
        if model:
            json_data["model"] = model

        headers = None
        if api_key:
            headers = {"Authorization": f"Bearer {api_key}"}
        elif ALBERT_MODELS_API_KEY:
            headers = {"Authorization": f"Bearer {ALBERT_MODELS_API_KEY}"}
        url = f"{url}/{LLM_API_VER}{path}" if LLM_API_VER else f"{url}{path}"
        response = requests.post(url, headers=headers, json=json_data)
        log_and_raise_for_status(response, "LLM API error")
        results = response.json()
        if openai_format:
            return results

        if isinstance(texts, str):
            results = results["data"][0]["embedding"]
        else:
            results = [x["embedding"] for x in results["data"]]

        return results


class SearchEngineClient:
    # Global config
    CONFIG = {
        "default_engine": "elasticsearch",
        "hybrid_collections": HYBRID_COLLECTIONS,
        # Elastic config
        "es_url": ELASTICSEARCH_URL,
        "es_creds": ELASTICSEARCH_CREDS,
        "es_col_version": ELASTICSEARCH_IX_VER,
        # Qdrant config
        "qdrant_url": QDRANT_URL,
        "qdrant_grpc_port": QDRANT_GRPC_PORT,
        "qdrant_rest_port": QDRANT_REST_PORT,
        "qdrant_use_grpc": QDRANT_USE_GRPC,
        "qdrant_col_version": QDRANT_IX_VER,
    }

    def __init__(self, **config):
        self.config = self.CONFIG.copy()
        if config:
            self.config.update(config)

        self.config = namedtuple("Config", self.config.keys())(**self.config)

    def search(
        self,
        collection: str,
        query: str,
        limit: int = 5,
        engine: str = None,
        do_expand_acronyms: bool = False,
        filters=None,
    ) -> list[dict]:
        engine = engine if engine else self.config.default_engine

        if do_expand_acronyms:
            query = expand_acronyms(query)

        match engine:
            case "elasticsearch":
                results = self._search_es(collection, query, limit=limit, filters=filters)
            case "qdrant":
                results = self._search_qdrant(collection, query, limit=limit, filters=filters)

        return results

    def _rrf_ranker(self, group_results, limit: int, k: int = 20):
        """
        Combine search results using Reciprocal Rank Fusion (RRF)
        :param group_results: A list of result lists from different searches
        :param k: The constant k in the RRF formula
        :return: A combined list of results with updated scores
        """
        combined_scores = {}
        doc_map = {}
        for results in group_results:
            for rank, result in enumerate(results):
                doc_id = result["_id"]
                if doc_id not in combined_scores:
                    combined_scores[doc_id] = 0
                    doc_map[doc_id] = result
                combined_scores[doc_id] += 1 / (k + rank + 1)

        # Sort combined results by their RRF scores in descending order
        ranked_results = sorted(combined_scores.items(), key=lambda item: item[1], reverse=True)

        reranked_results = []
        for doc_id, rrf_score in ranked_results:
            document = doc_map[doc_id]
            document["_rff_score"] = rrf_score
            reranked_results.append(document)

        return reranked_results[:limit]

    #
    # Elasticsearch related methods
    #
    def _search_es(
        self,
        collection: str,
        query: str,
        limit: int,
        filters: dict | None = None,
        hybrid_limit_factor: float = 1.5,
    ) -> list[dict]:
        index = collate_ix_name(collection, ELASTICSEARCH_IX_VER)
        client = Elasticsearch(self.config.es_url, basic_auth=self.config.es_creds)

        # No ranking filters
        must_not_filter = []
        should_filter = []
        query_filter = []
        filters = filters if filters else {}
        if filters.get("institution"):
            query_filter.append({"term": {"intitule_typologie_1.keyword": filters["institution"]}})
        if filters.get("sources"):
            query_filter.append({"terms": {"source.keyword": filters["sources"]}})
        if filters.get("should_sids"):
            should_filter.append({"ids": {"values": filters["should_sids"], "boost": 100}})
        if filters.get("must_not_sids"):
            must_not_filter.append({"ids": {"values": filters["must_not_sids"]}})

        # Lexical search
        fuzziness = {}
        if len(query.split()) < 25:
            fuzziness =  {"fuzziness": "AUTO"}
        lexical_query = {
            "multi_match": {
                "query": query,
                "type": "best_fields",
                "tie_breaker": 0.3,
                **fuzziness
            }
        }

        lexical_query = {
            "bool": {
                "must": [lexical_query],
                "must_not": must_not_filter,
                "should": should_filter,
                "filter": query_filter,
            }
        }

        if collection not in self.config.hybrid_collections:
            body = {"query": lexical_query, "size": limit}
            res = client.search(index=index, body=body)
            hits = [x.get("_source") for x in res["hits"]["hits"] if x]
            return hits

        # Semantic search
        embedding = LlmClient.create_embeddings(query)
        semantic_query = {
            "field": "embedding",
            "query_vector": embedding,
            "k": int(limit * hybrid_limit_factor),
            "num_candidates": 200,
            "filter": query_filter,
        }

        # RRF is not available in the free license.
        # body = {
        #    "query": lexical_query,
        #    "knn": semantic_query,
        #     "rank": {"rrf": {}},
        #    "size": limit,
        #    "_source": {"excludes": ["embedding"]},
        # }
        # res = client.search(index=index, body=body)
        # hits = [x.get("_source") for x in res["hits"]["hits"] if x]
        hits = self._hybrid_search_es(
            index, lexical_query, semantic_query, limit, hybrid_limit_factor
        )

        return hits

    def _hybrid_search_es(
        self, index, lexical_query, semantic_query, limit: int, hybrid_limit_factor: float
    ):
        # See also: https://elasticsearch-py.readthedocs.io/en/v8.14.0/async.html
        with ThreadPoolExecutor(max_workers=2) as executor:
            lexical_query_body = {
                "query": lexical_query,
                "size": int(limit * hybrid_limit_factor),
                "_source": {"excludes": ["embedding"]},
            }
            semantic_query_body = {
                "knn": semantic_query,
                "size": int(limit * hybrid_limit_factor),
                "_source": {"excludes": ["embedding"]},
            }

            lexical_future = executor.submit(self._search_lowlevel_es, index, lexical_query_body)
            semantic_future = executor.submit(self._search_lowlevel_es, index, semantic_query_body)

            lexical_results = [x for x in lexical_future.result()["hits"]["hits"] if x]
            semantic_results = [x for x in semantic_future.result()["hits"]["hits"] if x]

        results = self._rrf_ranker([lexical_results, semantic_results], limit=limit)
        hits = [x.get("_source") for x in results]
        return hits

    def _search_lowlevel_es(self, index, query):
        client = Elasticsearch(self.config.es_url, basic_auth=self.config.es_creds)
        return client.search(index=index, body=query)

    #
    # Qdrant related methods
    #

    def _search_qdrant(self, collection: str, query: str, limit: int, **kwargs) -> list[dict]:
        raise NotImplementedError
