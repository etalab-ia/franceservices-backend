import csv
import json
import nltk

from .words_extraction import (
    ner_fr,
    extract_numerical_data,
    compute_tfidf,
    extract_keywords_from_tfidf_text,
)

from .params import (
    CSV_FILE_GPT,
    JSON_KEY_WORDS,
    TFIDF_MATRIX_FILE,
    TFIDF_FEATURE_NAMES_FILE,
    KEYWORD_FREQUENCY,
)

nltk.download("stopwords", quiet=True)


def calculate_tfidf(csv_file_gpt=CSV_FILE_GPT) -> None:
    """
    This function creates the TFIDF model from answers of GPT.
    WARNING : the csv in argument has to be in a particular format (if you want to recalculate the tfidf,
    you have to check your csv is similar to CSV_FILE_GPT)
    It uses the 20 000 answers to compute TFIDF.
    You can run this function if you want to update the TFIDF if there are new answers, in order to get the TFIDF more accurate.
    """
    answers_gpt = []
    with open(csv_file_gpt, "r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=";", quotechar='"')
        next(reader)
        for row in reader:
            if len(row) > 1:
                answers_gpt.append(row[1])
        compute_tfidf(
            answers_gpt,
            tfidf_matrix_file=TFIDF_MATRIX_FILE,
            tfidf_feature_names_file=TFIDF_FEATURE_NAMES_FILE,
        )


def crucial_words_tfidf_textcollection(
    csv_file_gpt=CSV_FILE_GPT,
    json_key_words=JSON_KEY_WORDS,
    keyword_frequency=KEYWORD_FREQUENCY,
    compute_ner=False,
):
    """
    This function allows to create a jsonfile which contains the import words in a dataset.
    It is necessary that you computed the "calculate_tfidf" fonction on this dataset before launching
    the "crucial_words_tfidf_textcollection" function.
    We return a list of dictionnaries (a dictionnary by answer in the dataset).
    Each dictionnary contains :
        - The question
        - The index of the question in the csv file
        - The output of NER (name entity recognition) # We advice you not to calculate it beacuse it is very long.
            The argument "" of the function allow you to change it
        - The numerical data : a dictionnary with complete_numerical_data in keys,
            and True in value if the number is in context and False if not
        - The tfidf keywords : a dictionnary with tfidf keywords in keys,
            and the count of these keywords in the context for the value

    Example :
    {
    "question": "Quels sont les documents à fournir pour faire une demande de visa de long séjour en France?",
    "index": 4,
    "output_ner": {},
    "numerical_data": {
      "62 899,2 €": true,
      "10 ans": true,
      "3 mois": true,
    },
    "key_words_tfidf": {
      "supplément": 0,
      "référence": 3,
    }
    }
    """
    output_list = []
    with open(csv_file_gpt, "r", encoding="utf-8") as source_file:
        reader = csv.reader(source_file, delimiter=";", quotechar='"')
        next(reader)
        for answer_index, row in enumerate(reader):
            question_gpt = row[0]
            answer_gpt = row[1]
            context = row[2]
            ## Compute ner if wanted
            if compute_ner:
                output_ner = ner_fr(answer_gpt)
            else:
                output_ner = {}

            # Search numerical data in answers
            numerical_data, numbers_to_test = extract_numerical_data(answer_gpt)
            # Now check if numerical data are in contexts.
            # As explained in words_extraction.py, we check only the numbers in the context,
            # and not the potential symbols or nouns after the numbers
            output_numerical_data = {}
            for index, numbertext in enumerate(numerical_data):
                if numbers_to_test[index] in context:
                    output_numerical_data[numbertext] = True
                else:
                    output_numerical_data[numbertext] = False
            # Search TF-IDF keywords
            key_words_tfidf = extract_keywords_from_tfidf_text(
                answer_index,
                num_keywords=len(answer_gpt) // (1 / keyword_frequency),
                tfidf_matrix_file=TFIDF_MATRIX_FILE,
                tfidf_feature_names_file=TFIDF_FEATURE_NAMES_FILE,
            )
            # Count how many times keywords are in contexts
            output_key_words_tfidf = {}
            for word in key_words_tfidf:
                output_key_words_tfidf[word] = context.lower().split().count(word)

            dico_key_words = {
                "question": question_gpt,
                "index": answer_index,
                "output_ner": output_ner,
                "numerical_data": output_numerical_data,
                "key_words_tfidf": output_key_words_tfidf,
            }
            output_list.append(dico_key_words)
    with open(json_key_words, "w", encoding="utf-8") as target_file:
        json.dump(output_list, target_file, ensure_ascii=False)
