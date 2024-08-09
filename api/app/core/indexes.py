from elasticsearch import Elasticsearch
from qdrant_client import QdrantClient
from qdrant_client import models as QdrantModels

from pyalbert import collate_ix_name
from pyalbert.clients import SearchEngineClient
from pyalbert.config import (
    ELASTICSEARCH_CREDS,
    ELASTICSEARCH_IX_VER,
    ELASTICSEARCH_URL,
    QDRANT_GRPC_PORT,
    QDRANT_IX_VER,
    QDRANT_REST_PORT,
    QDRANT_URL,
    QDRANT_USE_GRPC,
)


def get_document(index_name: str, uid: str) -> dict:
    es = Elasticsearch(ELASTICSEARCH_URL, basic_auth=ELASTICSEARCH_CREDS)

    if index_name == "sheets":
        doc = es.get(index=collate_ix_name(index_name, ELASTICSEARCH_IX_VER), id=uid)["_source"]
    elif index_name == "chunks":
        doc = es.get(index=collate_ix_name(index_name, ELASTICSEARCH_IX_VER), id=uid)["_source"]
    else:
        raise NotImplementedError("Index unkown")

    return doc


def search_indexes(
    name,
    query,
    limit,
    similarity,
    institution,
    sources,
    should_sids=None,
    must_not_sids=None,
    do_expand_acronyms=False,
) -> list[dict]:
    # Similarity ignored / @TODO: to remove
    filters = {
        "institution": institution,
        "sources": sources,
        "should_sids": should_sids,
        "must_not_sids": must_not_sids,
    }

    se_client = SearchEngineClient()
    hits = se_client.search(
        name, query, limit=limit, filters=filters, do_expand_acronyms=do_expand_acronyms
    )

    return hits
