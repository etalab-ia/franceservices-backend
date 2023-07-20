import csv
import json
import os
import sys
import copy
from retrieving.text_spliter import HybridSplitter

# Chemin vers le fichier CSV
CSV_PATH = os.path.join("datas/cleaned_xml", "string_publications_xml_parsed.csv")
JSON_PARSED_PATH = os.path.join("datas/json_files", "string_complete_db.json")
JSON_ORGANIZED_PATH = os.path.join("datas/json_files", "organized_string_db.json")

DATA_COLUMN = ["introduction", "liste_situations", "other_content"]
METADATA_COLUMN = ["file", "title", "xml_url", "surtitre", "subject", "theme"]


def csv_to_json(csv_path: str = "datas/cleaned_xml/publications_xml_parsed.csv"):
    # Augmentation de la taille maximale du champ
    csv.field_size_limit(sys.maxsize)

    liste_dictionnaires = []

    # Ouverture du fichier CSV en mode lecture
    with open(csv_path, newline="", encoding="utf-8") as fichier_csv:
        lecteur_csv = csv.DictReader(fichier_csv, delimiter=";")

        next(lecteur_csv)
        # Parcours de chaque ligne du CSV
        for ligne in lecteur_csv:
            dico_ligne = {}
            for colonne, valeur in ligne.items():
                dico_ligne[colonne] = valeur

            liste_dictionnaires.append(dico_ligne)

        return liste_dictionnaires


def organize_datas(input_dico, metadata_columns):
    output_dico = {"data": "", "metadata": {}}
    for key in input_dico:
        if key in metadata_columns:
            output_dico["metadata"][key] = input_dico[key]
        elif key == "introduction":
            output_dico["data"] = input_dico[key] + output_dico["data"]
        elif key == "other_content" or key == "liste_situations":
            output_dico["data"] = output_dico["data"] + input_dico[key]

    return output_dico


def save_json(
    liste_dictionnaires, json_path: str = "datas/json_files/string_complete_db.json"
):
    with open(json_path, "w", encoding="utf-8") as fichier_json:
        json.dump(liste_dictionnaires, fichier_json, ensure_ascii=False)


def create_main_json(xml_parsed_json_path, json_organized_path):
    output_list = []
    with open(xml_parsed_json_path, "r", encoding="utf-8") as json_file:
        xml_files_to_organize = json.load(json_file)
        for input_dico in xml_files_to_organize:
            output_dico = organize_datas(input_dico, METADATA_COLUMN)
            output_list.append(output_dico)
        save_json(output_list, json_organized_path)


def all_json_actions(csv_path: str, json_parsed_path: str, json_organized_path: str):
    save_json(csv_to_json(csv_path), json_parsed_path)
    create_main_json(json_parsed_path, json_organized_path)


### Code to chunk data


JSON_FILE_SOURCE = os.path.join("datas/json_files", "organized_string_db.json")
JSON_FILE_TARGET = os.path.join("datas/json_files", "chunk_organized_string_db.json")


def all_to_chunk(json_file_source, json_file_target):
    text_splitter = HybridSplitter(chunk_size=1100, chunk_overlap=200)
    with open(json_file_source, "r", encoding="utf-8") as f:
        law_documents = json.load(f)

    new_list = []
    for law_document in law_documents:
        liste_chunks = text_splitter.split_text(law_document["data"])
        for index, chunk in enumerate(liste_chunks):
            new_chunk_doc = {"data": chunk, "metadata": law_document["metadata"]}
            new_chunk_doc["metadata"]["chunk_index"] = index
            new_list.append(copy.deepcopy(new_chunk_doc))

    with open(json_file_target, "w", encoding="utf-8") as target_file:
        json.dump(new_list, target_file, ensure_ascii=False)


def chunk_db():
    all_to_chunk(JSON_FILE_SOURCE, JSON_FILE_TARGET)


#### Final Command for create json


def final_command_json():
    all_json_actions(CSV_PATH, JSON_PARSED_PATH, JSON_ORGANIZED_PATH)
