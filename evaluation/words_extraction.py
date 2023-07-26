import re

import pickle
import numpy as np

from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline

### Remove the # from the following lines if "stopwords" is not installed in nltk.
# import nltk
# nltk.download("stopwords")

from nltk.corpus import stopwords

from sklearn.feature_extraction.text import TfidfVectorizer

from .params import TFIDF_FEATURE_NAMES_FILE, TFIDF_MATRIX_FILE, MOD2


def ner_fr(texte, model_name=MOD2):
    """
    This function computes NER (Name Entity Recognition) about responses, to detect locations, person name, organization name, or other name.
    This function is not fast because it uses a transformer.
    """
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(model_name)
    nlp = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")
    result_ner = nlp(texte)
    output = {"LOC": [], "PER": [], "ORG": [], "MISC": []}
    for dico in result_ner:
        type_ner = dico["entity_group"]
        if type_ner != "DATE" and dico["score"] > 0.80:
            output[type_ner].append(dico["word"])
    for key in output:
        output[key] = list(set(output[key]))

    return output


def extract_numerical_data(texte):
    """
    This function allows to extract numerical data from answers to test if these data are in the context.
    This process prevents us from hallucinations of the LLM.
    We extract :
        - Complete dates (ex : 12 mars 2023)
        - Partial dates (ex : janvier 1999)
        - Hours (ex : 9h30)
        - Prices and percentages (ex : 12.99 € / 1 000,99 $ / 50%)
        - Numbers followed by nouns (ex : 5 salariés)
        - Other numbers (numbers not followed by nouns or symbols. Ex : detects 49 in the sentence "49 et 50 salariés")

    We keep all these data in the list "complete_numerical_data"
    Ex : complete_numerical_data = ["12 mars 2023", "janvier 1999", "9h30", "12.99 €", "1 000,99 $", "50%", "5 salariés", "49"]

    In addition, we create another list named "only_numbers". This list will contain only numbers and not the symbols or nouns after.
    It will allow to search numbers in contexts. We create a second list because the formulation in contexts can be different
    from the formulation in answers, for example, ther could be spaces between numbers and symbols, or synonyms for numbers and nouns.
    Thus, we just changed two classes :
        - Prices and percentages : we keep 12.99 / 1 000.99 / 50 from 12.99 € / 1 000,99 $ / 50%
        - Numbers followed by nouns we keep 5 from "5 salariés"
    Ex : only_numbers = ["12 mars 2023", "janvier 1999", "9h30", "12.99", "1 000,99", "50", "5", "49"]
    """
    current_text = texte  # we create this var to remove numerical_data already found from the text to analyze
    complete_numerical_data = []
    only_numbers = []

    ### Complete dates
    pattern_dates_completes = r"\b(?:\d{1,2}(?:er)?\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\b"
    dates_completes = re.findall(pattern_dates_completes, current_text, re.IGNORECASE)
    complete_numerical_data += dates_completes
    only_numbers += dates_completes
    for date_complete in dates_completes:
        current_text = current_text.replace(date_complete, "")

    ### Partial Dates
    pattern_monthyear = (
        r"\b(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}\b"
    )
    monthyear = re.findall(pattern_monthyear, current_text, re.IGNORECASE)
    complete_numerical_data += monthyear
    only_numbers += monthyear
    for date in monthyear:
        current_text = current_text.replace(date, "")

    ### Hours
    pattern_hours = r"\b\d{1,2}h(?:\d{1,2})?\b"
    hours = re.findall(pattern_hours, current_text, re.IGNORECASE)
    complete_numerical_data += hours
    only_numbers += hours
    for hour in hours:
        current_text = current_text.replace(hour, "")

    ### Symbols
    pattern_symbols = r"\b(?<!\d|[,.])\d{1,3}(?:\s?\d{3})*(?:[,.]\d+)?(?:\s?[$€%£])"
    # Return number + symbol in string
    symbols = re.findall(pattern_symbols, current_text, re.IGNORECASE)
    complete_numerical_data += symbols

    pattern_symbols_tuple = r"\b(?<!\d|[,.])(\d{1,3}(?:\s?\d{3})*(?:[,\.]\d+)?)(?:\s*|$)([$€%£])"
    # Return a tuple number/symbols
    symbols_tuple = re.findall(pattern_symbols_tuple, current_text, re.IGNORECASE)
    only_numbers += [symbol_tuple[0] for symbol_tuple in symbols_tuple]

    for symbol in symbols:
        current_text = current_text.replace(symbol, "")

    ### Numbers followed by nouns
    pattern_numbernoun = r"\b(?<!\S)(\d{1,3}(?:\s?\d{3})*(?:[,\.]\d+)?)(?:\s+|$)([a-zA-ZÀ-ÿ]+)\b"
    # Return a tuple number/noun
    numbernouns = re.findall(pattern_numbernoun, current_text, re.IGNORECASE)

    # Avoid stopwords
    stop_words = stopwords.words("french") + ["est"]
    i = 0
    while i < len(numbernouns):
        if numbernouns[i][1] in stop_words:
            numbernouns.pop(i)
        else:
            i += 1
    only_numbers += [numbernoun[0] for numbernoun in numbernouns]
    numbernouns = [" ".join(numbernoun) for numbernoun in numbernouns]
    complete_numerical_data += numbernouns
    for numbernoun in numbernouns:
        current_text = current_text.replace(numbernoun, "")

    ### Other numbers
    pattern_others = r"\b(?<!\d|[,.])\d{1,3}(?:\s?\d{3})*(?:[,.]\d+)\b"
    others = re.findall(pattern_others, current_text, re.IGNORECASE)
    complete_numerical_data += others
    only_numbers += others
    for other in others:
        current_text = current_text.replace(other, "")

    assert len(only_numbers) == len(complete_numerical_data)

    return complete_numerical_data, only_numbers


