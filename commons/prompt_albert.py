from elasticsearch import Elasticsearch
from qdrant_client import QdrantClient
from qdrant_client import models as QdrantModels

from commons import get_embedding_e5
from commons.prompt_base import Prompter
from commons.search_engines import semantic_search


def embed(text: str) -> list:
    return get_embedding_e5(text)


# WIP
class AlbertLightPrompter(Prompter):
    URL = "@TODO"
    SAMPLING_PARAMS = {
        "max_tokens": 4096,
        "temperature": 0.5,
    }

    def make_prompt(self, question=None, limit=3):
        prompt = []
        prompt.append(
            "Utilisez les éléments de contexte suivants pour répondre à la question finale. Si vous ne connaissez pas la réponse, dites simplement que vous ne savez pas, n'essayez pas d'inventer une réponse."
        )

        # Rag
        hits = semantic_search(
            "chunks",
            embed(question),
            retrieves=["title", "url", "text", "context"],
            must_filters=None,
            limit=limit,
        )
        self.sources = [x["url"] for x in hits]
        if len(hits) == 3:
            # LLM Lost in the middle
            hits[1], hits[2] = hits[2], hits[1]
        chunks = [
            f'{x["url"]} : {x["title"] + (x["context"]) if x["context"] else ""}\n{x["text"]}'
            for x in hits
        ]
        chunks = "\n\n".join(chunks)
        prompt.append(f"{chunks}")

        prompt.append(f"Question : {question}")
        prompt = "\n\n".join(prompt)
        return prompt
