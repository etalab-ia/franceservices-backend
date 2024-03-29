import json
import os
import re

from pyalbert.corpus.parser import RagSource


def _add_space_after_punctuation(text: str):
    return re.sub(r"([.,;:!?])([^\s\d])", r"\1 \2", text)


def load_exeriences(storage_dir: str):
    with open(os.path.join(storage_dir, "export-expa-c-riences.json")) as f:
        documents = json.load(f)

    for d in documents:
        descr = d["description"]
        d["description"] = _add_space_after_punctuation(descr)

    return documents


def load_sheets(storage_dir: str, sources: str | list[str]):
    documents = RagSource.get_sheets(
        storage_dir=storage_dir,
        sources=sources,
        structured=False,
    )
    documents = [d for d in documents if d["text"][0]]
    for doc in documents:
        doc["text"] = doc["text"][0]

    return documents


def load_sheet_chunks(storage_dir: str, format_context: bool = True):
    with open(os.path.join(storage_dir, "sheets_as_chunks.json")) as f:
        documents = json.load(f)

    if format_context:
        for doc in documents:
            if "context" in doc:
                doc["context"] = " > ".join(doc["context"])

    return documents
