import hashlib
import json
import os
import string
import unicodedata
from collections import defaultdict
from typing import List

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from retrieving.text_spliter import HybridSplitter


def make_questions(directory: str) -> None:
    # Parses service-public XML
    basedir = "_data/"
    df = parse_questions(directory)
    df.drop_duplicates(subset=["question"], inplace=True)
    q_fn = os.path.join(basedir, "questions.json")
    # df.to_json(q_fn, orient="records", indent=2, force_ascii=False)
    with open(q_fn, "w", encoding="utf-8") as f:
        json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=4)
    print("Questions created in", q_fn)


def make_chunks(directory: str, structured=False, chunk_size=1100, chunk_overlap=200) -> None:
    # Parses service-public XML
    df = parse_xml(directory, structured)

    if structured:
        chunk_overlap = 20

    # Chunkify and save to a Json file
    basedir = "_data/"
    data_columns = ["file", "url", "surtitre", "theme", "title", "subject", "introduction", "text", "context"]
    chunks = []
    text_splitter = HybridSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    hashes = []  # checks for duplicate chunks
    info = defaultdict(lambda: defaultdict(list))
    for sheet in df.to_dict(orient="records"):
        data = {}
        for key in data_columns:
            if key in sheet:
                data[key] = sheet[key]

        if not data["text"]:
            continue
        if data["surtitre"] in ["Dossier", "Recherche guidée"]:
            # @TODO: can be used for cross-reference...
            # see also <LienInterne>...
            continue

        # print(
        #    f"""
        #     \rFile: {sheet["file"]}
        #     \rTitle: {sheet["title"]}
        #     \rSurtitre: {sheet["surtitre"]}
        #     \rAudience: {sheet["audience"]}
        #     \rDescription: {sheet["introduction"]}
        #     \rOther content: {sheet["other_content"]}
        #     \r{len(data["text"])}

        #    """
        # )
        if structured:
            info[sheet["surtitre"]]["len"].append(len(" ".join([x["text"] for x in data["text"]]).split()))
        else:
            info[sheet["surtitre"]]["len"].append(len(" ".join(data["text"]).split()))

        index = 0
        for natural_chunk in data["text"]:
            # Natural splitting
            if isinstance(natural_chunk, dict):
                natural_text_chunk = natural_chunk["text"]
            else:
                natural_text_chunk = natural_chunk

            #for fragment in [natural_text_chunk]:
            for fragment in text_splitter.split_text(natural_text_chunk):
                if not fragment:
                    print("Warning: empty fragment")
                    continue

                h = hashlib.blake2b(fragment.encode(), digest_size=8).hexdigest()
                if h in hashes:
                    continue
                else:
                    hashes.append(h)

                info[sheet["surtitre"]]["chunk_len"].append(len(fragment.split()))

                chunk = data.copy()
                chunk["chunk_index"] = index
                chunk["text"] = fragment
                if isinstance(natural_chunk, dict) and "context" in natural_chunk:
                    chunk["context"] = natural_chunk["context"]
                chunks.append(chunk)
                index += 1

    json_file_target = os.path.join(basedir, "xmlfiles_as_chunks.json")
    with open(json_file_target, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=4)

    info_summary = ""
    for k, v in info.items():
        info_summary += f"### {k}\n"
        info_summary += f"total doc: {len(v['len'])}\n"
        info_summary += f"mean length: {np.mean(v['len']):.0f} ± {np.std(v['len']):.0f}    max:{np.max(v['len'])} min:{np.min(v['len'])}\n"
        info_summary += f"mean chunks length: {np.mean(v['chunk_len']):.0f} ± {np.std(v['chunk_len']):.0f}    max:{np.max(v['chunk_len'])} min:{np.min(v['chunk_len'])}\n"
        info_summary += "\n"

    chunks_fn = os.path.join(basedir, "chunks.info")
    with open(chunks_fn, "w", encoding="utf-8") as f:
        f.write(info_summary)

    print("Chunks created in", json_file_target)
    print("Chunks info created in", chunks_fn)


