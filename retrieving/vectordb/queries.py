from typing import List, Optional

from vectordb.embedding import VectorEmbeddor


from .settings import WEAVIATE_CLIENT


def query_n_contexts(
    question, n_neighbors: int, embeddor: Optional[VectorEmbeddor] = None
) -> List[dict]:
    if not embeddor:
        contexts = (
            WEAVIATE_CLIENT.query.get(
                "Contexts",
                ["title", "theme", "content", "xml_url"],
            )
            .with_near_text({"concepts": [question]})
            .with_limit(n_neighbors)
            .do()
        )
        return contexts["data"]["Get"]["Contexts"]

    vector = embeddor.embed(question)
    contexts = (
        WEAVIATE_CLIENT.query.get(
            "Contexts",
            ["title", "theme", "content", "xml_url"],
        )
        .with_near_vector({"vector": vector})
        .with_limit(n_neighbors)
        .do()
    )
    return contexts["data"]["Get"]["Contexts"]


def get_all_xml_attribute(attribute: str, batch_size=20) -> List[str]:
    class_name = "Contexts"
    cursor = None

    def recursive_attributes_query(
        attributes: list[str], cursor: Optional[str], batch_size: int
    ) -> list[str]:
        query = (
            WEAVIATE_CLIENT.query.get(class_name, [attribute])
            .with_additional(["id"])
            .with_limit(batch_size)
        )

        if cursor is not None:
            result = query.with_after(cursor).do()
        else:
            result = query.do()
        # finished to parse db, returning the whole list
        if len(result["data"]["Get"][class_name]) == 0:
            return attributes

        # move the cursor to the next batch
        cursor = result["data"]["Get"][class_name][-1]["_additional"]["id"]
        attributes += [item[attribute] for item in result["data"]["Get"][class_name]]

        return recursive_attributes_query(attributes, cursor, batch_size)

    return recursive_attributes_query([], cursor, batch_size)
