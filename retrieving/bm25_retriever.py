import json
from typing import Union, List
from typing_extensions import TypedDict

from rank_bm25 import BM25Okapi

from .retrieving import ContextRetriever

from .params import JSON_DATABASE


class SearchResult(TypedDict):
    doc_id: int
    score: float
    text: str
    filename: str
    url: str
    title: str


def bm25_retrieval(question: str, json_file: str, top_k: Union[int, None] = 3, model=BM25Okapi) -> List[SearchResult]:
    # Load law documents from JSON file
    with open(json_file, "r", encoding="utf-8") as data_file:
        law_documents = json.load(data_file)

    # Preprocess documents
    documents = [doc["text"].split() for doc in law_documents]

    # Create BM25 model
    bm25 = model(documents)

    # Preprocess query
    query = question.split()

    # Get BM25 scores for documents
    scores = bm25.get_scores(query)

    # Sort documents based on scores
    sorted_docs = sorted(enumerate(scores), key=lambda item: -item[1])

    # Retrieve the best documents
    results = []
    for doc_index, score in sorted_docs[:top_k]:
        document = law_documents[doc_index]
        result: SearchResult = {
            "doc_id": doc_index,
            "score": score,
            "text": document["text"],
            "filename": document["file"],
            "url": document["xml_url"],
            "title": document["title"],
        }
        results.append(result)

    return results


class BM25Retriever(ContextRetriever):
    def __init__(self, json_database: str = JSON_DATABASE):
        self.database = json_database

    def retrieve_contexts(self, question: str, n_contexts: int) -> List[SearchResult]:
        return bm25_retrieval(question, self.database, top_k=n_contexts, model=BM25Okapi)
