import re
from abc import ABC, abstractmethod
from typing import Generator

from tqdm import tqdm

from pyalbert.clients import LlmClient


class CorpusHandler(ABC):
    def __init__(self, name, corpus):
        self._name = name
        self._corpus = corpus

    @classmethod
    def create_handler(cls, corpus_name: str, corpus:list[dict]) -> "CorpusHandler":
        """Get the appropriate handler subclass from the string corpus name."""
        corpuses = {
            "spp_experiences": SppExperiencesHandler,
            "chunks": SheetChunksHandler,
        }
        if corpus_name not in corpuses:
            raise ValueError(f"Corpus '{corpus_name}' is not recognized")
        return corpuses[corpus_name](corpus_name, corpus)

    def iter_docs(self, batch_size: int, desc: str = None) -> Generator[list, None, None]:
        if not desc:
            desc = f"Processing corpus: {self._name}..."

        corpus = self._corpus
        num_chunks = len(corpus) // batch_size
        if len(corpus) % batch_size != 0:
            num_chunks += 1

        for i in tqdm(range(num_chunks), desc=desc):
            start_idx = i * batch_size
            end_idx = min(start_idx + batch_size, len(corpus))
            yield corpus[start_idx:end_idx]

    def iter_docs_embeddings(self, batch_size: int) -> Generator[tuple[list], None, None]:
        desc = f"Processing corpus {self._name} with embeddings..."
        for batch in self.iter_docs(batch_size=batch_size, desc=desc):
            batch_embeddings = embed([self.doc_to_chunk(x) for x in batch])
            if len([x for x in batch_embeddings if x is not None]) == 0:
                continue
            yield batch, batch_embeddings

    @abstractmethod
    def doc_to_chunk(self, doc: dict) -> str:
        raise NotImplementedError("Subclasses should implement this!")


class SppExperiencesHandler(CorpusHandler):
    def doc_to_chunk(self, doc: dict) -> str | None:
        text = doc["reponse_structure_1"]
        if not text:
            return None
        # Clean some text garbage
        # --
        # Define regular expression pattern to match non-breaking spaces:
        # - \xa0 for Latin-1 (as a raw string)
        # - \u00a0 for Unicode non-breaking space
        # - \r carriage return
        # - &nbsp; html non breaking space
        text = re.sub(r"[\xa0\u00a0\r]", " ", text)
        text = re.sub(r"&nbsp;", " ", text)

        # Add a space after the first "," if not already followed by a space.
        text = re.sub(r"\,(?!\s)", ". ", text, count=1)
        return text


class SheetChunksHandler(CorpusHandler):
    def doc_to_chunk(self, doc: dict) -> str | None:
        context = ""
        if "context" in doc:
            context = "  (" " > ".join(doc["context"]) + ")"

        text = "\n".join([doc["title"] + context, doc["introduction"], doc["text"]])
        return text


def embed(data: None | str | list[str]) -> None | list:
    if data is None:
        return None

    if isinstance(data, list):
        # Keep track of None positions
        indices_of_none = [i for i, x in enumerate(data) if x is None]
        filtered_data = [x for x in data if x is not None]
        if not filtered_data:
            return [None] * len(data)

        # Apply the original function on filtered data
        try:
            embeddings = LlmClient.create_embeddings(filtered_data)
        except Exception as err:
            print(filtered_data)
            raise err

        # Reinsert None at their original positions in reverse order
        for index in reversed(indices_of_none):
            embeddings.insert(index, None)

        return embeddings

    # Fall back to single data input
    return LlmClient.create_embeddings(data)
