import hashlib
import json
import os
import string
import unicodedata
from collections import defaultdict

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from langchain_text_splitters import RecursiveCharacterTextSplitter

# *********
# * Utils *
# *********


def normalize(text: str) -> str:
    # Like removing non-breaking space in latin-1 (\xa0)
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


def extract_all(soup: Tag, tag: str, pop=True) -> list[str]:
    if not soup.find(tag):
        return []

    elts = []
    for t in soup.find_all(tag):
        if pop:
            t.extract()
        elts.append(get_text(t))

    return elts


# ***************
# * Sheet parsing *
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
    return sorted(xml_files)


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
    current: list[str], context: list[str], soups: list[Tag], recurse=True, depth=0
) -> list[dict]:
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


def _parse_xml_text(xml_file, structured=False) -> dict:
    with open(xml_file, mode="r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "xml")

    doc = _get_metadata(soup)
    doc["sid"] = doc["url"].split("/")[-1]
    doc["source"] = "service-public"

    # Clean document / Remove potential noise
    extract_all(soup, "OuSAdresser")
    extract_all(soup, "RefActualite")

    def drop_duplicates(data: list[dict], k: str):
        seen = []
        keeps = []
        for x in data:
            if x[k] in seen:
                continue

            keeps.append(x)
            seen.append(x[k])

        return keeps

    def sp_url_encoder(sid, audience):
        audience_to_uri = {
            "Associations": "associations",
            "Particuliers": "particuliers",
            "Professionnels": "professionnels-entreprises",
        }
        # Do not fail silently
        audience_uri = audience_to_uri[audience]
        return f"https://www.service-public.fr/{audience_uri}/vosdroits/{sid}"

    # Get related questions
    questions = [
        {"question": get_text(q), "sid": q["ID"], "url": sp_url_encoder(q["ID"], q["audience"])}
        for q in soup.find_all("QuestionReponse")
    ]
    questions = drop_duplicates(questions, "question")
    doc["related_questions"] = questions

    # Get the Service/contact ressources
    web_services = [
        {
            "title": normalize(q.find("Titre").get_text(" ", strip=True)),
            "institution": normalize(q.find("Source").get_text(" ", strip=True)),
            "url": q["URL"],
            "type": q["type"],
        }
        for q in soup.find_all("ServiceEnLigne")
        if q.get("URL")
    ]
    web_services = drop_duplicates(web_services, "title")
    doc["web_services"] = web_services

    # Clean document / Remove potential noise
    extract_all(soup, "OuSAdresser")
    extract_all(soup, "ServiceEnLigne")
    extract_all(soup, "QuestionReponse")
    extract_all(soup, "RefActualite")

    # Get all textual content
    # --
    # Introduction
    current = [doc["introduction"]]
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
            sections = (
                "\n\nVoici une liste de différentes questions ou thématiques relatives à ce sujet :\n"
                + sections
            )
            texts[0]["text"] += sections

    else:
        if soup.find("ListeSituations") is not None:
            current.append("Liste des situations :")
            for i, situation in enumerate(soup.find("ListeSituations").find_all("Situation")):
                if not situation.find("Titre"):
                    print("warning: Situation > Titre, not found")
                    continue

                if not situation.find("Texte"):
                    print("warning: Situation > Texte, not found")
                    continue

                situation_title = normalize(situation.find("Titre").get_text(" ", strip=True))
                situation_texte = normalize(situation.find("Texte").get_text(" ", strip=True))
                current.append(f"Cas n°{i+1} : {situation_title} : {situation_texte}")

        if soup.find("Publication") is not None:
            t = soup.find("Publication").find("Texte", recursive=False)
            if t is not None:
                current.append(normalize(t.get_text(" ", strip=True)))

        texts = [" ".join(current)]

    doc["text"] = texts
    return doc


def _parse_xml_questions(xml_file: str) -> list[dict]:
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
                "url": f"https://www.service-public.fr/{audience}/vosdroits/{t['ID']}",
                "tag": tag,
            }
            docs.append(doc)

    return docs


def _parse_xml(target_dir: str, parse_type: str, structured: bool = False) -> list[dict]:
    if parse_type not in ("text", "questions"):
        raise ValueError()

    if not os.path.exists(target_dir):
        raise FileNotFoundError(f"path {target_dir} to xml sheets not found.")

    xml_files = _get_xml_files(target_dir)

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

    return docs


