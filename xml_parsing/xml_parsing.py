import hashlib
import json
import os
import unicodedata
from collections import defaultdict
from typing import List

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from bs4.element import Tag

from retrieving.text_spliter import HybridSplitter


def normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def extract(soup: Tag, tag: str, pop: bool = False) -> str:
    t = soup.find(tag)
    if not t:
        return ""

    if pop:
        t.extract()

    return normalize(t.get_text(" ", strip=True))


def extract_all(soup: Tag, tag: str, pop: bool = False) -> List[str]:
    if not soup.find(tag):
        return []

    elts = []
    for t in soup.find_all(tag):
        if pop:
            t.extract()
        elts.append(normalize(t.get_text(" ", strip=True)))

    return elts


def make_chunks(directory: str, chunk_size: int = 1100, chunk_overlap: int = 200) -> None:
    # Parses service-public XML
    df = parse_xml(directory)

    # Chunkify and save to a Json file
    basedir = "_data/"
    json_file_target = os.path.join(basedir, "xmlfiles_as_chunks.json")
    metadata_columns = ["file", "title", "xml_url", "surtitre", "subject", "theme"]
    text_columns = ["introduction", "liste_situations", "other_content"]  # introduction OR description
    chunks = []
    text_splitter = HybridSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    hashes = []  # checks for duplicate chunks
    info = defaultdict(lambda: defaultdict(list))
    for sheet in df.to_dict(orient="records"):
        data = {"text": []}
        for key in metadata_columns:
            if key in sheet:
                data[key] = sheet[key]

        for key in text_columns:
            if key in sheet:
                data["text"].append(sheet[key])
            elif key == "introduction" and "description" in sheet:
                data["text"].append(sheet["description"])

        data["text"] = " ".join(data["text"]).strip()

        if not data["text"]:
            continue
        if data["surtitre"] in ["Dossier", "Recherche guidée"]:
            continue

        print(
            f"""
             \rfile: {sheet["file"]}
             \rtitle: {sheet["title"]}
             \rsurtitre: {sheet["surtitre"]}
             \raudience: {sheet["audience"]}
             \rdescription: {sheet["introduction"] or sheet["description"]}
             \r{sheet["other_content"]}
             \r{len(data["text"])}

            """
        )

        info[sheet["surtitre"]]["len"].append(len(data["text"]))

        for index, fragment in enumerate(text_splitter.split_text(data["text"])):
            h = hashlib.blake2b(fragment.encode(), digest_size=8).hexdigest()
            if h in hashes:
                continue
            else:
                hashes.append(h)

            chunk = data.copy()
            chunk["text"] = fragment
            chunk["chunk_index"] = index
            chunks.append(chunk)

    with open(json_file_target, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=4)

    info_summary = ""
    for k, v in info.items():
        info_summary += f"### {k}\n"
        info_summary += f"total doc: {len(v['len'])}\n"
        info_summary += f"mean length: {np.mean(v['len']):.0f} ± {np.std(v['len']):.0f}\n"
        info_summary += "\n"

    chunks_fn = os.path.join(basedir, "chunks.info")
    with open(chunks_fn, "w", encoding="utf-8") as f:
        f.write(info_summary)

    print("Chunks created in", chunks_fn)


def parse_xml(xml_3_folders_path: str = "_data/xml") -> pd.DataFrame:
    xml_files = []

    if os.path.isfile(xml_3_folders_path):
        # Use to test result on a particular file
        xml_files = [xml_3_folders_path]
    else:
        for root, _, files in os.walk(xml_3_folders_path):
            for file in files:
                fullpath = os.path.join(root, file)
                if file.endswith(".xml"):
                    xml_files.append(fullpath)

    docs = []
    current_percentage = 0
    for xml_index, xml_file in enumerate(xml_files):
        # Print the percentage of total time
        if (100 * xml_index) // (len(xml_files)) > current_percentage:
            current_percentage = (100 * xml_index) // (len(xml_files))
            print(f"Process: {current_percentage}%\r", end="")

        if not ("N" in xml_file.split("/")[-1] or "F" in xml_file.split("/")[-1]):
            # Permet de garder uniquement les fiches pratiques,
            # fiches questions-réponses, fiches thème, fiches dossier.
            continue

        doc = parse_xml_sheet(xml_file)
        if not doc:
            continue

        doc["file"] = xml_file
        docs.append(doc)

    return pd.DataFrame(docs)


def parse_xml_sheet(xml_filepath: str) -> dict:
    """
    On utilise cette fonction pour créer un csv pour les fichiers qui commencent par N ou F.
    Ils correspondent soit à des fiches pratiques,
    soit à des questions réponses, soit à des fiches dossiers...
    """
    with open(xml_filepath, "r", encoding="utf-8") as xml_file:
        soup = BeautifulSoup(xml_file, "xml")

    doc = {}
    doc["xml_url"] = ""
    if soup.find("Publication") is not None:
        if "spUrl" in soup.find("Publication").attrs:
            doc["xml_url"] = soup.find("Publication")["spUrl"]
    # --
    doc["audience"] = ", ".join(extract_all(soup, "Audience"))
    doc["theme"] = ", ".join(extract_all(soup, "Theme"))
    # --
    doc["surtitre"] = extract(soup, "SurTitre")  # == dc:type
    doc["subject"] = extract(soup, "dc:subject")
    doc["title"] = extract(soup, "dc:title")
    doc["description"] = extract(soup, "dc:description")
    doc["introduction"] = extract(soup, "Introduction", pop=True)

    #
    # Content
    #

    doc["liste_situations"] = ""
    if soup.find("ListeSituations") is not None:
        doc["liste_situations"] = "Liste des situations : "
        for i, situation in enumerate(soup.find("ListeSituations").find_all("Situation")):
            situation_title = situation.find("Titre").get_text(" ", strip=True)
            situation_texte = situation.find("Texte").get_text(" ", strip=True)
            situation_title = unicodedata.normalize("NFKC", situation_title)
            situation_texte = unicodedata.normalize("NFKC", situation_texte)

            doc["liste_situations"] += " Cas n°" + str(i + 1) + " : " + situation_title + " : " + situation_texte

    doc["other_content"] = ""
    if soup.find("Publication") is not None:
        if soup.find("Publication").find("Texte", recursive=False) is not None:
            doc["other_content"] = soup.find("Publication").find("Texte", recursive=False).get_text(" ", strip=True)
            doc["other_content"] = unicodedata.normalize("NFKC", doc["other_content"])

    return doc


def table_to_md(soup):
    md_table = "| "

    # Headers
    for cell in soup.find_all("cellule", parent=lambda tag: tag.name == "rangée" and tag.get("type") == "header"):
        md_table += cell.paragraphe.string + " | "
    md_table += "\n"

    # Separator
    for _ in soup.find_all("cellule", parent=lambda tag: tag.name == "rangée" and tag.get("type") == "header"):
        md_table += "| --- "
    md_table += "|\n"

    # Rows
    for row in soup.find_all("rangée", {"type": "normal"}):
        md_table += "| "
        for cell in row.find_all("cellule"):
            md_table += cell.paragraphe.string + " | "
        md_table += "\n"

    return md_table
