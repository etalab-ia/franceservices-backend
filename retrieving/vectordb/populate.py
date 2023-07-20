from ast import Raise
from typing import List, Optional
import json

import pandas as pd  # type: ignore

from .settings import WEAVIATE_CLIENT
from .text_spliter import HybridSplitter
from .embedding import VectorEmbeddor


def get_xml_datas(xml_parsed_path: str) -> List[dict]:
    if xml_parsed_path.endswith(".json"):
        with open(xml_parsed_path, "r", encoding="utf-8") as json_file:
            xml_files_to_vectorize = json.load(json_file)
    elif xml_parsed_path.endswith(".csv"):
        xml_df = pd.read_csv(xml_parsed_path)
        xml_files_to_vectorize = xml_df.to_dict("records")
    else:
        xml_files_to_vectorize = []
        Raise("xml_parsed_path must be a json or csv file")
    return xml_files_to_vectorize


def create_schema(schema_name: str):
    class_obj = {
        "class": schema_name,
        "description": "Contexts to be used for answering questions with a chatbot",
        "properties": [
            {
                "dataType": ["text"],
                "description": "The theme of the context",
                "name": "theme",
            },
            {
                "dataType": ["text"],
                "description": "The title of the context",
                "name": "title",
            },
            {
                "dataType": ["text"],
                "description": "The surtitre of the context",
                "name": "surtitre",
            },
            {
                "dataType": ["text"],
                "description": "The content of the context",
                "name": "content",
            },
            {
                "dataType": ["text"],
                "description": "The subject of the context",
                "name": "subject",
            },
            {
                "dataType": ["text"],
                "description": "The URL of the original xml file",
                "name": "xml_url",
                "moduleConfig": {
                    "text2vec-contextionary": {
                        "skip": True,
                    }
                },
            },
        ],
    }

    existing_classes = [
        existing_class["class"]
        for existing_class in WEAVIATE_CLIENT.schema.get()["classes"]
    ]
    if schema_name not in existing_classes:
        print('Creating class "Contexts" in Weaviate...')
        WEAVIATE_CLIENT.schema.create_class(class_obj)


def reset_schema(schema_name: str):
    existing_classes = [
        existing_class["class"]
        for existing_class in WEAVIATE_CLIENT.schema.get()["classes"]
    ]

    if schema_name in existing_classes:
        print('Deleting schema "Contexts" in Weaviate...')
        WEAVIATE_CLIENT.schema.delete_class(schema_name)


def print_import_logs(import_number: int, *args) -> None:
    print(f"Adding to Weaviate file number {import_number}:")
    for arg in args:
        print(f"    - {arg}")


def run_weaviate_migration(
    xml_files_to_vectorize: List[dict], embeddor: Optional[VectorEmbeddor] = None
) -> None:
    reset_schema("Contexts")
    create_schema("Contexts")
    text_splitter = HybridSplitter(chunk_size=1000, chunk_overlap=100)

    with WEAVIATE_CLIENT.batch as batch:
        batch.batch_size = 10
        for index, xml_file in enumerate(xml_files_to_vectorize):
            xml_text_chunks = text_splitter.split_text(xml_file["data"])
            print_import_logs(
                index,
                xml_file["metadata"]["xml_url"],
                xml_file["metadata"]["title"],
                f"{len(xml_text_chunks)} chunks exctracted",
            )
            for xml_text_chunk in xml_text_chunks:
                properties = {
                    "content": xml_text_chunk,
                    "xml_url": xml_file["metadata"]["xml_url"],
                    "theme": xml_file["metadata"]["theme"],
                    "title": xml_file["metadata"]["title"],
                    "subject": xml_file["metadata"]["subject"],
                    "surtitre": xml_file["metadata"]["surtitre"],
                }

                vector = None
                if embeddor:
                    vector = embeddor.embed(xml_text_chunk)

                WEAVIATE_CLIENT.batch.add_data_object(
                    properties, "Contexts", vector=vector
                )
