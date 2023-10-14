from elasticsearch import Elasticsearch
from qdrant_client import QdrantClient
from qdrant_client import models as QdrantModels

from commons import get_embedding_e5
from commons.prompt_base import Prompter, format_llama_chat_prompt
from commons.search_engines import semantic_search


def embed(text: str) -> list:
    return get_embedding_e5(text)


# WIP
class AlbertLightPrompter(Prompter):
    URL = "@TODO"
    SAMPLING_PARAMS = {
        "max_tokens": 2048,
        "temperature": 0.3,
    }

    def __init__(self, mode="simple"):
        super().__init__(mode)

        # Default mode is RAG !
        if not self.mode:
            self.mode = "rag"

    def make_prompt(self, question=None, **kwargs):
        if self.mode == "rag":
            prompt = self._make_prompt_rag(question, **kwargs)
        else:  # simple
            prompt = self._make_prompt_simple(question, **kwargs)

        if "llama_chat" in kwargs:
            return format_llama_chat_prompt(prompt)["text"]

        return prompt

    def _make_prompt_simple(self, question=None, **kwargs):
        return question

    def _make_prompt_rag(self, question=None, limit=3, **kwargs):
        prompt = []
        prompt.append(
            "Utilisez les éléments de contexte à votre disposition ci-dessous pour répondre à la question finale. Si vous ne connaissez pas la réponse, dites simplement que vous ne savez pas, n'essayez pas d'inventer une réponse."
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
        # if len(hits) == 3:
        #    # LLM Lost in the middle
        #    hits[1], hits[2] = hits[2], hits[1]
        chunks = [
            f'{x["url"]} : {x["title"] + (" (" + x["context"] + ")") if x["context"] else ""}\n{x["text"]}'
            for x in hits
        ]
        chunks = "\n\n".join(chunks)
        prompt.append(f"{chunks}")

        prompt.append(f"Question : {question}")
        prompt = "\n\n".join(prompt)
        return prompt
