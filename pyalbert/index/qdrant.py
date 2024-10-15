import hashlib
import re

from qdrant_client import QdrantClient, models

from pyalbert import collate_ix_name
from pyalbert.config import (
    QDRANT_GRPC_PORT,
    QDRANT_IX_VER,
    QDRANT_REST_PORT,
    QDRANT_URL,
    QDRANT_USE_GRPC,
)
from pyalbert.corpus import load_exeriences, load_sheet_chunks

from .commons import CorpusHandler, embed


def get_unique_color(string):
    if not string:
        return None
    color = hashlib.sha256(string.encode()).hexdigest()[:6]
    return "#" + color


def create_qdrant_index(
    index_name, add_doc=True, recreate=False, batch_size=None, storage_dir=None
):
    """Add vector to qdrant collection.
    The payload, if present is useful to get back a data and filter a search.
    """
    batch_size = batch_size if batch_size else 16
    probe_vector = embed("Hey, I'am a probe")
    embedding_size = len(probe_vector)

    # For quick testing/prototyping
    # client = QdrantClient(":memory:")  # or QdrantClient(path="path/to/db")
    client = QdrantClient(url=QDRANT_URL, port=QDRANT_REST_PORT, grpc_port=QDRANT_GRPC_PORT, prefer_grpc=QDRANT_USE_GRPC)  # fmt: skip
    collection_name = collate_ix_name(index_name, QDRANT_IX_VER)

    if index_name == "spp_experiences":
        meta_data = [
            "reponse_structure_1",
            "intitule_typologie_1",
            "ressenti_usager",
        ]

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

        corpus_handler = CorpusHandler.create_handler(index_name, documents)
        for batch_documents, batch_embeddings in corpus_handler.iter_docs_embeddings(batch_size):
            client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=batch_documents[j]["id_experience"],
                        vector=batch_embeddings[j],
                        payload={k: batch_documents[j][k] for k in meta_data},
                    )
                    for j in range(len(batch_documents))
                    if batch_embeddings[j]
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

        corpus_handler = CorpusHandler.create_handler(index_name, documents)
        for batch_documents, batch_embeddings in corpus_handler.iter_docs_embeddings(batch_size):
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
                    if batch_embeddings[j]
                ],
            )

    else:
        raise NotImplementedError("Index unknown")


def list_qdrant_collections():
    """List and show information about Qdrant collections."""
    client = QdrantClient(url=QDRANT_URL, port=QDRANT_REST_PORT, grpc_port=QDRANT_GRPC_PORT, prefer_grpc=QDRANT_USE_GRPC)  # fmt: skip
    collections = client.get_collections()

    if not collections.collections:
        print("No collections found in Qdrant.")
        return

    print("=" * 80)
    print("QDRANT COLLECTIONS INFORMATION (%s)" % (QDRANT_URL))
    print("=" * 80)

    # Print header
    print(
        "{:<20} {:<15} {:<15} {:<15}".format(
            "Collection Name",
            "Points Count",
            "Segments Count",
            "Optimizers Status",
        )
    )
    print("-" * 80)

    # Print collection information
    for collection in collections.collections:
        collection_info = client.get_collection(collection.name)

        points_count = collection_info.points_count
        segments_count = collection_info.segments_count
        optimizer_status = "Active" if collection_info.optimizer_status else "Inactive"

        print(
            "{:<20} {:<15} {:<15} {:<15}".format(
                collection.name, points_count, segments_count, optimizer_status
            )
        )

    print("-" * 80)
    print(f"Total collections: {len(collections.collections)}")
    print()
