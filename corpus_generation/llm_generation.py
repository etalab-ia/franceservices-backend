from abc import ABC, abstractmethod

from .prompt_generation import PromptGenerator


class AnswerQuestionGenerator(ABC):
    def __init__(
        self,
        prompt_generator: PromptGenerator,
        model_name: str,
        max_new_tokens: int = 100,
        repetition_penalty: float = 1.2,
    ) -> None:
        self.prompt_generator = prompt_generator
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.repetition_penalty = repetition_penalty

    @abstractmethod
    def get_answer(self, question: str, contexts: list[str]) -> str:
        pass


class QuestionGenerator(ABC):
    def __init__(self, prompt_generator: PromptGenerator, model_name: str) -> None:
        self.prompt_generator = prompt_generator
        self.model_name = model_name

    @abstractmethod
    def get_question(self, theme: str, contexts: list[str]) -> str:
        pass
