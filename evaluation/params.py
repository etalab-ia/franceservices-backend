import os

CSV_FILE_GPT = "_data/backup/results.csv"
JSON_KEY_WORDS = os.path.join("evaluation", "keywords.json")

MOD1 = "Jean-Baptiste/camembert-ner"
MOD2 = "Jean-Baptiste/camembert-ner-with-dates"

TFIDF_MATRIX_FILE = "evaluation/tfidf_matrix.pkl"
TFIDF_FEATURE_NAMES_FILE = "evaluation/tfidf_feature_names.pkl"

KEYWORD_FREQUENCY = 1 / 150
