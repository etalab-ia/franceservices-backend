import json
from pprint import pprint


def create_index(index_type, index_name, add_doc=True):
    if index_type == "bucket":
        return create_bucket_index(index_name, add_doc)
    elif index_type == "bm25":
        return create_bm25_index(index_name, add_doc)
    else:
        raise NotImplementedError


def create_bucket_index(index_name, add_doc=True):
    import meilisearch

    client = meilisearch.Client("http://localhost:7700", "masterKey")

    if index_name == "experiences":
        # Load stop words
        stopwords = []
        with open("_data/stopwords/fr.txt", "r") as file:
            for line in file:
                stopwords.append(line.strip())

        # Create index
        client.create_index(index_name, {"primaryKey": "id_experience"})
        client.index(index_name).update_settings(
            {
                "searchableAttributes": [
                    "description",
                    "titre",
                ],
                "displayedAttributes": [
                    "titre",
                    "reactivite",
                    "amelioration_de_service_a_considerer",
                    "relation",
                    "action",
                    "description",
                    "information_explication",
                    "intitule_typologie_1",
                    "reponse_structure_1",
                ],
                "stopWords": stopwords,
            }
        )

        # Get index
        index = client.get_index(index_name)

        if add_doc:
            # Add documents
            with open("_data/export-expa-c-riences.json") as f:
                documents = json.load(f)

            index.update_documents_in_batches(documents)

        ### Search test
        ##res = index.search("à l'aide !", {"limit": 3, "attributesToRetrieve": ["title", "description"]})

        ##print("total hit ~ %s" % res["estimatedTotalHits"])
        ##for v in res["hits"]:
        ##    pprint(v)

    elif index_name == "sheets":
        # Load stop words
        stopwords = []
        with open("_data/stopwords/fr.txt", "r") as file:
            for line in file:
                stopwords.append(line.strip())

        # Create index
        client.create_index(index_name, {"primaryKey": "id"})
        client.index(index_name).update_settings(
            {
                "searchableAttributes": ["title", "text", "subject"],
                "displayedAttributes": [
                    "title",
                    "subject",
                    "introduction",
                    "url",
                ],
                "stopWords": stopwords,
            }
        )

        # Get index
        index = client.get_index(index_name)

        if add_doc:
            from xml_parsing import parse_xml

            # Add documents
            df = parse_xml("_data/data.gouv/vos-droits-et-demarche/", structured=False)
            documents = [d for d in df.to_dict(orient="records") if d["text"][0]]

            for doc in documents:
                # one chunks for unstructured parsing.
                doc["id"] = doc["url"].split("/")[-1]
                doc["text"] = doc["text"][0]

            index.update_documents_in_batches(documents)

    elif index_name == "chunks":
        # Load stop words
        stopwords = []
        with open("_data/stopwords/fr.txt", "r") as file:
            for line in file:
                stopwords.append(line.strip())

        # Create index
        client.create_index(index_name, {"primaryKey": "hash"})
        client.index(index_name).update_settings(
            {
                "searchableAttributes": [
                    "title",
                    "context",
                    "text",
                    "introduction",
                ],
                "displayedAttributes": [
                    "title",
                    "context",
                    "text",
                    "url",
                ],
                "stopWords": stopwords,
            }
        )

        # Get index
        index = client.get_index(index_name)

        if add_doc:
            # Add documents
            with open("_data/xmlfiles_as_chunks.json") as f:
                documents = json.load(f)

            for doc in documents:
                if "context" in doc:
                    doc["context"] = " > ".join(doc["context"])

            index.update_documents_in_batches(documents)

    else:
        raise NotImplementedError("Index unknown")

    # Show index stats
    stats = index.get_stats()
    print("Stats for index '%s':" % index_name)
    print(pprint(dict(stats)))


def create_bm25_index(index_name, add_doc=True):
    from elasticsearch import Elasticsearch, helpers

    # Connect to Elasticsearch
    client = Elasticsearch("http://localhost:9202", basic_auth=("elastic", "changeme"))

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
                "intitule_typologie_1": {
                    "type": "text",
                    "index": False,
                },
                "reponse_structure_1": {
                    "type": "text",
                    "index": False,
                },
                # "url": {
                #    "type": "keyword"
                # }
            }
        }
        # Create the index
        client.indices.create(index=index_name, mappings=mappings, settings=settings, ignore=400)

        # Test index
        client.indices.refresh(index=index_name)
        pprint(client.cat.count(index=index_name, format="json"))

        if add_doc:
            # Add documents
            with open("_data/export-expa-c-riences.json") as f:
                documents = json.load(f)

            for doc in documents:
                doc["_id"] = doc["id_experience"]

            helpers.bulk(client, documents, index=index_name)

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
                "title": {"type": "text", "store": True, "analyzer": "french_analyzer"},
                "text": {"type": "text", "analyzer": "french_analyzer"},
                "subject": {"type": "text", "store": True, "analyzer": "french_analyzer"},
                "introduction": {"type": "text", "index": False},
                "url": {"type": "keyword", "index": False},
            }
        }
        # Create the index
        client.indices.create(index=index_name, mappings=mappings, settings=settings, ignore=400)

        # Test index
        client.indices.refresh(index=index_name)
        pprint(client.cat.count(index=index_name, format="json"))

        if add_doc:
            # Add documents
            from xml_parsing import parse_xml

            df = parse_xml("_data/data.gouv/vos-droits-et-demarche/", structured=False)
            documents = [d for d in df.to_dict(orient="records") if d["text"][0]]

            for doc in documents:
                doc["_id"] = doc["url"].split("/")[-1]
                doc["text"] = doc["text"][0]

            helpers.bulk(client, documents, index=index_name)
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
                "title": {"type": "text", "store": True, "analyzer": "french_analyzer"},
                "text": {"type": "text", "store": True, "analyzer": "french_analyzer"},
                "context": {"type": "text", "store": True, "analyzer": "french_analyzer"},
                "introduction": {"type": "text", "analyzer": "french_analyzer"},
                "url": {"type": "keyword", "index": False},
            }
        }
        # Create the index
        client.indices.create(index=index_name, mappings=mappings, settings=settings, ignore=400)

        # Test index
        #client.indices.refresh(index=index_name)
        pprint(client.cat.count(index=index_name, format="json"))

        if add_doc:
            # Add documents
            with open("_data/xmlfiles_as_chunks.json") as f:
                documents = json.load(f)

            for doc in documents:
                doc["_id"] = doc["hash"]
                if "context" in doc:
                    doc["context"] = " > ".join(doc["context"])

            helpers.bulk(client, documents, index=index_name)
    else:
        raise NotImplementedError("Index unknown")
