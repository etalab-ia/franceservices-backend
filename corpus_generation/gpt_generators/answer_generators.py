import openai

from ..llm_generation import AnswerQuestionGenerator


class GPTAnswerGenerator(AnswerQuestionGenerator):
    def get_answer(self, question: str, contexts: list[str]) -> str:
        messages = self.prompt_generator.create_prompt_messages(question, contexts)
        print(f"prompting GPT with question: {question}...")
        response = self.prompt_openai_api(messages, retry_on_fail=True)
        return response["choices"][0]["message"]["content"]

    def prompt_openai_api(
        self, messages: list[dict], retry_on_fail: bool = True
    ) -> dict:
        if not retry_on_fail:
            return openai.ChatCompletion.create(
                model=self.model_name, messages=messages
            )

        retry = True
        while retry:
            try:
                response = openai.ChatCompletion.create(
                    model=self.model_name, messages=messages
                )
                retry = False
            except Exception as error:  # pylint: disable=broad-except
                print(error)
                print("retrying query...")
        return response
