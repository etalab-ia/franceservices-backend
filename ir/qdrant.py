import hashlib
import json
import os

import numpy as np
from qdrant_client import QdrantClient, models

try:
    from app.config import (EMBEDDING_BOOTSTRAP_PATH, QDRANT_IX_VER,
                            collate_ix_name)
except ModuleNotFoundError as e:
    from api.app.config import (EMBEDDING_BOOTSTRAP_PATH, QDRANT_IX_VER,
                                collate_ix_name)


def get_unique_color(string):
    if not string:
        return None
    color = hashlib.sha256(string.encode()).hexdigest()[:6]
    return "#" + color


def create_vector_index(index_name, add_doc=True, recreate=False):
    """Add vector to qdrant collection.
    The payload, if present is useful to get back a data and filter a search.
    """
    # For quick testing/prototyping
    # client = QdrantClient(":memory:")  # or QdrantClient(path="path/to/db")
    client = QdrantClient(url="http://localhost:6333", grpc_port=6334, prefer_grpc=True)

    collection_name = collate_ix_name(index_name, QDRANT_IX_VER)

    if index_name == "experiences":
        # Load data
        embeddings = np.load(os.path.join(EMBEDDING_BOOTSTRAP_PATH, "embeddings_experiences.npy"))
        with open("_data/export-expa-c-riences.json") as f:
            documents = json.load(f)

        # Get or reCreate collection
        try:
            if recreate:
                raise Exception
            client.get_collection(collection_name)
        except Exception:
            client.recreate_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embeddings.shape[1], distance=models.Distance.COSINE
                ),
            )

        client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=documents[i]["id_experience"],
                    vector=vector.tolist(),
                    payload={
                        "intitule_typologie_1": documents[i]["intitule_typologie_1"],
                        "feeling": documents[i]["ressenti_usager"],
                    },
                )
                for i, vector in enumerate(embeddings)
            ],
        )

        # Test
        hits = client.search(collection_name=collection_name, query_vector=embeddings[0], limit=3)

        print(
            f"""
              question: {documents[0]["id_experience"]}
              experience: {documents[0]["description"]}
              """
        )
        documents = {doc["id_experience"]: doc for doc in documents}
        for h in hits:
            doc = documents[h.id]
            print(doc["id_experience"])
            print(doc["titre"])
            print(doc["description"])

    # elif index_name == "sheets":
    elif index_name == "chunks":
        # Load data
        embeddings = np.load(os.path.join(EMBEDDING_BOOTSTRAP_PATH, "embeddings_chunks.npy"))
        with open("_data/sheets_as_chunks.json") as f:
            documents = json.load(f)

        # Get or reCreate collection
        try:
            if recreate:
                raise Exception
            client.get_collection(collection_name)
        except Exception:
            client.recreate_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embeddings.shape[1], distance=models.Distance.COSINE
                ),
            )

        client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=documents[i]["hash"].encode("utf8").hex(),
                    vector=vector.tolist(),
                    payload={
                        "source": documents[i]["source"],
                        "sid": documents[i]["sid"],
                        # "color": "red", "rand_number": idx % 10,
                    },
                )
                for i, vector in enumerate(embeddings)
            ],
        )

    else:
        raise NotImplementedError("Index unknown")
