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

# *********
# * Utils *
# *********


def normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def get_text(obj):
    if isinstance(obj, NavigableString):
        t = obj.string.strip()
    else:
        t = obj.get_text(" ", strip=True)
    return normalize(t)


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


# ***************
# * XML parsing *
# ***************


def _get_xml_files(path):
    xml_files = []

    if os.path.isfile(path):
        # Use to test result on a particular file
        xml_files = [path]
    else:
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".xml") and file.startswith(("N", "F")):
                    # Keep only "fiches pratiques", "fiches questions-réponses",
                    # "fiches thème", "fiches dossier".
                    fullpath = os.path.join(root, file)
                    xml_files.append(fullpath)
    return xml_files


def _get_metadata(soup):
    url = ""
    if soup.find("Publication") is not None:
        if "spUrl" in soup.find("Publication").attrs:
            url = soup.find("Publication")["spUrl"]

    doc = {
        "url": url,
        "audience": ", ".join(extract_all(soup, "Audience")),
        "theme": ", ".join(extract_all(soup, "Theme")),
        "surtitre": extract(soup, "SurTitre"),
        "subject": extract(soup, "dc:subject"),
        "title": extract(soup, "dc:title"),
        "description": extract(soup, "dc:description"),
        "introduction": extract(soup, "Introduction"),
    }
    if not doc["introduction"]:
        doc["introduction"] = doc["description"]

    return doc


def _table_to_md(soup):
    # FIXME: multi-column header are lost
    #        e.g.: https://entreprendre.service-public.fr/vosdroits/F3094
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


def _not_punctuation(s):
    return s.strip()[-1:] not in string.punctuation


def _parse_xml_text_structured(
    current: List[str], context: List[str], soups: List[Tag], recurse=True, depth=0
) -> List[dict]:
    """
    Separate text on Situation and Chapitre.
    Keep the contexts (the history of titles) while iterating.

    Args:
        current: the current text of the cursor, that will be joined to a string
        context: the current history of title (Titre)
        soups: the tree cursor
        recurse: continue to split chunks

    Returns: a list of {text, context}
    """
    # TODO:
    #  - could probably be optimized by not extracting tag, just reading it; see extract()
    #  - <TitreAlternatif> can be present next to title
    #  - extract text and reference law (legifrance.fr); see <Reference>
    state = []

    for part in soups:
        if isinstance(part, NavigableString):
            current.append(get_text(part))
            # New chunk
            state.append({"text": current, "context": context})
            current = []
            continue

        for child in part.children:
            # Purge current
            current = [c for c in current if c]

            if isinstance(child, NavigableString):
                current.append(get_text(child))
                continue

            if child.name in ("Situation", "Chapitre", "SousChapitre") and recurse:
                if child.name in ("Situation", "Chapitre"):
                    new_recurse = True
                else:  # "SousChapitre"
                    new_recurse = False

                # New chunk
                if current:
                    state.append({"text": current, "context": context})
                    current = []

                title = extract(child, "Titre", recursive=False)
                if title:
                    new_context = context + [title]
                else:
                    new_context = context

                s = _parse_xml_text_structured(
                    [], new_context, [child], recurse=new_recurse, depth=depth + 1
                )
                state.extend(s)

            elif child.name in ("BlocCas", "Liste"):
                scn = "Cas" if child.name == "BlocCas" else "Item"
                blocs = "\n"
                for subchild in child.children:
                    if subchild.name != scn:
                        if subchild.string.strip():
                            print(f"XML warning: {child.name} has orphan text")
                        continue

                    if child.name == "BlocCas":
                        title = extract(subchild, "Titre", recursive=False)
                    s = _parse_xml_text_structured(
                        [], context, [subchild], recurse=False, depth=depth + 1
                    )
                    content = " ".join([" ".join(x["text"]) for x in s]).strip()

                    if child.name == "BlocCas":
                        blocs += f"Cas {title}: {content}\n"
                    else:  # Liste
                        blocs += f"- {content}\n"

                current.append(blocs)

            elif child.name == "Tableau":
                title = extract(child, "Titre", recursive=False)
                sep = ":" if _not_punctuation(title) else ""
                table = _table_to_md(child)
                table = f"\n{title}{sep}\n{table}"
                current.append(table)

            elif child.name in ("ANoter", "ASavoir", "Attention", "Rappel"):
                title = extract(child, "Titre", recursive=False)
                sep = ": " if title else ""
                current.append(f"({title}{sep}{get_text(child)})\n")

            elif child.name == "Titre":
                # Format title inside chunks (sub-sub sections etc)
                title = get_text(child)
                sep = ":" if _not_punctuation(title) else ""
                current.append(f"{title}{sep}")

            else:
                # Space joins
                s = _parse_xml_text_structured(
                    current, context, [child], recurse=recurse, depth=depth + 1
                )
                current = []
                sub_state = []
                for x in s:
                    if len(x["context"]) == len(context):
                        # Same context
                        if child.name in ("Chapitre", "SousChapitre", "Cas", "Situation"):
                            # Add a separator
                            x["text"][-1] += "\n"
                        elif (
                            child.name in ("Paragraphe",)
                            and child.parent.name not in ("Item", "Cellule")
                            and _not_punctuation(x["text"][-1])
                        ):
                            # Title !
                            x["text"][-1] += ":"

                        current.extend(x["text"])
                    else:
                        # New chunk
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


