from commons.api import get_legacy_client
from commons.prompt_base import Prompter, format_llama_chat_prompt


# WIP
class AlbertLightPrompter(Prompter):
    URL = "http://127.0.0.1:8082"
    SAMPLING_PARAMS = {
        "max_tokens": 2048,
        "temperature": 30,
    }

    def __init__(self, mode="simple"):
        super().__init__(mode)

        # Default mode is RAG !
        if not self.mode:
            self.mode = "rag"

    @classmethod
    def preprocess_prompt(cls, prompt: str) -> str:
        new_prompt = cls._expand_acronyms(prompt)
        return new_prompt

    def make_prompt(self, llama_chat=True, expand_acronyms=True, **kwargs):
        if expand_acronyms and "query" in kwargs:
            kwargs["query"] = self.preprocess_prompt(kwargs["query"])

        if self.mode == "rag":
            prompt = self._make_prompt_rag(**kwargs)
        else:  # simple
            prompt = self._make_prompt_simple(**kwargs)

        if llama_chat:
            return format_llama_chat_prompt(prompt)["text"]

        return prompt

    def _make_prompt_simple(self, query=None, **kwargs):
        return query

    def _make_prompt_rag(
        self, query=None, limit=4, sources=None, should_sids=None, must_not_sids=None, **kwargs
    ):
        prompt = []
        prompt.append(
            "Utilisez les éléments de contexte à votre disposition ci-dessous pour répondre à la question finale. Si vous ne connaissez pas la réponse, dites simplement que vous ne savez pas, n'essayez pas d'inventer une réponse."
        )

        # Rag
        client = get_legacy_client()
        limit = 4 if limit is None else limit
        hits = client.search(
            "chunks",
            query,
            limit=limit,
            similarity="e5",
            sources=sources,
            should_sids=should_sids,
            must_not_sids=must_not_sids,
        )
        self.sources = [x["url"] for x in hits]
        # if len(hits) == 3:
        #    # LLM Lost in the middle
        #    hits[1], hits[2] = hits[2], hits[1]
        chunks = [
            f'{x["url"]} : {x["title"] + (" (" + x["context"] + ")") if x["context"] else ""}\n{x["text"]}'
            for i, x in enumerate(hits)
        ]
        chunks = "\n\n".join(chunks)
        prompt.append(f"{chunks}")

        prompt.append(f"Question : {query}")
        prompt = "\n\n".join(prompt)

        if limit > 1 and len(prompt.split()) * 1.25 > 3 / 4 * self.SAMPLING_PARAMS["max_tokens"]:
            return self._make_prompt_rag(query, limit=limit - 1, **kwargs)

        return prompt
