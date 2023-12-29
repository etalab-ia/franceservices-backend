import json
import os
import re
import shutil

import wget


def download_directory(PATH: str = "_data/directory"):
    """
    A download public local and national directory in path
    Steps:
    1- Check if files exists
    2- Download .tar.bz2 and .zip files from given url
    3- Extract them
    4- Delete all not .json files
    5- Rename downloaded .json files

    Args:
        PATH (str): path where to download the directory
    """

    os.makedirs(PATH, exist_ok=True)

    url_directory_local_data = (
        "https://www.data.gouv.fr/fr/datasets/r/73302880-e4df-4d4c-8676-1a61bb997f3d"
    )
    url_directory_national_data = (
        "https://www.data.gouv.fr/fr/datasets/r/d0158eb2-6772-49c2-afb1-732e573ba1e5"
    )

    if os.path.exists(f"f{PATH}/local_data_directory.json") and os.path.exists(
        f"{PATH}/national_data_directory.json"
    ):
        print(
            "\nlocal_data_directory.json and national_data_directory.json already exist.\nFiles deleted\nDownloading files...\n"
        )
        os.remove(f"{PATH}/local_data_directory.json")
        os.remove(f"{PATH}/national_data_directory.json")
        wget.download(url_directory_local_data, f"{PATH}/local_data_directory.tar.bz2")
        wget.download(url_directory_national_data, f"{PATH}/national_data_directory.zip")
        print("\nUnpacking files...\n")
        shutil.unpack_archive(f"{PATH}/local_data_directory.tar.bz2", f"{PATH}")
        shutil.unpack_archive(f"{PATH}/national_data_directory.zip", f"{PATH}")

    else:
        print(
            "\nlocal_data_directory and national_data_directory don't exist.\nDownloading files...\n"
        )
        wget.download(url_directory_local_data, f"{PATH}/local_data_directory.tar.bz2")
        wget.download(url_directory_national_data, f"{PATH}/national_data_directory.zip")

        print("\nUnpacking files...\n")
        shutil.unpack_archive(f"{PATH}/local_data_directory.tar.bz2", f"{PATH}")
        shutil.unpack_archive(f"{PATH}/national_data_directory.zip", f"{PATH}")
        print("\nFiles unpacked")

    for f in os.listdir(f"{PATH}"):
        if not f.endswith(".json"):
            os.remove(os.path.join(f"{PATH}", f))
        if f.endswith("data.gouv_local.json"):
            os.rename(
                os.path.join(f"{PATH}", f),
                os.path.join(f"{PATH}", "local_data_directory.json"),
            )
        if f.startswith("dila_refOrga_admin_Etat_fr"):
            os.rename(
                os.path.join(f"{PATH}", f),
                os.path.join(f"{PATH}", "national_data_directory.json"),
            )

    print("\nDirectoty files successfuly downloaded")


def create_whitelist(PATH: str = "_data/directory"):
    """
    Creating a .json whitelist file which contains:
    - All phone numbers
    - All mail
    - All domain URL
    Extracted from local and national directory

    Args:
        PATH (str): path where to download the directory
    """
    whitelist = dict()
    phone_list = []
    mail_list = []
    domain_list = []

    ### Loading directories
    with open(f"{PATH}/local_data_directory.json") as json_file:
        local_data_directory = json.load(json_file)
        local_data_directory = local_data_directory["service"]

    with open(f"{PATH}/national_data_directory.json") as json_file:
        national_data_directory = json.load(json_file)
        national_data_directory = national_data_directory["service"]

    ### Creating domain URL whitelist
    for k in range(len(local_data_directory)):
        if (
            local_data_directory[k]["site_internet"] != []
            and local_data_directory[k]["site_internet"][0]["valeur"] != ""
        ):
            domain_list.append(local_data_directory[k]["site_internet"][0]["valeur"])

    for k in range(len(national_data_directory)):
        if (
            national_data_directory[k]["site_internet"] != []
            and national_data_directory[k]["site_internet"][0]["valeur"] != ""
        ):
            domain_list.append(national_data_directory[k]["site_internet"][0]["valeur"])

    ### Creating phone numbers whitelist
    pattern = [
        r"(?:\+\d{,3}|0)?\s*\([\d\s]*\)(?:[\s\.\-]*\d{2,}){2,}",
        r"(?<!\d)(?:\+\d{,3}|0)\s*\d(?:[\s\.\-]*\d{2}){4}(?<![\.,])",
        r"(?<![\d\)]\s)\d{2}[\s\.\-]*\d{2}(?![\s\.\-]\d)",
        r"(?<!\d)0\s*(?:[\s\.\-]*\d{3}){3}(?<![\.,])",
        r"(?<!\d)0\d\s*\d{2}(?:[\s\.\-]*\d{3}){2}(?<![\.,])",
    ]

    for k in range(len(local_data_directory)):
        if (
            local_data_directory[k]["telephone"] != []
            and local_data_directory[k]["telephone"][0]["valeur"] != ""
        ):
            for pat in pattern:
                matches = re.findall(pat, local_data_directory[k]["telephone"][0]["valeur"])
                phone_list.extend(matches)

    for k in range(len(national_data_directory)):
        if (
            national_data_directory[k]["telephone"] != []
            and national_data_directory[k]["telephone"][0]["valeur"] != ""
        ):
            for pat in pattern:
                matches = re.findall(pat, national_data_directory[k]["telephone"][0]["valeur"])
                phone_list.extend(matches)

    ### Creating mail whitelist

    for k in range(len(local_data_directory)):
        if local_data_directory[k]["adresse_courriel"] != []:
            mail_list.append(local_data_directory[k]["adresse_courriel"][0])

    for k in range(len(national_data_directory)):
        if national_data_directory[k]["adresse_courriel"] != []:
            mail_list.append(national_data_directory[k]["adresse_courriel"][0])

    whitelist["phone_number_list"] = phone_list
    whitelist["mail_list"] = mail_list
    whitelist["domain_url_list"] = domain_list

    whitelist_json = json.dumps(whitelist, indent=4)
    with open(f"{PATH}/whitelist.json", "w") as file:
        file.write(whitelist_json)
