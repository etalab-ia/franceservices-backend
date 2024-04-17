import hashlib

from qdrant_client import QdrantClient, models

from pyalbert import collate_ix_name
from pyalbert.clients import LlmClient
from pyalbert.config import (
    QDRANT_GRPC_PORT,
    QDRANT_IX_VER,
    QDRANT_REST_PORT,
    QDRANT_URL,
    QDRANT_USE_GRPC,
)
from pyalbert.corpus import load_exeriences, load_sheet_chunks


def get_unique_color(string):
    if not string:
        return None
    color = hashlib.sha256(string.encode()).hexdigest()[:6]
    return "#" + color


def create_vector_index(index_name, add_doc=True, recreate=False, batch_size=10, storage_dir=None):
    """Add vector to qdrant collection.
    The payload, if present is useful to get back a data and filter a search.
    """
    embed = LlmClient.create_embeddings
    probe_vector = embed("Hey, I'am a probe")
    embedding_size = len(probe_vector)

    # For quick testing/prototyping
    # client = QdrantClient(":memory:")  # or QdrantClient(path="path/to/db")
    client = QdrantClient(url=QDRANT_URL, port=QDRANT_REST_PORT, grpc_port=QDRANT_GRPC_PORT, prefer_grpc=QDRANT_USE_GRPC)  # fmt: skip
    collection_name = collate_ix_name(index_name, QDRANT_IX_VER)

    if index_name == "experiences":
        # Load data
        documents = load_exeriences(storage_dir)

        # Get or reCreate collection
        try:
            if recreate:
                raise Exception
            client.get_collection(collection_name)
        except Exception:
            client.recreate_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size, distance=models.Distance.COSINE
                ),
            )

        def doc_to_text(doc):
            return doc["description"]

        current_pct = 0
        n = len(documents)
        for i in range(0, len(documents), batch_size):
            pct = (100 * i) // n
            if pct > current_pct:
                current_pct = pct
                print(f"Processing {index_name}: {current_pct}%\r", end="")

            batch_documents = documents[i : i + batch_size]
            batch_embeddings = embed([doc_to_text(x) for x in batch_documents])
            client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=batch_documents[j]["id_experience"],
                        vector=batch_embeddings[j],
                        payload={
                            "intitule_typologie_1": batch_documents[j]["intitule_typologie_1"],
                            "feeling": batch_documents[j]["ressenti_usager"],
                        },
                    )
                    for j in range(len(batch_documents))
                ],
            )

    elif index_name == "chunks":
        # Load data
        documents = load_sheet_chunks(storage_dir)

        # Get or reCreate collection
        try:
            if recreate:
                raise Exception
            client.get_collection(collection_name)
        except Exception:
            client.recreate_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size, distance=models.Distance.COSINE
                ),
            )

        def doc_to_text(doc):
            return "\n".join(
                [doc["title"], doc.get("context", ""), doc["introduction"], doc["text"]]
            )

        current_pct = 0
        n = len(documents)
        for i in range(0, len(documents), batch_size):
            pct = (100 * i) // n
            if pct > current_pct:
                current_pct = pct
                print(f"Processing {index_name}: {current_pct}%\r", end="")

            batch_documents = documents[i : i + batch_size]
            batch_embeddings = embed([doc_to_text(x) for x in batch_documents])
            client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=batch_documents[j]["hash"].encode("utf8").hex(),
                        vector=batch_embeddings[j],
                        payload={
                            "source": batch_documents[j]["source"],
                            "sid": batch_documents[j]["sid"],
                            # "color": get_unique_color(batch_documents[i]["surtitre"]),
                        },
                    )
                    for j in range(len(batch_documents))
                ],
            )

    else:
        raise NotImplementedError("Index unknown")
