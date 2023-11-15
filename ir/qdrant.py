import hashlib
import json

import numpy as np
from qdrant_client import QdrantClient, models

try:
    from app.config import QDRANT_IX_VER, collate_ix_name
except ModuleNotFoundError as e:
    from api.app.config import QDRANT_IX_VER, collate_ix_name


def get_unique_color(string):
    if not string:
        return None
    color = hashlib.sha256(string.encode()).hexdigest()[:6]
    return "#" + color


def create_vector_index(index_name, add_doc=True):
    # For quick testing/prototyping
    # client = QdrantClient(":memory:")  # or QdrantClient(path="path/to/db")
    client = QdrantClient(url="http://localhost:6333", grpc_port=6334, prefer_grpc=True)

    collection_name = collate_ix_name(index_name, QDRANT_IX_VER)

    if index_name == "experiences":
        # Load data
        embeddings = np.load("_data/embeddings/e5-large/embeddings_e5_experiences.npy")
        with open("_data/export-expa-c-riences.json") as f:
            documents = json.load(f)

        # Create collection
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
        embeddings = np.load("_data/embeddings/e5-large/embeddings_e5_chunks.npy")
        with open("_data/xmlfiles_as_chunks.json") as f:
            documents = json.load(f)

        # Create collection
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
                    # payload={"color": "red", "rand_number": idx % 10}
                )
                for i, vector in enumerate(embeddings)
            ],
        )

    else:
        raise NotImplementedError("Index unknown")
