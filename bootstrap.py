#!/bin/python

""" Convert XML data gouv sheet to a Json (file) database.

Usage:
    bootstrap.py chunks DIRECTORY


Commands:
    chunks DIRECTORY    Parse les fichiers Xml issue de data.gouv, situé dans le repertoir DIRECTORY pour les transformer en fiches sous format Json.
                        Chaque élement Json correspond à un bout de fiche d'une longueur de 1000 caractères appelé chunk, découpé en conservant les phrases intacts.

Examples:
    ./bootstrap.py chunks ../../data.gouv/vos-droits-et-demarche/
"""

import json
import os

from docopt import docopt

from retrieving.text_spliter import HybridSplitter
from xml_parsing import parse_xml

if __name__ == "__main__":
    # Parse CLI arguments
    args = docopt(__doc__, version="0")

    if args["chunks"]:
        # Parse XML
        df = parse_xml(args["DIRECTORY"])

        # Chunkify and save to a Json file
        json_file_target = os.path.join("_data/", "xmlfiles_as_chunks.json")
        metadata_columns = ["file", "title", "xml_url", "surtitre", "subject", "theme"]
        chunk_size = 1100
        chunk_overlap = 200
        chunks = []
        text_splitter = HybridSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        for sheet in df.to_dict(orient="records"):
            data = {"data": "", "metadata": {}}
            for key in sheet:
                if key in metadata_columns:
                    data["metadata"][key] = sheet[key]
                elif key == "introduction":
                    data["data"] = sheet[key] + data["data"]
                elif key == "other_content" or key == "liste_situations":
                    data["data"] = data["data"] + sheet[key]

            for index, fragment in enumerate(text_splitter.split_text(data["data"])):
                chunk = {"data": fragment, "metadata": data["metadata"].copy()}
                chunk["metadata"]["chunk_index"] = index
                chunks.append(chunk)

        with open(json_file_target, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=4)
    else:
        raise NotImplementedError
