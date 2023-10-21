from elasticsearch import Elasticsearch
from qdrant_client import QdrantClient
from qdrant_client import models as QdrantModels

# @IMPROVE: commons & app.config unification
try:
    from app.config import ELASTICSEARCH_CREDS, ELASTICSEARCH_URL, QDRANT_URL
except ModuleNotFoundError as e:
    from api.app.config import (ELASTICSEARCH_CREDS, ELASTICSEARCH_URL,
                                QDRANT_URL)


# Note: the only difference between this function and the one used in api/app/core/indexes.py
# is that the embedding here is built with an api called, while in the api, it actually compute the embedding.
# Both can be unified in the future is we use a dedicated api to compute embeddings.
def semantic_search(index_name, vector, retrieves=None, must_filters=None, limit=10):
    """Search best items in a vector database

    Params
    ---
    index_name: Name of the collection to search in.
    vector: a list representing an embedding.
    retrieves: list of features to extract
    must_filters: list of {key:value} filters the query must satisfy.
    limit: number of best hits to return

    Returns
    ---
    List of hits
    """

    if index_name not in ["experiences", "sheets", "chunks"]:
        raise ValueError("unknwon collection name")

    # For Sheets special case
    do_unique_sheets = False
    if index_name == "sheets":
        index_name = "chunks"
        limit = limit * 5
        do_unique_sheets = True

    client = QdrantClient(url=QDRANT_URL, grpc_port=6334, prefer_grpc=True)
    query_filter = None
    if must_filters:
        # Filter results
        query_filter = QdrantModels.Filter(
            must=[
                QdrantModels.FieldCondition(
                    key=k,
                    match=QdrantModels.MatchValue(
                        value=v,
                    ),
                )
                for k, v in must_filters.items()
            ]
        )
    res = client.search(
        collection_name=index_name,
        query_vector=vector,
        query_filter=query_filter,
        limit=limit,
    )

    es = Elasticsearch(ELASTICSEARCH_URL, basic_auth=ELASTICSEARCH_CREDS)
    # @Debug : qdrant doesnt accept the hash id as string..
    if index_name == "chunks":
        _uid = lambda x: bytes.fromhex(x.replace("-", "")).decode("utf8")
    else:
        _uid = lambda x: x

    if retrieves:
        _extract = lambda x: dict((r, x[r]) for r in retrieves)
    else:
        # Extract all
        _extract = lambda x: x
    hits = [_extract(es.get(index=index_name, id=_uid(x.id))["_source"]) for x in res if x]

    # For Sheets special case
    if do_unique_sheets:
        keep_idx = []
        seen_sheets = []
        for i, d in enumerate(hits):
            if d["url"] in seen_sheets:
                continue
            keep_idx.append(i)
            seen_sheets.append(d["url"])

        hits = [hits[i] for i in keep_idx][: limit // 5]

    return hits
