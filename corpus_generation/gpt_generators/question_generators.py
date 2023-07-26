import openai


from ..llm_generation import QuestionGenerator


class GPTQuestionGenerator(QuestionGenerator):
    def get_keywords(self, contexts):
        # Génération des mots-clés nécessaires à la génération des questions.

        first_prompt = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {"role": "system", "content": "Tu es un agent de l'état français"},
                {
                    "role": "user",
                    "content": f"Voici plusieurs textes sur un même thème:{str(contexts)}\n"
                    + "Donne moi tous les mots clés de ces textes sous la forme d'une liste.\n"
                    + "Voici les mots-clés :",
                },
            ],
        )

        return first_prompt["choices"][0]["message"]["content"]  # List(str) des mots-clés

        # Prompt pour la génération de questions

    def get_question(self, contexts, questions_nb):
        # Génération des mots-clés nécessaires à la génération des questions.

        retry = True
        while retry:
            try:
                keyword = self.get_keywords(contexts)
                retry = False
            except Exception as error:
                print(error)
                print("retrying keyword query...")

        # Prompt pour la génération de questions

        messages = [
            {"role": "system", "content": "Tu es un agent de l'état français"},
            {
                "role": "user",
                "content": f"Voici une liste de mots-clés :{str(keyword)}\n"
                + f"Génère {questions_nb} questions en lien avec les mots-clés sous la forme d'une liste.\n"
                + "Numérote les questions. Voici les questions :",
            },
        ]
        return self.prompt_openai_api(messages, retry_on_fail=True)  # Liste numérotée des questions générées

    def prompt_openai_api(self, messages: list[dict], retry_on_fail: bool = True) -> dict:
        if not retry_on_fail:
            return openai.ChatCompletion.create(model=self.model_name, messages=messages)

        retry = True
        while retry:
            try:
                response = openai.ChatCompletion.create(model=self.model_name, messages=messages)
                retry = False
            except Exception as error:
                print(error)
                print("retrying query...")
        return response["choices"][0]["message"]["content"]


class GPTQuestionReformulation(QuestionGenerator):
    def create_context_text(self, contexts) -> str:
        contexts_text = ""
        for index, context in enumerate(contexts):
            contexts_text += f"{index}. {context}\n\n"
        return contexts_text

    def get_question(self, question):
        context = self.create_context_text(question)

        messages = [
            {
                "role": "user",
                "content": f"Voici une question  : {context}. "
                + "Je veux une liste numérotée des questions que tu vas générer. Il faut que tu me génères 2 questions à la première personne et 2 avec un langage familier."
                + "Numérote les questions. Voici les 4 questions :",
            }
        ]

        return self.prompt_openai_api(messages, retry_on_fail=True)

    def prompt_openai_api(self, messages: list[dict], retry_on_fail: bool = True) -> dict:
        if not retry_on_fail:
            return openai.ChatCompletion.create(model=self.model_name, messages=messages)

        retry = True
        while retry:
            try:
                response = openai.ChatCompletion.create(model=self.model_name, messages=messages)
                retry = False
            except Exception as error:  # pylint: disable=broad-except
                print(error)
                print("retrying query...")
        return response["choices"][0]["message"]["content"]
