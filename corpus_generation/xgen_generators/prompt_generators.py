from ..prompt_generation import PromptGenerator


class XGenPromptGenerator(PromptGenerator):
    def create_context_text(self, contexts: list[str]) -> str:
        texts_for_context = [f"référence {index} : {context}" for index, context in enumerate(contexts)]
        return "\n\n".join(texts_for_context)

    def create_prompt_messages(self, question: str, contexts: list[str]) -> str:
        contexts = self.choose_contexts_based_on_lenght(contexts)
        contexts_text = self.create_context_text(contexts)
        prompt = (
            "Voici plusieurs références sur un même thème :\n\n"
            ">>REFERENCES<<\n"
            f"{contexts_text}\n\n"
            ">>INSTRUCTION<<\n"
            "Tu es un agent de l'état français. Tu es chargé d'informer "
            "ton interlocuteur sur sa question et lui proposer des démarches à suivre. "
            "Aide-toi des informations des références, mais réponds comme "
            "s'il n'y avait pas de références. "
            "Si les références ne permettent pas répondre, "
            "réponds: 'Désolé, je ne peux pas répondre à la question'."
            "Parle à la 3ème personne du singulier sans mentionner que tu es "
            "un agent de l'état."
            "Tu dois répondre à la question suivante :\n\n"
            ">>QUESTION<<\n"
            f"{question}"
        )
        return prompt

    def choose_contexts_based_on_lenght(self, contexts: list[str]) -> list[str]:
        contexts = sorted(contexts, key=self.count_tokens, reverse=True)
        while self.count_tokens(contexts) > self.prompt_token_limit:
            contexts.pop(0)
        return contexts
