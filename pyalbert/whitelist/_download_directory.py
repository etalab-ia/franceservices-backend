import json
import os
import shutil
import traceback
from urllib.request import urlopen

import requests
import wget

from pyalbert import Logging


def download_directory(
    storage_dir: str,
    config_file: str,
    debug: bool = False,
):
    """
    A download public local and national directory to create whitelist file.

    Args:
        storage_dir (str): path where to download the files.
        config_file (str,): configuration path file.
        debug (bool, optional): print debug logs. Defaults to False.
    """

    logging = Logging(level="DEBUG" if debug else "INFO")
    logger = logging.get_logger()

    os.makedirs(storage_dir, exist_ok=True)

    # Open whitelist_config
    file = open(config_file, "r")
    whitelist_config = json.load(file)
    file.close()

    for ressource, attributes in whitelist_config["directories"].items():
        if os.path.exists(os.path.join(storage_dir, attributes["output"])):
            if attributes["force_download"]:
                logger.info(
                    f"{attributes['output']} already exists, deleting and downloading again."
                )
                try:
                    shutil.rmtree(os.path.join(storage_dir, attributes["output"]))
                except NotADirectoryError:
                    os.remove(os.path.join(storage_dir, attributes["output"]))

            else:
                logger.info(f"{attributes['output']} already exists, skipping.")
                continue

        old_files = os.listdir(storage_dir)
        logger.debug(f"old files: {old_files}")

        logger.info(f"downloading {ressource} archive...")
        url = requests.head(attributes["url"], allow_redirects=True).url
        info = urlopen(url).info()
        file = info.get_filename() if info.get_filename() else os.path.basename(url)

        try:
            wget.download(attributes["url"], os.path.join(storage_dir, file))
        except Exception:
            logger.error(traceback.print_exc())
            exit(1)

        logger.info(f"unpacking {ressource} archive...")
        shutil.unpack_archive(os.path.join(storage_dir, file), storage_dir)

        logger.info(f"deleting {ressource} archive...")
        os.remove((os.path.join(storage_dir, file)))

        new_files = [x for x in os.listdir(storage_dir) if x not in old_files]
        logger.debug(f"new files: {new_files}")

        for file in new_files:
            if not file.endswith(".json"):
                logger.debug(f"deleting {file}...")
                os.remove(os.path.join(storage_dir, file))

            else:
                logger.debug(f"renaming {file} to {attributes['output']}...")
                os.rename(
                    os.path.join(storage_dir, file),
                    os.path.join(storage_dir, attributes["output"]),
                )

        logger.info("Whitelist directories successfully downloaded")