def parse_xml(xml_3_folders_path: str = "_data/xml", structured: bool = False) -> pd.DataFrame:
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

        if not (xml_file.split("/")[-1].startswith("N") or xml_file.split("/")[-1].startswith("F")):
            # Permet de garder uniquement les fiches pratiques,
            # fiches questions-réponses, fiches thème, fiches dossier.
            continue

        doc = parse_xml_sheet(xml_file, structured)
        if not doc:
            continue

        doc["file"] = xml_file
        docs.append(doc)

    return pd.DataFrame(docs)


def parse_questions(xml_3_folders_path: str = "_data/xml") -> pd.DataFrame:
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

        if not (xml_file.split("/")[-1].startswith("N") or xml_file.split("/")[-1].startswith("F")):
            # Permet de garder uniquement les fiches pratiques,
            # fiches questions-réponses, fiches thème, fiches dossier.
            continue

        with open(xml_file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "xml")

        # doc = get_metadata(soup)
        # doc["file"] = xml_file

        # Extract questions
        for x in soup.find_all("QuestionReponse"):
            doc = {}
            question = get_text(x)
            audience = x["audience"].lower()
            ID = x["ID"]
            url = f"https://www.service-public.fr/{audience}/vosdroits/{ID}"
            doc = {
                "question": question,
                "file": xml_file,
                "url": url,
                "tag": "QuestionReponse",
            }
            docs.append(doc)

        for x in soup.find_all("CommentFaireSi"):
            doc = {}
            question = "Comment faire si " + get_text(x) + " ?"
            audience = x["audience"].lower()
            ID = x["ID"]
            url = f"https://www.service-public.fr/{audience}/vosdroits/{ID}"
            doc = {
                "question": question,
                "file": xml_file,
                "url": url,
                "tag": "CommentFaireSi",
            }
            docs.append(doc)

    return pd.DataFrame(docs)


#
# Utils functions
#


def normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def extract(soup: Tag, tag: str, pop=True, recursive=True) -> str:
    t = soup.find(tag, recursive=recursive)
    if not t:
        return ""

    if pop:
        t.extract()

    return get_text(t)


def extract_all(soup: Tag, tag: str, pop=True) -> List[str]:
    if not soup.find(tag):
        return []

    elts = []
    for t in soup.find_all(tag):
        if pop:
            t.extract()
        elts.append(get_text(t))

    return elts


def get_text(obj):
    if isinstance(obj, NavigableString):
        text = normalize(obj.string.strip())
    else:
        text = normalize(obj.get_text(" ", strip=True))

    return text


#
# XML metier parsing
#


def get_metadata(soup):
    doc = {}
    doc["url"] = ""
    if soup.find("Publication") is not None:
        if "spUrl" in soup.find("Publication").attrs:
            doc["url"] = soup.find("Publication")["spUrl"]
    # --
    doc["audience"] = ", ".join(extract_all(soup, "Audience"))
    doc["theme"] = ", ".join(extract_all(soup, "Theme"))
    # --
    doc["surtitre"] = extract(soup, "SurTitre")  # == dc:type
    doc["subject"] = extract(soup, "dc:subject")
    doc["title"] = extract(soup, "dc:title")
    doc["description"] = extract(soup, "dc:description")
    doc["introduction"] = extract(soup, "Introduction")
    if not doc["introduction"]:
        doc["introduction"] = doc["description"]

    return doc


