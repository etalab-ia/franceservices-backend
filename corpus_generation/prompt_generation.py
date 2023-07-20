from abc import ABC, abstractmethod
from typing import List, Union, Callable


class PromptGenerator(ABC):
    def __init__(
        self,
        token_counter_fn: Callable[[str], int],
        prompt_token_limit: int,
        model_name: str,
    ) -> None:
        self.model_name = model_name
        self.token_counter_fn = token_counter_fn
        self.prompt_token_limit = prompt_token_limit

    def count_tokens(self, contexts: Union[List[str], str]) -> int:
        if isinstance(contexts, str):
            return self.token_counter_fn(contexts)
        return sum(self.token_counter_fn(context) for context in contexts)

    @abstractmethod
    def create_prompt_messages(self, question: str, contexts: list[str]):
        pass

    @abstractmethod
    def choose_contexts_based_on_lenght(self, contexts: List[str]) -> List[str]:
        pass
