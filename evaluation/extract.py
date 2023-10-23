import re
from collections import defaultdict
from typing import List

import nltk
from lexicalrichness import LexicalRichness

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")
from nltk.corpus import stopwords


def _purge(text: str, matches: List[str]) -> str:
    for m in matches:
        text = text.replace(m, "", 1)
    return text


def _remove_punctuations(text: str) -> str:
    # Remove punctuations
    text_ = text
    for s in [".", ",", ":", "-", "+"]:
        text_ = text_.replace(s, "")

    return text_


def _load_stopwords(lang: str) -> List[str]:
    stops = []
    try:
        with open(f"_data/stopwords/{lang}.txt", "r") as file:
            for line in file:
                stops.append(line.strip())
    except FileNotFoundError as e:
        raise FileNotFoundError("Stopwords language not found for lang: %s\n\n %s" % str(e))

    return stops


def extract_data(text: str) -> (str, dict):
    """Extract numerical data as well as dates, url, email and mode.
       It removes terms along the way to avoid ambiguity, so the order of extraction matters here.

    extract :
        - Complete and partial dates (ex : 12 mars 2023, janvier 1999)
        - Hours (ex : 9h30)
        - Prices and percentages (ex : 12.99 € / 1 000,99 $ / 50%)
        - Numbers followed by nouns (ex : 5 salariés)
        - Other numbers (numbers not followed by nouns or symbols. Ex : detects 49 in the sentence "49 et 50 salariés", "12.99", "1 000,99", "50", "5")

    Note: Order is important. Ex if a string like "name3310@me.io", is parsed for phone number before email, we loose it.
    """
    data_x = defaultdict(list)

    # Be markdown aware:
    # - remove all ordered list tp avoid false positive in number extraction.
    text = re.sub(r"^\d+\. ", "", text, flags=re.MULTILINE)

    # Dates
    date_pattern = [
        # dates (ex : mars, 12 mars, mars 2023, 12 mars 2023)
        r"\b(?:\d{1,2}(?:er)?\s*)?(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)(?:\s*\d{4})?\b",
    ]
    for pattern in date_pattern:
        matches = re.findall(pattern, text, re.IGNORECASE)
        data_x["dates"].extend(matches)
        text = _purge(text, matches)

    # Prices and ratios
    p_pattern = [r"\b(?<!\d|[,\.])\d{1,3}(?:\s?\d{3})*(?:[,\.]\d+)?(?:\s?[$€%£])"]
    for pattern in p_pattern:
        matches = re.findall(pattern, text, re.IGNORECASE)
        data_x["prices_"].extend(matches)
        text = _purge(text, matches)

    #
    # Location
    #

    # Email
    email_pattern = [r"(?:[\w\+\-\.]+@[\w-]+\.[\w\-\.]+)(?<![\.,])"]
    for pattern in email_pattern:
        matches = re.findall(pattern, text, re.IGNORECASE)
        data_x["emails"].extend(matches)
        text = _purge(text, matches)

    # Url
    url_pattern = [
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+(?<![\.,])",
        r"\b[\w\-\.]+\.\w{2,3}(?<![\.,])\b",
    ]
    for pattern in url_pattern:
        matches = re.findall(pattern, text, re.IGNORECASE)
        data_x["urls"].extend(matches)
        text = _purge(text, matches)

    # Phone number
    phone_pattern = [
        r"\b(?:\+?33|0)\s*\d(?:[\s\.\-]*\d{2}){4}(?<![\.,])\b",
        r"\b(?<!\S)(?:[\s\.\-]*\d{2}){2}(?<![\.,])\b",
    ]
    for pattern in phone_pattern:
        matches = re.findall(pattern, text, re.IGNORECASE)
        data_x["phones"].extend(matches)
        text = _purge(text, matches)

    #
    # Other numbers...
    #

    # Hours
    hours_pattern = [r"\b\d{1,2}[h:](?:\d{1,2})?\b"]
    for pattern in hours_pattern:
        matches = re.findall(pattern, text, re.IGNORECASE)
        data_x["hours"].extend(matches)
        text = _purge(text, matches)

    # Numbers followed by nouns
    stops_fr = stopwords.words("french")
    number_pattern = [
        # Return a tuple number/noun
        r"\b(?<!\S)(\d{1,3}(?:\s?\d{3})*(?:[,\.]\d+)?)(?:\s+|$)([a-zA-ZÀ-ÿ]+)\b",
        # orphan number
        r"\b\d+(?:\.\d+)?(?<![\.,])\b",
    ]
    data_x["numbers_"] = []
    for pattern in number_pattern:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Filter stopwords
            processed_match = []
            for i, m in enumerate(matches):
                if isinstance(m, (list, tuple)):
                    processed_match.append(" ".join([x for x in m if x not in stops_fr]))
                    text = _purge(text, [" ".join(m)])
                else:
                    processed_match.append(m)
                    text = _purge(text, [m])

            data_x["numbers_"].extend(processed_match)

    return text, data_x


