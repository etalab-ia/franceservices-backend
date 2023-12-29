import json
from pprint import pprint

from elasticsearch import Elasticsearch, helpers

try:
    from app.config import ELASTICSEARCH_IX_VER, SHEET_SOURCES, collate_ix_name
except ModuleNotFoundError:
    from api.app.config import (ELASTICSEARCH_IX_VER, SHEET_SOURCES,
                                collate_ix_name)


def create_bm25_index(index_name, add_doc=True, recreate=False):
    # Connect to Elasticsearch
    client = Elasticsearch("http://localhost:9202", basic_auth=("elastic", "changeme"))

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
            client.indices.delete(index=ix_name)
        client.indices.create(index=ix_name, mappings=mappings, settings=settings, ignore=400)

        if add_doc:
            # Add documents
            with open("_data/export-expa-c-riences.json") as f:
                documents = json.load(f)

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
            client.indices.delete(index=ix_name)
        client.indices.create(index=ix_name, mappings=mappings, settings=settings, ignore=400)

        if add_doc:
            # Add documents
            from xml_parsing import RagSource

            documents = RagSource.get_sheets(
                SHEET_SOURCES,
                structured=False,
                path="_data/data.gouv/vos-droits-et-demarche/",
            )
            documents = [d for d in documents if d["text"][0]]

            for doc in documents:
                doc["text"] = doc["text"][0]
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
            client.indices.delete(index=ix_name)
        client.indices.create(index=ix_name, mappings=mappings, settings=settings, ignore=400)

        if add_doc:
            # Add documents

            documents = []

            with open("_data/sheets_as_chunks.json") as f:
                documents = json.load(f)

            for doc in documents:
                doc["_id"] = doc["hash"]
                if "context" in doc:
                    doc["context"] = " > ".join(doc["context"])

            if len(documents) == 0:
                print(f"warning: No documents to add to the index '{ix_name}'")

            helpers.bulk(client, documents, index=ix_name)

    else:
        raise NotImplementedError("Index unknown")

    # Test index
    # client.indices.refresh(index=index_name)
    pprint(client.cat.count(index=ix_name, format="json"))
