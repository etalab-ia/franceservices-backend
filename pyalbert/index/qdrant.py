import hashlib
import re

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

def embed(data):
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


def create_vector_index(index_name, add_doc=True, recreate=False, batch_size=None, storage_dir=None):
    """Add vector to qdrant collection.
    The payload, if present is useful to get back a data and filter a search.
    """
    batch_size = batch_size if batch_size else 10
    probe_vector = embed("Hey, I'am a probe")
    embedding_size = len(probe_vector)

    # For quick testing/prototyping
    # client = QdrantClient(":memory:")  # or QdrantClient(path="path/to/db")
    client = QdrantClient(url=QDRANT_URL, port=QDRANT_REST_PORT, grpc_port=QDRANT_GRPC_PORT, prefer_grpc=QDRANT_USE_GRPC)  # fmt: skip
    collection_name = collate_ix_name(index_name, QDRANT_IX_VER)

    if index_name.startswith("spp"):
        meta_data = [
            "intitule_typologie_1",
            "ressenti_usager",
        ]

        if index_name == "spp_experience_question":
            indexed_field = "description"
        elif index_name == "spp_experience_answer":
            indexed_field = "reponse_structure_1"
        else:
            raise NotImplementedError("Index unknown")

        meta_data += [indexed_field]

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
            text = doc[indexed_field]
            if not text:
                return None
            # Clean some text garbage
            # --
            # Define regular expression pattern to match non-breaking spaces:
            # - \xa0 for Latin-1 (as a raw string)
            # - \u00a0 for Unicode non-breaking space
            # - \r carriage return
            # - &nbsp; html non breaking space
            text = re.sub(r'[\xa0\u00a0\r]', ' ', text)
            text = re.sub(r"&nbsp;", " ", text)

            # Add a space after the first "," if not already followed by a space.
            text = re.sub(r"\,(?!\s)", ". ", text, count=1)
            return text

        current_pct = 0
        n = len(documents)
        for i in range(0, len(documents), batch_size):
            pct = (100 * i) // n
            if pct > current_pct:
                current_pct = pct
                print(f"Processing {index_name}: {current_pct}%\r", end="", flush=True)

            batch_documents = documents[i : i + batch_size]
            batch_embeddings = embed([doc_to_text(x) for x in batch_documents])
            if len([x for x in batch_embeddings if x is not None]) == 0:
                continue

            client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=batch_documents[j]["id_experience"],
                        vector=batch_embeddings[j],
                        payload={k: batch_documents[j][k] for k in meta_data},
                    )
                    for j in range(len(batch_documents)) if batch_embeddings[j]
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
                print(f"Processing {index_name}: {current_pct}%\r", end="", flush=True)

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
