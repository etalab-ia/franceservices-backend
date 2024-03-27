#!/bin/python
import sys

sys.path.append(".")

from pprint import pprint

from pyalbert.clients import AlbertClient


client = AlbertClient()
hits = client.search("chunks", "carte d'indentité", limit=3, similarity="bm25")
pprint(hits)

# KEEP IT FOR FURTHER (Qdrant) test..
# --
# client = QdrantClient( url=QDRANT_URL, port=QDRANT_REST_PORT, grpc_port=QDRANT_GRPC_PORT, prefer_grpc=QDRANT_USE_GRPC) # fmt: off
# collection_name = collate_ix_name(index_name, QDRANT_IX_VER)
# client.get_collection(collection_name)
# hits = client.search(collection_name=collection_name, query_vector=embeddings[0], limit=3)

# print(
#     f"""
#       question: {documents[0]["id_experience"]}
#       experience: {documents[0]["description"]}
#       """
# )
# documents = {doc["id_experience"]: doc for doc in documents}
# for h in hits:
#     doc = documents[h.id]
#     print(doc["id_experience"])
#     print(doc["titre"])
#     print(doc["description"])
