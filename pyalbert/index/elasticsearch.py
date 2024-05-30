from pprint import pprint

from elasticsearch import Elasticsearch, helpers

from pyalbert import collate_ix_name
from pyalbert.config import (
    ELASTICSEARCH_CREDS,
    ELASTICSEARCH_IX_VER,
    ELASTICSEARCH_URL,
    SHEET_SOURCES,
)
from pyalbert.corpus import load_exeriences, load_sheet_chunks, load_sheets


def create_bm25_index(index_name, add_doc=True, recreate=False, storage_dir=None):
    # Connect to Elasticsearch
    client = Elasticsearch(ELASTICSEARCH_URL, basic_auth=ELASTICSEARCH_CREDS)
    ix_name = collate_ix_name(index_name, ELASTICSEARCH_IX_VER)

    # Define index settings and mappings
    if index_name == "experiences":
        settings = {
            "similarity": {"default": {"type": "BM25"}},
            "analysis": {
                "filter": {
                    "french_stop": {"type": "stop", "stopwords": "_french_"},
                    "french_stemmer": {"type": "stemmer", "language": "light_french"},
                },
                "analyzer": {
                    "french_analyzer": {
                        "tokenizer": "standard",
                        "filter": ["lowercase", "french_stop", "french_stemmer"],
                    }
                },
            },
        }
        mappings = {
            "dynamic": False,
            "properties": {
                "titre": {"type": "text", "store": True, "analyzer": "french_analyzer"},
                "description": {"type": "text", "store": True, "analyzer": "french_analyzer"},
                "intitule_typologie_1": {"type": "keyword"},
                "reponse_structure_1": {"type": "text", "index": False},
                "id_experiences": {"type": "keyword", "index": False},
            },
        }
        # Create the index
        if recreate:
            client.indices.delete(index=ix_name, ignore_unavailable=True)
        client.indices.create(index=ix_name, mappings=mappings, settings=settings, ignore=400)

        if add_doc:
            # Add documents
            documents = load_exeriences(storage_dir)

            for doc in documents:
                doc["_id"] = doc["id_experience"]

            helpers.bulk(client, documents, index=ix_name)

    elif index_name == "sheets":
        settings = {
            "similarity": {"default": {"type": "BM25"}},
            "analysis": {
                "filter": {
                    "french_stop": {"type": "stop", "stopwords": "_french_"},
                    "french_stemmer": {"type": "stemmer", "language": "light_french"},
                },
                "analyzer": {
                    "french_analyzer": {
                        "tokenizer": "standard",
                        "filter": ["lowercase", "french_stop", "french_stemmer"],
                    }
                },
            },
        }
        mappings = {
            "dynamic": False,
            "properties": {
                "source": {"type": "keyword", "store": True},
                "title": {"type": "text", "store": True, "analyzer": "french_analyzer"},
                "text": {"type": "text", "analyzer": "french_analyzer"},
                "subject": {"type": "text", "store": True, "analyzer": "french_analyzer"},
                "introduction": {"type": "text", "index": False},
                "theme": {"type": "text", "index": False},
                "surtitre": {"type": "text", "index": False},
                "url": {"type": "keyword", "index": False},
                "sid": {"type": "keyword", "index": False},
                "related_questions": {
                    "type": "nested",
                    "index": False,
                    "properties": {
                        "question": {"type": "text"},
                        "sid": {"type": "keyword"},
                        "url": {"type": "keyword"},
                    },
                },
                "web_services": {
                    "type": "nested",
                    "index": False,
                    "properties": {
                        "title": {"type": "text"},
                        "source": {"type": "text"},
                        "url": {"type": "keyword"},
                    },
                },
            },
        }
        # Create the index
        if recreate:
            client.indices.delete(index=ix_name, ignore_unavailable=True)
        client.indices.create(index=ix_name, mappings=mappings, settings=settings, ignore=400)

        if add_doc:
            # Add documents
            documents = load_sheets(storage_dir, sources=SHEET_SOURCES)

            for doc in documents:
                doc["_id"] = doc["sid"]

            if len(documents) == 0:
                print(f"warning: No documents to add to the index '{ix_name}'")

            helpers.bulk(client, documents, index=ix_name)

    elif index_name == "chunks":
        settings = {
            "similarity": {"default": {"type": "BM25"}},
            "analysis": {
                "filter": {
                    "french_stop": {"type": "stop", "stopwords": "_french_"},
                    "french_stemmer": {"type": "stemmer", "language": "light_french"},
                },
                "analyzer": {
                    "french_analyzer": {
                        "tokenizer": "standard",
                        "filter": ["lowercase", "french_stop", "french_stemmer"],
                    }
                },
            },
        }
        mappings = {
            "dynamic": False,
            "properties": {
                "source": {"type": "keyword", "store": True},
                "title": {"type": "text", "store": True, "analyzer": "french_analyzer"},
                "text": {"type": "text", "store": True, "analyzer": "french_analyzer"},
                "context": {"type": "text", "store": True, "analyzer": "french_analyzer"},
                "introduction": {"type": "text", "analyzer": "french_analyzer"},
                "theme": {"type": "text", "index": False},
                "surtitre": {"type": "text", "index": False},
                "url": {"type": "keyword", "index": False},
                "sid": {"type": "keyword", "index": False},
                "hash": {"type": "keyword", "index": False},
                "related_questions": {
                    "type": "nested",
                    "index": False,
                    "properties": {
                        "question": {"type": "text"},
                        "sid": {"type": "keyword"},
                        "url": {"type": "keyword"},
                    },
                },
                "web_services": {
                    "type": "nested",
                    "index": False,
                    "properties": {
                        "title": {"type": "text"},
                        "source": {"type": "text"},
                        "url": {"type": "keyword"},
                    },
                },
            },
        }
        # Create the index
        if recreate:
            client.indices.delete(index=ix_name, ignore_unavailable=True)
        client.indices.create(index=ix_name, mappings=mappings, settings=settings, ignore=400)

        if add_doc:
            # Add documents
            documents = load_sheet_chunks(storage_dir)

            for doc in documents:
                doc["_id"] = doc["hash"]

            if len(documents) == 0:
                print(f"warning: No documents to add to the index '{ix_name}'")

            helpers.bulk(client, documents, index=ix_name)

    else:
        raise NotImplementedError("Index unknown")

    # Test index
    # client.indices.refresh(index=index_name)
    pprint(client.cat.count(index=ix_name, format="json"))
