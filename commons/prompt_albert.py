from commons.embeddings import embed
from commons.prompt_base import Prompter, format_llama_chat_prompt
from commons.search_engines import semantic_search


# WIP
class AlbertLightPrompter(Prompter):
    URL = "http://127.0.0.1:8082"
    SAMPLING_PARAMS = {
        "max_tokens": 2048,
        "temperature": 0.3,
    }

    def __init__(self, mode="simple"):
        super().__init__(mode)

        # Default mode is RAG !
        if not self.mode:
            self.mode = "rag"

    def make_prompt(self, llama_chat=True, **kwargs):
        if self.mode == "rag":
            prompt = self._make_prompt_rag(**kwargs)
        else:  # simple
            prompt = self._make_prompt_simple(**kwargs)

        if llama_chat:
            return format_llama_chat_prompt(prompt)["text"]

        return prompt

    def _make_prompt_simple(self, query=None, **kwargs):
        return query

    def _make_prompt_rag(self, query=None, limit=4, **kwargs):
        prompt = []
        prompt.append(
            "Utilisez les éléments de contexte à votre disposition ci-dessous pour répondre à la question finale. Si vous ne connaissez pas la réponse, dites simplement que vous ne savez pas, n'essayez pas d'inventer une réponse."
        )

        # Rag
        limit = 4 if limit is None else limit
        hits = semantic_search(
            "chunks",
            embed(query),
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

        prompt.append(f"Question : {query}")
        prompt = "\n\n".join(prompt)

        if len(prompt.split()) * 1.25 > 3 / 4 * self.SAMPLING_PARAMS["max_tokens"]:
            return self._make_prompt_rag(query, limit=limit - 1, **kwargs)

        return prompt