def parse_xml_sheet(xml_file: str, structured: bool = False) -> dict:
    """
    On utilise cette fonction pour créer un csv pour les fichiers qui commencent par N ou F.
    Ils correspondent soit à des fiches pratiques,
    soit à des questions réponses, soit à des fiches dossiers...
    """
    with open(xml_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "xml")

    doc = get_metadata(soup)

    # Content

    if structured:
        # Clean document
        # remove <OuSadresser>, <ServiceEnLigne>, <Image> (information noise + non contextual information) -> could be used to improved the chat with media information (links images, etc)
        # remove <RefActualite> (file in subfolder actualites/)
        extract_all(soup, "ServiceEnLigne")
        extract_all(soup, "OuSAdresser")
        extract_all(soup, "RefActualite")

        # Add introduction into the first chunk
        current = [doc["introduction"]]

        # Save sections for later (de-duplicate keeping order)
        sections = list(dict.fromkeys([get_text(a.Titre) for a in soup.find_all("Chapitre") if a.Titre and not a.find_parent("Chapitre")]))

        context = []
        top_list = []
        for x in soup.find_all("Publication"):
            for obj in x.children:
                if obj.name == "Texte":
                    top_list.append(obj)
                elif obj.name == "ListeSituations":
                    top_list.append(obj)
        texts = parse_structured(current, context, top_list)

        if texts:
            # Add all sections title into the first chunk
            sections = "\n".join("- " + item for item in sections)
            sections = "\n\nVoici une liste de différents cas possibles:\n" + sections
            texts[0]["text"] += sections

        doc["text"] = texts
    else:
        text = [doc["introduction"]]
        if soup.find("ListeSituations") is not None:
            text.append("Liste des situations :")
            for i, situation in enumerate(soup.find("ListeSituations").find_all("Situation")):
                situation_title = situation.find("Titre").get_text(" ", strip=True)
                situation_texte = situation.find("Texte").get_text(" ", strip=True)
                situation_title = unicodedata.normalize("NFKC", situation_title)
                situation_texte = unicodedata.normalize("NFKC", situation_texte)
                text.append("Cas n°" + str(i + 1) + " : " + situation_title + " : " + situation_texte)

        if soup.find("Publication") is not None:
            if soup.find("Publication").find("Texte", recursive=False) is not None:
                text.append(normalize(soup.find("Publication").find("Texte", recursive=False).get_text(" ", strip=True)))

        doc["text"] = [" ".join(text)]

    return doc


