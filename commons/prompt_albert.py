from elasticsearch import Elasticsearch
from qdrant_client import QdrantClient
from qdrant_client import models as QdrantModels

from commons import get_embedding_e5


def embed(text: str) -> list:
    return get_embedding_e5(text)


class AlbertLightPrompter:
    @staticmethod
    def make_prompt(question=None):
        prompt = "todo"
        return prompt
