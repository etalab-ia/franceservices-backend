import os

# To create parsed_csv from xml :

XML_3_FOLDERS_PATH = "_data/xml_files"
SAVE_PATH_CSV = "_data/csv_database/xml_parsed.csv"

# To create a json_database

CSV_PATH = os.path.join("_data/csv_database", "xml_parsed.csv")
JSON_PARSED_PATH = os.path.join("_data/json_database", "files.json")

DATA_COLUMN = ["introduction", "liste_situations", "other_content"]
METADATA_COLUMN = ["file", "title", "xml_url", "surtitre", "subject", "theme"]

# Code to chunk data

JSON_FILE_SOURCE = os.path.join("_data/json_database", "files.json")
JSON_FILE_TARGET = os.path.join("_data/json_database", "xmlfiles_as_chunks.json")