def parse_structured(current: List[str], context: List[str], soups: List[Tag], recurse=True, depth=0) -> List[dict]:
    # Separate text on Situation and Chapitre.
    # Keep the contexts (the history of titles) while iterating.
    #
    # Args:
    #  current: the current text of the cursor, that will be join to a string.
    #  context: the cyrrent history of title (Titre).
    #  soups: the tree cursor.
    #  recurse: continue to split chunks.
    #
    # Returns: a list of {text, context}
    #
    # @Improvments:
    # - could probably be optimized by not extracting tag, just reading it (see extract())
    # - <TitreAlternatif> can be present next to title...
    # - extraire texte et loi de référence (legifrance.fr): see <Reference>
    # -
    state = []

    for i, part in enumerate(soups):
        if isinstance(part, NavigableString):
            current.append(get_text(part))

        else:
            for j, child in enumerate(part.children):
                # Purge current
                current = [c for c in current if c]

                if isinstance(child, NavigableString):
                    current.append(get_text(child))
                    continue

                if child.name == "Situation" and recurse:
                    # New chunk
                    if current:
                        state.append({"text": current, "context": context})
                        current = []

                    if child.find("Titre", recursive=False):
                        new_context = context + [extract(child, "Titre", recursive=False)]
                    else:
                        new_context = context

                    state.extend(parse_structured([], new_context, [child], recurse=True, depth=depth + 1))
                elif child.name == "Chapitre" and recurse:
                    # New chunk
                    if current:
                        state.append({"text": current, "context": context})
                        current = []

                    if child.find("Titre", recursive=False):
                        new_context = context + [extract(child, "Titre", recursive=False)]
                    else:
                        new_context = context

                    state.extend(parse_structured([], new_context, [child], recurse=True, depth=depth + 1))
                elif child.name == "SousChapitre" and recurse:
                    # New chunk
                    if current:
                        state.append({"text": current, "context": context})
                        current = []

                    if child.find("Titre", recursive=False):
                        new_context = context + [extract(child, "Titre", recursive=False)]
                    else:
                        new_context = context

                    state.extend(parse_structured([], new_context, [child], recurse=False, depth=depth + 1))

                elif child.name == "BlocCas":
                    blocs = "\n"
                    for subchild in child.children:
                        if subchild.name != "Cas":
                            if subchild.string.strip():
                                print("XML warning: BloCas has orphan text")
                            continue

                        title = extract(subchild, "Titre", recursive=False)
                        s = parse_structured([], context, [subchild], recurse=False, depth=depth + 1)
                        content = " ".join([" ".join(x["text"]) for x in s]).strip()
                        blocs += f"Cas {title}: {content}\n"

                    current.append(blocs)
                elif child.name == "Liste":
                    blocs = "\n"
                    for subchild in child.children:
                        if subchild.name != "Item":
                            if subchild.string.strip():
                                print("XML warning: Item has orphan text")
                            continue

                        s = parse_structured([], context, [subchild], recurse=False, depth=depth + 1)
                        content = " ".join([" ".join(x["text"]) for x in s]).strip()
                        blocs += f"- {content}\n"

                    current.append(blocs)
                elif child.name == "Tableau":
                    title = extract(child, "Titre", recursive=False)
                    sep = ""
                    if not title.strip()[-1:] in string.punctuation:
                        sep = ":"
                    table = table_to_md(child)
                    table = f"\n{title}{sep}\n{table}"
                    current.append(table)
                elif child.name in ["ANoter", "ASavoir", "Attention", "Rappel"]:
                    if child.find("Titre", recursive=False):
                        current.append("({0}: {1})\n".format(extract(child, "Titre", recursive=False), get_text(child)))
                    else:
                        current.append("({0})\n".format(get_text(child)))

                elif child.name == "Titre":
                    # Format title inside chunks (sub-sub sections etc)
                    title = get_text(child)
                    sep = ""
                    if not title.strip()[-1:] in string.punctuation:
                        sep = ":"
                    current.append(f"{title}{sep}")
                else:
                    # Space joins
                    s = parse_structured(current, context, [child], recurse=recurse, depth=depth + 1)
                    current = []
                    sub_state = []
                    for x in s:
                        if len(x["context"]) == len(context):
                            # Same context
                            if child.name in ["Chapitre", "SousChapitre", "Cas", "Situation"]:
                                # add a separator
                                x["text"][-1] += "\n"
                            elif child.name in ["Paragraphe"] and child.parent.name not in ["Item", "Cellule"] and not x["text"][-1].strip()[-1:] in string.punctuation:
                                # title !
                                x["text"][-1] += ":"

                            current.extend(x["text"])
                        else:
                            # new chunk
                            sub_state.append(x)

                    if sub_state:
                        state.append({"text": current, "context": context})
                        current = []
                        state.extend(sub_state)

        # New chunk
        if current:
            state.append({"text": current, "context": context})
            current = []

    if depth == 0:
        state = [d for d in state if "".join(d["text"])]
        punctuations = (".", ",", ";")
        for d in state:
            texts = ""
            for i, x in enumerate(d["text"]):
                if not x:
                    continue

                if i > 0 and x.startswith(punctuations):
                    # Stretch join / fix punctuations extra space
                    texts += x
                elif x.startswith("\n") or texts.endswith("\n"):
                    # Strech join / do not surround newline with space
                    texts += x
                else:
                    # Space join
                    texts += " " + x

            d["text"] = texts.strip()

    return state


def table_to_md(soup):
    # @DEBUG: multi-column header are lost. See for example https://entreprendre.service-public.fr/vosdroits/F3094

    md_table = ""

    # Headers
    for row in soup.find_all("Rangée", {"type": "header"}):
        md_table += "| "
        for cell in row.find_all("Cellule"):
            md_table += get_text(cell) + " | "
        md_table += "\n"

        # Separator
        md_table += "| "
        for _ in row.find_all("Cellule"):
            md_table += "- | "
        md_table += "\n"

    # Rows
    for row in soup.find_all("Rangée", {"type": "normal"}):
        md_table += "| "
        for cell in row.find_all("Cellule"):
            md_table += get_text(cell) + " | "
        md_table += "\n"

    return md_table
