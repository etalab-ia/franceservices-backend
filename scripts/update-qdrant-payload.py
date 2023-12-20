#!/usr/bin/env python

import json

from qdrant_client import QdrantClient, models

try:
    from app.config import (EMBEDDING_BOOTSTRAP_PATH, QDRANT_IX_VER,
                            collate_ix_name)
except ModuleNotFoundError as e:
    from api.app.config import (EMBEDDING_BOOTSTRAP_PATH, QDRANT_IX_VER,
                                collate_ix_name)

if __name__ == "__main__":
    client = QdrantClient(url="http://localhost:6333", grpc_port=6334, prefer_grpc=True)

    index_name = "chunks"
    collection_name = collate_ix_name(index_name, QDRANT_IX_VER)

    with open("_data/sheets_as_chunks.json") as f:
        documents = json.load(f)

    ## UPDATE A FIELD
    for i, doc in enumerate(documents):
        client.set_payload(
            collection_name=collection_name,
            payload={
                "sid": doc["sid"],
            },
            points=[i],
        )
