from .xml_parsing import parse_xml
from .create_json import create_json_db

# For xml parsing:
from .params import SAVE_PATH_CSV, XML_3_FOLDERS_PATH

# For create json :
from .params import CSV_PATH, JSON_PARSED_PATH

# For chunk json
from .params import JSON_FILE_SOURCE, JSON_FILE_TARGET


def complete_parsing(
    save_path_xml=SAVE_PATH_CSV,
    xml_3_folders_path=XML_3_FOLDERS_PATH,
    csv_path=CSV_PATH,
    json_organized_path=JSON_PARSED_PATH,
    json_file_source=JSON_FILE_SOURCE,
    json_file_target=JSON_FILE_TARGET,
):
    parse_xml(save_path_xml, xml_3_folders_path)
    create_json_db(csv_path, json_organized_path, json_file_source, json_file_target)
