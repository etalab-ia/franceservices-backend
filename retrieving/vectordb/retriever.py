from ..retrieving import ContextRetriever

from .client import get_weaviate_client
from .queries import query_n_contexts

from .embedding import CPUEmbeddor
from .populate import run_weaviate_migration


class WeaviateRetriever(ContextRetriever):
    def __init__(self):
        self.weaviate_client = get_weaviate_client()
        self.embeddor = CPUEmbeddor()

    def retrieve_contexts(self, question, n_contexts=3):
        return query_n_contexts(
            self.weaviate_client,
            question,
            n_contexts,
        )

    def run_weaviate_migration(self, xml_files_to_vectorize):
        run_weaviate_migration(
            self.weaviate_client,
            xml_files_to_vectorize,
            embeddor=self.embeddor,
        )
