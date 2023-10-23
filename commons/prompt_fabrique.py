from commons.embeddings import embed
from commons.prompt_base import Prompter
from commons.search_engines import semantic_search


class FabriquePrompter(Prompter):
    URL = "http://127.0.0.1:8081"
    SAMPLING_PARAMS = {
        "max_tokens": 500,
        "temperature": 0.2,
    }

    @staticmethod
    def make_prompt(experience=None, institution=None, context=None, links=None, **kwargs):
        institution_ = institution + " " if institution else ""
        prompt = f"Question soumise au service {institution_}: {experience}\n"
        if context and links:
            prompt += f"Prompt : {context} {links}\n"
        elif context:
            prompt += f"Prompt : {context}\n"
        elif links:
            prompt += f"Prompt : {links}\n"

        prompt += "---Réponse : "
        return prompt


class FabriqueReferencePrompter(Prompter):
    URL = "http://127.0.0.1:8081"
    # SAMPLING_PARAMS depends of {mode} here...

    def __init__(self, mode="simple"):
        super().__init__(mode)
        if self.mode == "simple":
            self.sampling_params = {
                "max_tokens": 500,
                "temperature": 0.2,
            }
        elif self.mode in ["experience", "expert"]:
            self.sampling_params = {
                "max_tokens": 4096,
                "temperature": 0.2,
                "top_p": 0.95,
            }
        else:
            raise ValueError("prompt mode unknown: %s" % self.mode)

    def make_prompt(self, **kwargs):
        if self.mode == "simple":
            return self._make_prompt_simple(**kwargs)
        elif self.mode == "experience":
            return self._make_prompt_experience(**kwargs)
        elif self.mode == "expert":
            return self._make_prompt_expert(**kwargs)
        else:
            raise ValueError("prompt mode unknown: %s" % self.mode)

    @staticmethod
    def _make_prompt_simple(experience=None, institution=None, context=None, links=None, **kwargs):
        institution_ = institution + " " if institution else ""
        prompt = []
        prompt.append("Mode simple")
        prompt.append(f"Question soumise au service {institution_}: {experience}")
        if context and links:
            prompt.append(f"Prompt : {context} {links}")
        elif context:
            prompt.append(f"Prompt : {context}")
        elif links:
            prompt.append(f"Prompt : {links}")

        prompt.append("###Réponse : \n")
        prompt = "\n\n".join(prompt)
        return prompt

    def _make_prompt_experience(
        self,
        experience=None,
        institution=None,
        context=None,
        links=None,
        limit=1,
        skip_first=False,
        **kwargs,
    ):
        institution_ = institution + " " if institution else ""
        prompt = []
        prompt.append("Mode expérience")
        prompt.append(f"Question soumise au service {institution_} : {experience}")

        # Rag / similar experiences
        limit = 1 if limit is None else limit
        if skip_first:
            limit += 1
        must_filters = None
        if institution:
            must_filters = {"intitule_typologie_1": institution}
        hits = semantic_search(
            "experiences",
            embed(experience),
            retrieves=["id_experience", "description"],
            must_filters=must_filters,
            limit=limit,
        )
        if skip_first:
            hits = hits[1:]
        self.sources = [x["id_experience"] for x in hits]
        chunks = [f'{x["id_experience"]} : {x["description"]}' for x in hits]
        chunks = "\n\n".join(chunks)
        prompt.append(f"Expériences :\n\n {chunks}")

        prompt.append("###Réponse : \n")
        prompt = "\n\n".join(prompt)
        return prompt

    def _make_prompt_expert(
        self,
        experience=None,
        institution=None,
        context=None,
        links=None,
        limit=3,
        skip_first=False,
        **kwargs,
    ):
        prompt = []
        prompt.append("Mode expert")
        prompt.append(f"Experience : {experience}")

        vector = embed(experience)
        # Get a reponse...
        # --
        # Using LLM
        # rep1 = vllm_generate(prompt, streaming=False,  max_tokens=500, **FabriquePrompter.SAMPLING_PARAMS)
        # rep1 = "".join(rep1)
        # Using similar experience
        n_exp = 1
        if skip_first:
            n_exp = 2
        must_filters = None
        if institution:
            must_filters = {"intitule_typologie_1": institution}
        hits = semantic_search(
            "experiences",
            vector,
            retrieves=["id_experience", "description"],
            must_filters=must_filters,
            limit=n_exp,
        )
        if skip_first:
            hits = hits[1:]
        rep1 = hits[0]["description"]
        # --
        prompt.append(f"Réponse :\n\n {rep1}")

        # Rag / relevant sheets
        limit = 3 if limit is None else limit
        hits = semantic_search(
            "chunks",
            vector,
            retrieves=["title", "url", "text", "context"],
            must_filters=None,
            limit=limit,
        )
        chunks = [
            f'{x["url"]} : {x["title"] + (x["context"]) if x["context"] else ""}\n{x["text"]}'
            for x in hits
        ]
        chunks = "\n\n".join(chunks)
        prompt.append(f"Fiches :\n\n {chunks}")

        prompt.append("###Réponse : \n")
        prompt = "\n\n".join(prompt)
        return prompt