def extract_artefact(text: str) -> (str, dict):
    data_x = defaultdict(list)

    # artefact
    date_pattern = [
        # prompt artefact
        r"^---",  # prompt residu
        r"^###",
        r"^<\w",  # html tag
    ]
    for pattern in date_pattern:
        matches = re.findall(pattern, text, re.IGNORECASE)
        data_x["artefacts"].extend(matches)
        text = _purge(text, matches)

    return text, data_x


def extract_repetition(text: str) -> (str, dict):
    # NOTE: if placed after extract_data, false positive will be detected because number are beeing removed
    # when they stand to differentiate two lines.
    #
    data_x = defaultdict(list)

    data_x["repetition"] = 0
    data_x["3word_repetition"] = 0

    # Remove all ordered list (1., 2. etc).

    sentences = list(filter(lambda x: x.strip() != "", text.split(". ")))
    lines = list(filter(lambda x: x.strip() != "", text.split("\n")))
    if len(sentences) - len(set(sentences)) >= 2 or len(lines) - len(set(lines)) >= 2:
        data_x["repetition"] = 1

    text_ = _remove_punctuations(text)

    pattern = r"\b(\w+)\b\s+\1\s+\1\b"
    match = re.search(pattern, text_)
    if match:
        data_x["3word_repetition"] = 1

    return text, data_x


def extract_idk(text: str) -> (str, dict):
    data_x = defaultdict(list)

    data_x["idk"] = 0

    missed_patterns = [
        "ne fournissent pas",
        "a pas d'éléments de contexte",
        "pas possible de répondre",
        "peux pas répondre",
        "je ne sais pas",
        "je ne peux pas",
    ]

    text_ = text.lower()
    for s in missed_patterns:
        if s in text_:
            data_x["idk"] = 1
            break

    return text, data_x


def extract_anglicism(text: str) -> (str, dict):
    data_x = defaultdict(list)

    data_x["lang:en"] = 0

    # Load stop words
    # @TODO: upload stopwors to etalab-ia HF space
    stops_en = _load_stopwords("en")
    stops_fr = _load_stopwords("fr") + ["an", "part", "but", "former", "due"]

    text_ = _remove_punctuations(text).split()
    for s in set(stops_en) - set(stops_fr):
        if s in text_:
            data_x["lang:en"] += 1

    return text, data_x


def extract_all(text: str) -> dict:
    data_x = {}

    # Repetitions
    _, x = extract_repetition(text)
    data_x.update(x)

    # General data
    _, x = extract_data(text)
    data_x.update(x)

    # Prompt Artefact
    _, x = extract_artefact(text)
    data_x.update(x)

    # I don"t kown the answer.
    _, x = extract_idk(text)
    data_x.update(x)

    # Lexical diversity
    lex = LexicalRichness(text)
    data_x.update(
        {
            "words": lex.words,
            "ttr": lex.ttr,
        }
    )

    _, x = extract_anglicism(text)
    data_x.update(x)

    # TODO
    # - optinnal NER extraction

    return data_x


def extract(text: str, how: str = "count") -> dict:
    """
    how: count | binary | content
    """
    data_x = extract_all(text)

    if how == "binary":
        measure = lambda x: int(len(x) > 0)
    elif how == "count":
        measure = len
    elif how == "content":
        measure = lambda x: x
    else:
        raise ValueError("metrics measure unknown: %s" % how)

    return {
        "words": data_x["words"],
        "ttr": data_x["ttr"],
        "emails": measure(data_x["emails"]),
        "urls": measure(data_x["urls"]),
        "phones": measure(data_x["phones"]),
        "dates": measure(data_x["dates"]),
        "hours": measure(data_x["hours"]),
        "prices_": measure(data_x["prices_"]),
        "number_artefacts": measure(data_x["numbers_"]),
        "prompt_artefacts": measure(data_x["artefacts"]),
        "loop": data_x["repetition"],
        # "3word_repetition": data_x["3word_repetition"],
        "idk": data_x["idk"],
        "lang:en": data_x["lang:en"],
    }
