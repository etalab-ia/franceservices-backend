from app.config import (
    ELASTICSEARCH_CREDS,
    ELASTICSEARCH_IX_VER,
    ELASTICSEARCH_URL,
    QDRANT_IX_VER,
    QDRANT_URL,
    collate_ix_name,
)
from app.core.embeddings import make_embeddings
from elasticsearch import Elasticsearch
from qdrant_client import QdrantClient
from qdrant_client import models as QdrantModels


def _retrieves(index_name: str, similarity=None):
    if index_name == "experiences":
        retrieves = [
            "id_experience",
            "titre",
            "description",
            "intitule_typologie_1",
            "reponse_structure_1",
        ]
    elif index_name == "sheets" and similarity not in ["e5"]:
        retrieves = [
            "sid",
            "title",
            "url",
            "introduction",
            "theme",
            "surtitre",
            "source",
            "related_questions",
            "web_services",
        ]
    elif index_name == "chunks" or (similarity in ["e5"] and index_name == "sheets"):
        retrieves = [
            "hash",
            "sid",
            "title",
            "url",
            "introduction",
            "text",
            "context",
            "theme",
            "surtitre",
            "source",
            "related_questions",
            "web_services",
        ]
    else:
        raise NotImplementedError("Index unkown")

    return retrieves


def get_document(index_name: str, uid: str):
    es = Elasticsearch(ELASTICSEARCH_URL, basic_auth=ELASTICSEARCH_CREDS)
    _extract = lambda x: dict((r, x[r]) for r in _retrieves(index_name) if r in x)

    if index_name == "sheets":
        doc = _extract(
            es.get(index=collate_ix_name(index_name, ELASTICSEARCH_IX_VER), id=uid)["_source"]
        )
    elif index_name == "chunks":
        doc = _extract(
            es.get(index=collate_ix_name(index_name, ELASTICSEARCH_IX_VER), id=uid)["_source"]
        )
    else:
        raise NotImplementedError("Index unkown")

    return doc


def search_indexes(
    name, query, limit, similarity, institution, sources, should_sids=None, must_not_sids=None
):
    _extract = lambda x: dict((r, x[r]) for r in _retrieves(name, similarity) if r in x)

    hits = None
    if similarity == "bm25":
        client = Elasticsearch(ELASTICSEARCH_URL, basic_auth=ELASTICSEARCH_CREDS)
        must_filter = [{"multi_match": {"query": query, "fuzziness": "AUTO"}}]
        must_not_filter = []
        should_filter = []
        query_filter = []
        if institution:
            query_filter.append({"term": {"intitule_typologie_1": institution}})
        if sources:
            query_filter.append({"terms": {"source": sources}})
        if should_sids:
            should_filter.append({"ids": {"values": should_sids, "boost": 100}})
        if must_not_sids:
            must_not_filter.append({"ids": {"values": must_not_sids}})

        body = {
            "query": {
                "bool": {
                    "must": must_filter,
                    "must_not": must_not_filter,
                    "should": should_filter,
                    "filter": query_filter,
                }
            },
            "size": limit,
        }
        res = client.search(index=collate_ix_name(name, ELASTICSEARCH_IX_VER), body=body)
        hits = [_extract(x.get("_source")) for x in res["hits"]["hits"] if x]

    elif similarity == "e5":
        do_unique_sheets = False
        if name == "sheets":
            name = "chunks"
            limit = limit * 5
            do_unique_sheets = True

        embeddings = make_embeddings(query)
        client = QdrantClient(url=QDRANT_URL, grpc_port=6334, prefer_grpc=True)
        # Eventually set filters
        must_filter = []
        should_filter = []
        must_not_filter = []
        if institution:
            must_filter.append(
                QdrantModels.FieldCondition(
                    key="intitule_typologie_1",
                    match=QdrantModels.MatchValue(
                        value=institution,
                    ),
                )
            )
        if sources:
            # Equivalent to must_filter+MatchAny
            should_filter.extend(
                [
                    QdrantModels.FieldCondition(
                        key="source",
                        match=QdrantModels.MatchValue(
                            value=source,
                        ),
                    )
                    for source in sources
                ]
            )
        if should_sids:
            # @debug: Qdrant has a different "should" semantic than elasticsearch.
            # Qdrant should is a strict OR condition.
            must_filter.append(
                QdrantModels.FieldCondition(
                    key="sid",
                    match=QdrantModels.MatchAny(
                        any=should_sids,
                    ),
                )
            )
        if must_not_sids:
            must_not_filter.append(
                QdrantModels.FieldCondition(
                    key="sid",
                    match=QdrantModels.MatchAny(
                        any=must_not_sids,
                    ),
                )
            )

        query_filter = QdrantModels.Filter(
            must=must_filter,
            should=should_filter,
            must_not=must_not_filter,
        )

        res = client.search(
            collection_name=collate_ix_name(name, QDRANT_IX_VER),
            query_vector=embeddings,
            query_filter=query_filter,
            limit=limit,
        )

        es = Elasticsearch(ELASTICSEARCH_URL, basic_auth=ELASTICSEARCH_CREDS)
        # FIXME: qdrant doesn't accept the hash id as string
        if name == "chunks":
            _uid = lambda x: bytes.fromhex(x.replace("-", "")).decode("utf8")
        else:
            _uid = lambda x: x
        hits = [
            _extract(
                es.get(index=collate_ix_name(name, ELASTICSEARCH_IX_VER), id=_uid(x.id))["_source"]
            )
            for x in res
            if x
        ]
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
