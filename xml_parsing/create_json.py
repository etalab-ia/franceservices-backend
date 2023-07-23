import csv
import json
import sys
import copy
from retrieving.text_spliter import HybridSplitter

from .params import METADATA_COLUMN


def csv_to_listdict(csv_path: str):
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


def organize_datas(input_dico, metadata_columns=METADATA_COLUMN):
    output_dico = {"data": "", "metadata": {}}
    for key in input_dico:
        if key in metadata_columns:
            output_dico["metadata"][key] = input_dico[key]
        elif key == "introduction":
            output_dico["data"] = input_dico[key] + output_dico["data"]
        elif key == "other_content" or key == "liste_situations":
            output_dico["data"] = output_dico["data"] + input_dico[key]

    return output_dico


def save_json(liste_dictionnaires, json_path: str):
    with open(json_path, "w", encoding="utf-8") as fichier_json:
        json.dump(liste_dictionnaires, fichier_json, ensure_ascii=False)


def create_main_json(
    csv_path: str = "_data/json_database/files.json",
    json_organized_path: str = "_data/json_database/files.json",
):
    output_list = []
    list_dict = csv_to_listdict(csv_path)
    for input_dico in list_dict:
        output_dico = organize_datas(input_dico, METADATA_COLUMN)
        output_list.append(output_dico)
    save_json(output_list, json_organized_path)


### Code to chunk data


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


### Final Command for create json


def create_json_db(
    csv_path="_data/json_database/files.json",
    json_organized_path="_data/json_database/files.json",
    json_file_source="_data/json_database/files.json",
    json_file_target="_data/json_database/xmlfiles_as_chunks.json",
):
    create_main_json(csv_path, json_organized_path)
    all_to_chunk(json_file_source, json_file_target)
