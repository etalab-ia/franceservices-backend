import os
import shutil

import wget


def download_corpus(PATH: str = "_data/"):
    """Download french data corpus that power the RAG system.

    Args:
        PATH (str): path where to download the directory
    """

    os.makedirs(PATH, exist_ok=True)

    corpus_data = [
        {
            "nameid": "experiences",
            "url": "https://opendata.plus.transformation.gouv.fr/api/explore/v2.1/catalog/datasets/export-expa-c-riences/exports/json",
            "output": "export-expa-c-riences.json",
        },
        {
            "nameid": "vdd",
            "url": "https://lecomarquage.service-public.fr/vdd/3.3/part/zip/vosdroits-latest.zip",
            "output": "data.gouv/",
            "format": "zip",
        },
        {
            "nameid": "travail",
            "url": "https://github.com/SocialGouv/fiches-travail-data/raw/master/data/fiches-travail.json",
            "output": "fiches-travail.json",
        },
    ]

    if not os.path.exists(f"{PATH}/data.gouv"):
        os.makedirs(f"{PATH}/data.gouv")

    for corpus in corpus_data:
        print(f"Dowloading '{corpus['nameid']}'...\n")
        last_name = corpus["url"].split("/")[-1]
        target = f"{PATH}/{corpus['output']}"
        wget.download(corpus["url"], f"{PATH}/temp_{last_name}")
        if corpus.get("format"):
            shutil.unpack_archive(f"{PATH}/temp_{last_name}", extract_dir=target, format=corpus["format"])
        else:
            shutil.move(f"{PATH}/temp_{last_name}", target)
        print()

    print("\nCorpus files successfuly downloaded")
