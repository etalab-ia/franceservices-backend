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
                doc["text"] = doc["text"][0]
                doc["id"] = doc["url"].split("/")[-1]

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
                    "text" "introduction",
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
    from elasticsearch import Elasticsearch

    # Connect to Elasticsearch
    es = Elasticsearch([{"scheme": "http", "host": "localhost", "port": 9200}])

    # Define index settings and mappings
    if index_name == "experiences":
        index_settings = {
            "settings": {
                "index": {
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
            },
            "mappings": {
                "properties": {
                    "title": {"type": "text", "store": True, "analyzer": "french_analyzer"},
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
            },
        }
    elif index_name == "sheets":
        pass
    elif index_name == "chunks":
        pass
    else:
        raise NotImplementedError("Index unknown")

    # Create the index
    res = es.indices.create(index=index_name, body=index_settings, headers={'Content-Type': 'application/json'})

    print(res)
