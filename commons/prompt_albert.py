from elasticsearch import Elasticsearch
from qdrant_client import QdrantClient
from qdrant_client import models as QdrantModels

from commons import get_embedding_e5
from commons.prompt_base import Prompter


def embed(text: str) -> list:
    return get_embedding_e5(text)


class AlbertLightPrompter(Prompter):
    URL = "@TODO"
    SAMPLING_PARAMS = {
        "max_tokens": 4096,
        "temperature": 0.5,
    }
    @staticmethod
    def make_prompt(question=None):
        prompt = "todo"
        return prompt
