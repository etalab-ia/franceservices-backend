from abc import ABC, abstractmethod


class ContextRetriever(ABC):
    @abstractmethod
    def retrieve_contexts(self, question: str, n_contexts: int) -> list:
        pass

    def print_retrieving_infos(
        self, contexts: list[dict], keys_to_log: list[str]
    ) -> None:
        for index, context in enumerate(contexts):
            print(f"--- Context {index + 1} / {len(contexts)} ---")
            for key in keys_to_log:
                print(f"    - {key}: {context[key]}")
