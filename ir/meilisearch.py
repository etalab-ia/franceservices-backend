import json
from pprint import pprint

import meilisearch

try:
    from app.config import SHEET_SOURCES
except ModuleNotFoundError:
    from api.app.config import SHEET_SOURCES


def create_bucket_index(index_name, add_doc=True, directory=None):
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
        client.create_index(index_name, {"primaryKey": "sid"})
        client.index(index_name).update_settings(
            {
                "searchableAttributes": ["title", "text", "subject", "source"],
                "displayedAttributes": [
                    "title",
                    "subject",
                    "introduction",
                    "url",
                    "source",
                ],
                "stopWords": stopwords,
            }
        )

        # Get index
        index = client.get_index(index_name)

        if add_doc:
            # Add documents
            from sourcing import RagSource

            documents = RagSource.get_sheets(
                SHEET_SOURCES,
                structured=False,
                path=directory,
            )
            documents = [d for d in documents if d["text"][0]]

            for doc in documents:
                # one chunks for unstructured parsing.
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
                    "source",
                ],
                "displayedAttributes": [
                    "title",
                    "context",
                    "text",
                    "url",
                    "source",
                ],
                "stopWords": stopwords,
            }
        )

        # Get index
        index = client.get_index(index_name)

        if add_doc:
            # Add documents
            with open("_data/sheets_as_chunks.json") as f:
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
