import re
from collections import defaultdict
from typing import List

from lexicalrichness import LexicalRichness
import nltk

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")
from nltk.corpus import stopwords


def _purge(text: str, matches: List[str]) -> str:
    for m in matches:
        text = text.replace(m, "", 1)
    return text


def extract_data(text: str) -> (str, dict):
    """Extract numerical data, by removing terms along the way.

    extract :
        - Complete and partial dates (ex : 12 mars 2023, janvier 1999)
        - Hours (ex : 9h30)
        - Prices and percentages (ex : 12.99 € / 1 000,99 $ / 50%)
        - Numbers followed by nouns (ex : 5 salariés)
        - Other numbers (numbers not followed by nouns or symbols. Ex : detects 49 in the sentence "49 et 50 salariés", "12.99", "1 000,99", "50", "5")

    Note: Order is important. Ex if a string like "name3310@me.io", is parsed for phone number before email, we loose it.
    """
    data_x = defaultdict(list)

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


def extract(text: str) -> dict:

    # General data
    data_x = {}
    _, x = extract_data(text)
    data_x.update(x)

    # Prompt Artefact
    _, x = extract_artefact(text)
    data_x.update(x)

    # Lexical diversity
    lex = LexicalRichness(text)
    data_x.update({
        "words": lex.words,
        "ttr": lex.ttr,
    })

    # TODO
    # - Add number of english words.
    # - optinnal NER extraction

    return data_x