def compute_tfidf(
    collection,
    tfidf_matrix_file=TFIDF_MATRIX_FILE,
    tfidf_feature_names_file=TFIDF_FEATURE_NAMES_FILE,
):
    """
    This function computes TFIDF from a collection of texts, and saves the matrix and the feature_names.
    """
    # Create an instance of the TF-IDF vectorizer
    stop_words = stopwords.words("french")
    vectorizer = TfidfVectorizer(
        stop_words=stop_words,
    )

    # Compute the TF-IDF weights for the texts in the collection
    tfidf_matrix = vectorizer.fit_transform(collection)

    feature_names = vectorizer.get_feature_names_out()

    # Save the TF-IDF matrix to a file
    with open(tfidf_matrix_file, "wb") as file:
        pickle.dump(tfidf_matrix, file)
    with open(tfidf_feature_names_file, "wb") as file:
        pickle.dump(feature_names, file)


def extract_keywords_from_tfidf_text(
    text_index,
    num_keywords=5,
    tfidf_matrix_file=TFIDF_MATRIX_FILE,
    tfidf_feature_names_file=TFIDF_FEATURE_NAMES_FILE,
):
    """
    Arguments explanation:
        - text_index : it is the index of the text of the TFIDF collection of text
        - num_keywords : number of keywords we want to extract
        - tfidf_matrix_file : the matrix with all TFIDF weights
        - tfidf_feature_names : the feature names after tfidf

    This function takes the index of a text which was used to compite TF-IDF and return the num_keywords of this text.
    """
    # Load the TF-IDF matrix from the file
    with open(tfidf_matrix_file, "rb") as file:
        tfidf_matrix = pickle.load(file)
    # Load the TF-IDF feature names from the file
    with open(tfidf_feature_names_file, "rb") as file:
        feature_names = pickle.load(file)

    # Get the TF-IDF scores for the specific text
    scores = tfidf_matrix[text_index].toarray().flatten()

    # Get the keywords with the highest TF-IDF scores for the specific text
    num_keywords = int(num_keywords)
    keyword_indices = scores.argsort()[::-1][:num_keywords]
    keywords = [feature_names[index] for index in keyword_indices]

    return keywords


def extract_keywords_from_foreign_text(
    answer,
    num_keywords=5,
    tfidf_feature_names_file=TFIDF_FEATURE_NAMES_FILE,
):
    """
    This function searches for the most relevant keywords in an answer using the precomputed TF-IDF feature names.
    This is less efficient to search keywords in a text which is not in the TF-IDF collection of texts
    than to search keywords in a text which was used to compute TF-IDF.
    """
    # Load the TF-IDF feature names from the files
    with open(tfidf_feature_names_file, "rb") as file:
        feature_names = pickle.load(file)

    # Create an instance of the TF-IDF vectorizer with the loaded feature names
    vectorizer = TfidfVectorizer(
        vocabulary=feature_names,
    )

    # Compute the TF-IDF weights for the question
    tfidf_answer = vectorizer.fit_transform([answer])

    # Get the TF-IDF scores for the question
    scores = tfidf_answer.toarray().flatten()

    # Get the keywords with the highest TF-IDF scores for the question
    keyword_indices = np.argsort(scores)[::-1][:num_keywords]
    keywords = [feature_names[index] for index in keyword_indices]

    return keywords