def _parse_xml_text(xml_file, structured=False):
    with open(xml_file, mode="r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "xml")

    doc = _get_metadata(soup)

    # Clean document
    # Remove <ServiceEnLigne>, <OuSadresser> (noise + non contextual information)
    # -> could be used to improve the chat with media information (links, images, etc)
    extract_all(soup, "ServiceEnLigne")
    extract_all(soup, "OuSAdresser")
    # @TODO: For resource URL: check ServiceEnLigne, OuSAdresser et LienWeb... vos-droits-et-demarche/particulier/R62483.xml
    # Remove <RefActualite> (file in subfolder actualites/)
    extract_all(soup, "RefActualite")

    # Introduction
    current = [doc["introduction"]]

    # Get all textual content
    if structured:
        # Save sections for later (de-duplicate keeping order)
        sections = [
            get_text(a.Titre)
            for a in soup.find_all("Chapitre")
            if a.Titre and not a.find_parent("Chapitre")
        ]
        sections = list(dict.fromkeys(sections))

        context = []
        top_list = []
        for x in soup.find_all("Publication"):
            for obj in x.children:
                if obj.name in ("Texte", "ListeSituations"):
                    top_list.append(obj)
        texts = _parse_xml_text_structured(current, context, top_list)

        if texts and sections:
            # Add all sections title at the end of the introduction
            sections = "\n".join(f"- {section}" for section in sections)
            sections = "\n\nVoici une liste de différents cas possibles:\n" + sections
            texts[0]["text"] += sections

    else:
        if soup.find("ListeSituations") is not None:
            current.append("Liste des situations :")
            for i, situation in enumerate(soup.find("ListeSituations").find_all("Situation")):
                situation_title = normalize(situation.find("Titre").get_text(" ", strip=True))
                situation_texte = normalize(situation.find("Texte").get_text(" ", strip=True))
                current.append(f"Cas n°{i+1} : {situation_title} : {situation_texte}")

        if soup.find("Publication") is not None:
            t = soup.find("Publication").find("Texte", recursive=False)
            if t is not None:
                current.append(normalize(t.get_text(" ", strip=True)))

        texts = [" ".join(current)]

    doc["text"] = texts
    doc["file"] = xml_file
    return doc


def _parse_xml_questions(xml_file):
    with open(xml_file, mode="r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "xml")

    docs = []
    tags = (
        ("QuestionReponse", lambda x: get_text(x)),
        ("CommentFaireSi", lambda x: f"Comment faire si {get_text(x)} ?"),
    )
    for tag, f in tags:
        for t in soup.find_all(tag):
            audience = t["audience"].lower()
            doc = {
                "question": f(t),
                "file": xml_file,
                "url": f"https://www.service-public.fr/{audience}/vosdroits/{t['ID']}",
                "tag": tag,
            }
            docs.append(doc)

    return docs


def _parse_xml(path: str, parse_type: str, structured: bool = False) -> pd.DataFrame:
    if parse_type not in ("text", "questions"):
        raise ValueError()

    xml_files = _get_xml_files(path)

    docs = []
    current_pct = 0
    n = len(xml_files)
    for i, xml_file in enumerate(xml_files):
        pct = (100 * i) // n
        if pct > current_pct:
            current_pct = pct
            print(f"Processing sheet: {current_pct}%\r", end="")

        if parse_type == "text":
            doc = _parse_xml_text(xml_file, structured=structured)
            if doc:
                docs.append(doc)
        elif parse_type == "questions":
            _docs = _parse_xml_questions(xml_file)
            docs.extend(_docs)

    return pd.DataFrame(docs)


def parse_xml(xml_3_folders_path: str = "_data/xml", structured: bool = False) -> pd.DataFrame:
    return _parse_xml(xml_3_folders_path, "text", structured=structured)


def make_chunks(directory: str, structured=False, chunk_size=1100, chunk_overlap=200) -> None:
    if structured:
        chunk_overlap = 20

    df = parse_xml(directory, structured=structured)

    # Chunkify and save to a JSON file
    basedir = "_data/"
    cols = (
        "file",
        "url",
        "surtitre",
        "theme",
        "title",
        "subject",
        "introduction",
        "text",
        "context",
    )
    chunks = []
    text_splitter = HybridSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    hashes = []
    info = defaultdict(lambda: defaultdict(list))
    for sheet in df.to_dict(orient="records"):
        data = {}
        for col in cols:
            if col in sheet:
                data[col] = sheet[col]
        texts = data["text"]
        surtitre = data["surtitre"]

        if not texts:
            continue
        if surtitre in ("Dossier", "Recherche guidée"):
            # TODO: can be used for cross-reference, see also <LienInterne>
            continue

        if structured:
            s = [x["text"] for x in texts]
        else:
            s = texts
        info[surtitre]["len"].append(len(" ".join(s).split()))

        index = 0
        for natural_chunk in texts:
            if isinstance(natural_chunk, dict):
                natural_text_chunk = natural_chunk["text"]
            else:
                natural_text_chunk = natural_chunk

            for fragment in text_splitter.split_text(natural_text_chunk):
                if not fragment:
                    print("Warning: empty fragment")
                    continue

                h = hashlib.blake2b(fragment.encode(), digest_size=8).hexdigest()
                if h in hashes:
                    print("Warning: duplicate chunk")
                    continue
                hashes.append(h)

                info[surtitre]["chunk_len"].append(len(fragment.split()))

                chunk = {
                    **data,
                    "chunk_index": index,
                    "hash": h,
                    "text": fragment,  # overwrite previous value
                }
                if isinstance(natural_chunk, dict) and "context" in natural_chunk:
                    chunk["context"] = natural_chunk["context"]
                chunks.append(chunk)
                index += 1

    json_file_target = os.path.join(basedir, "xmlfiles_as_chunks.json")
    with open(json_file_target, mode="w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=4)

    info_summary = ""
    for k, v in info.items():
        v_len = v["len"]
        v_chunk_len = v["chunk_len"]
        template = "{}: {:.0f} ± {:.0f}    max:{} min:{}\n"
        info_summary += f"### {k}\n"
        info_summary += f"total doc: {len(v_len)}\n"
        info_summary += template.format(
            "mean length", np.mean(v_len), np.std(v_len), np.max(v_len), np.min(v_len)
        )
        info_summary += f"total chunk: {len(v_chunk_len)}\n"
        info_summary += template.format(
            "mean chunks length",
            np.mean(v_chunk_len),
            np.std(v_chunk_len),
            np.max(v_chunk_len),
            np.min(v_chunk_len),
        )
        info_summary += "\n"

    chunks_fn = os.path.join(basedir, "chunks.info")
    with open(chunks_fn, mode="w", encoding="utf-8") as f:
        f.write(info_summary)

    print("Chunks created in", json_file_target)
    print("Chunks info created in", chunks_fn)


def make_questions(directory: str) -> None:
    basedir = "_data/"
    df = _parse_xml(directory, "questions")
    df = df.drop_duplicates(subset=["question"])
    q_fn = os.path.join(basedir, "questions.json")
    with open(q_fn, mode="w", encoding="utf-8") as f:
        json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=4)
    print("Questions created in", q_fn)
