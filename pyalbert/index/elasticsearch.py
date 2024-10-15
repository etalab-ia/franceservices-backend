import logging
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

from .commons import CorpusHandler, embed

logging.getLogger("elastic_transport.transport").setLevel(logging.WARNING)


def create_elasticsearch_index(
    index_name, add_doc=True, recreate=False, batch_size=None, storage_dir=None
):
    batch_size = batch_size if batch_size else 16
    probe_vector = embed("Hey, I'am a probe")
    embedding_size = len(probe_vector)

    # Connect to Elasticsearch
    client = Elasticsearch(ELASTICSEARCH_URL, basic_auth=ELASTICSEARCH_CREDS)
    ix_name = collate_ix_name(index_name, ELASTICSEARCH_IX_VER)

    # Define index settings and mappings
    if index_name == "spp_experiences":
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
                # Lexical search
                "titre": {"type": "text", "store": True, "analyzer": "french_analyzer"},
                "description": {"type": "text", "store": True, "analyzer": "french_analyzer"},
                "reponse_structure_1": {"type": "text", "store": True, "analyzer": "french_analyzer"},
                "id_experience": {"type": "keyword", "index": False},
                "intitule_typologie_1": {"type": "keyword"},
                # Semantic search
                "embedding": {"type": "dense_vector", "similarity": "dot_product", "dims": embedding_size},
            },
        }  # fmt: skip

        # Create the index
        if recreate:
            client.indices.delete(index=ix_name, ignore_unavailable=True)
        client.indices.create(index=ix_name, mappings=mappings, settings=settings, ignore=400)

        # Add documents
        if add_doc:
            documents = load_exeriences(storage_dir)
            if len(documents) == 0:
                print(f"warning: No documents to add to the index '{ix_name}'")

            corpus_handler = CorpusHandler.create_handler(index_name, documents)
            for batch_documents, batch_embeddings in corpus_handler.iter_docs_embeddings(
                batch_size
            ):
                for doc, embedding in zip(batch_documents, batch_embeddings):
                    doc["_id"] = doc["id_experience"]
                    if embedding is not None:
                        doc["embedding"] = embedding

                helpers.bulk(client, batch_documents, index=ix_name)

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
            if len(documents) == 0:
                print(f"warning: No documents to add to the index '{ix_name}'")

            for doc in documents:
                doc["_id"] = doc["sid"]

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
                # Semantic search
                "embedding": {"type": "dense_vector", "similarity": "dot_product", "dims": embedding_size},
            },
        }  # fmt: skip

        # Create the index
        if recreate:
            client.indices.delete(index=ix_name, ignore_unavailable=True)
        client.indices.create(index=ix_name, mappings=mappings, settings=settings, ignore=400)

        # Add documents
        if add_doc:
            documents = load_sheet_chunks(storage_dir)
            if len(documents) == 0:
                print(f"warning: No documents to add to the index '{ix_name}'")

            corpus_handler = CorpusHandler.create_handler(index_name, documents)
            for batch_documents, batch_embeddings in corpus_handler.iter_docs_embeddings(
                batch_size
            ):
                for doc, embedding in zip(batch_documents, batch_embeddings):
                    doc["_id"] = doc["hash"]
                    if embedding is not None:
                        doc["embedding"] = embedding
                helpers.bulk(client, batch_documents, index=ix_name)

    else:
        raise NotImplementedError("Index unknown")

    # Test index
    # client.indices.refresh(index=index_name)
    pprint(client.cat.count(index=ix_name, format="json"))


def list_elasticsearch_indexes(index_pattern="*"):
    """List and show information about Elasticsearch indices.

    :param index_pattern: Pattern to match index names (default: '*' for all indices)
    """
    client = Elasticsearch(ELASTICSEARCH_URL, basic_auth=ELASTICSEARCH_CREDS)
    indices = client.cat.indices(index=index_pattern, format="json", v=True)

    if not indices:
        print(f"No indices found matching the pattern: {index_pattern}")
        return

    print("=" * 80)
    print("ELASTICSEARCH INDICES INFORMATION (%s)" % (ELASTICSEARCH_URL))
    print("=" * 80)

    # Print header
    print(
        "{:<20} {:<10} {:<15} {:<15} {:<15}".format(
            "Index", "Health", "Docs Count", "Store Size", "Primary Shards"
        )
    )
    print("-" * 80)

    # Print index information
    for index in indices:
        print(
            "{:<20} {:<10} {:<15} {:<15} {:<15}".format(
                index["index"],
                index["health"],
                index["docs.count"],
                index["store.size"],
                index["pri"],
            )
        )

    print("-" * 80)
    print(f"Total indices: {len(indices)}")
    print()