def _parse_travailEmploi(target_dir: str, structured: bool = False) -> list[dict]:
    with open(os.path.join(target_dir, "fiches-travail.json")) as f:
        data = json.load(f)

    if structured:

        def join_sections(sections):
            texts = []
            for section in sections:
                texts.append(
                    {
                        "text": normalize(section["text"]),
                        "context": [normalize(section["title"])],
                    }
                )
            return texts

    else:

        def join_sections(sections):
            text = ""
            for section in sections:
                text += normalize(f'{section["title"]}\n\n{section["text"]}')

            return [text]

    docs = []
    for doc in data:
        sheet = {
            "title": normalize(doc["title"]),
            "url": doc["url"],
            "date": doc["date"],
            "sid": doc["pubId"],
            "introduction": get_text(BeautifulSoup(doc["intro"], "html.parser")),
            "text": join_sections(doc["sections"]),
            "surtitre": "Travail-Emploi",
            "source": "travail-emploi",
        }

        docs.append(sheet)

    return docs


def make_chunks(
    storage_dir: str,
    structured=False,
    chunk_size=8000,
    chunk_overlap=800,
    sources=None,
) -> None:
    """Chunkify sheets and save to a JSON file"""

    if structured:
        chunk_overlap = 20

    if sources is None:
        raise ValueError("You must give a list of source to chunkify in the param 'sources'.")

    sheets = RagSource.get_sheets(storage_dir, sources, structured=structured)

    chunks = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    hashes = []
    info = defaultdict(lambda: defaultdict(list))
    for data in sheets:
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

                info[surtitre]["chunk_len"].append(len(fragment.split()))

                chunk = {
                    **data,
                    "chunk_index": index,
                    "text": fragment,  # overwrite previous value
                }
                if isinstance(natural_chunk, dict) and "context" in natural_chunk:
                    chunk["context"] = natural_chunk["context"]
                    chunk_content = "".join(chunk["context"]) + fragment
                else:
                    chunk_content = fragment

                # add an unique hash/id
                h = hashlib.blake2b(chunk_content.encode(), digest_size=8).hexdigest()
                if h in hashes:
                    # print("Warning: duplicate chunk (%s)" % chunk["sid"])
                    # print(chunk_content)
                    continue
                hashes.append(h)
                chunk["hash"] = h

                chunks.append(chunk)
                index += 1

    json_file_target = os.path.join(storage_dir, "sheets_as_chunks.json")
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

    chunks_fn = os.path.join(storage_dir, "chunks.info")
    with open(chunks_fn, mode="w", encoding="utf-8") as f:
        f.write(info_summary)

    print("Chunks created in", json_file_target)
    print("Chunks info created in", chunks_fn)


def make_questions(storage_dir: str) -> None:
    target_dir = storage_dir
    if storage_dir.split("/")[-1].strip("/") != "data.gouv":
        target_dir = os.path.join(storage_dir, "data.gouv")
    questions = _parse_xml(target_dir, "questions")
    df = pd.DataFrame(questions)
    df = df.drop_duplicates(subset=["question"])
    questions = df.to_dict(orient="records")
    q_fn = os.path.join(storage_dir, "questions.json")
    with open(q_fn, mode="w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=4)
    print("Questions created in", q_fn)


class RagSource:
    SERVICE_PUBLIC = "service-public"
    TRAVAIL_EMPLOI = "travail-emploi"

    # At this point a sheet is an hyvrid dict data structure with with only a set of mandatory fields:
    # - "sid" -> unique identifier
    # - "title -> sheet title
    # - "text" -> main payload
    # - "context" -> successive subtitle (if structured=True)
    # - "source" -> The source of the sheet (service-public, vie-publique, legifrance, etc)
    # - "url" -> URL of the source
    # Depending on the source, they can have many more attribute...

    @classmethod
    def is_valid(cls, source):
        return source in cls.__dict__.values()

    @classmethod
    def get_sheets(
        cls, storage_dir: str | None, sources: str | list[str], structured: bool = False
    ):
        if not storage_dir:
            raise ValueError("You must give a storage directory.")

        if isinstance(sources, str):
            sources = [sources]

        for source in sources:
            if not cls.is_valid(source):
                raise ValueError("This RAG source is not known: %s" % source)

        sheets = []
        for source in sources:
            if source == cls.SERVICE_PUBLIC:
                # storage_dir: the base path where files are gonna be written.
                # target_dir: read-only base path where sheets are read.
                target_dir = storage_dir
                if storage_dir.split("/")[-1].strip("/") != "data.gouv":
                    target_dir = os.path.join(storage_dir, "data.gouv")

                sheets.extend(_parse_xml(target_dir, "text", structured=structured))
            elif source == cls.TRAVAIL_EMPLOI:
                target_dir = storage_dir
                sheets.extend(_parse_travailEmploi(target_dir, structured=structured))
            else:
                raise NotImplementedError("Rag source unknown")

        return sheets
