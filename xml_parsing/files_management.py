import os
import pandas as pd  # type: ignore


def get_xml_files(root_folder: str) -> list[str]:
    xml_files = []
    for root, _, files in os.walk(root_folder):
        for file in files:
            fullpath = os.path.join(root, file)
            if file.endswith(".xml"):
                xml_files.append(fullpath)
    return xml_files


def get_contexts(filepath: str) -> pd.DataFrame:
    contexts = pd.read_csv(filepath, sep=";")
    return contexts
