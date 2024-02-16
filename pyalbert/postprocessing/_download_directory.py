import wget
import os
import shutil
import json
import requests
import traceback

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
        file_path = os.path.join(storage_dir, attributes["file_name"])

        if os.path.exists(file_path):
            if attributes["force_download"]:
                logger.info(f"{attributes['file_name']} already exists, deleting and downloading again.")
                os.remove(file_path)

            else:
                logger.info(f" {attributes['file_name']} already exists, skipping.")
                continue
        
        old_files = os.listdir(storage_dir)
        logger.debug(f"old files: {old_files}")

        logger.info(f"downloading {ressource} archive...")
        url = requests.head(attributes["url"], allow_redirects=True).url
        file_name = url.split("/")[-1]
        try:
            wget.download(attributes["url"], os.path.join(storage_dir, file_name))
        except Exception:
            logger.error(traceback.print_exc())
            exit(1)

        logger.info(f"unpacking {ressource} archive...")
        shutil.unpack_archive(os.path.join(storage_dir, file_name), storage_dir)

        logger.info(f"deleting {ressource} archive...")
        os.remove((os.path.join(storage_dir, file_name)))

        new_files = [x for x in os.listdir(storage_dir) if x not in old_files]
        logger.debug(f"new files: {new_files}")

        for file in new_files:
            if not file.endswith(".json"):
                logger.debug(f"deleting {file}...")
                os.remove(os.path.join(f"{storage_dir}", file))
                
            else:
                logger.debug(f"renaming {file}...")
                os.rename(
                    os.path.join(f"{storage_dir}", file),
                    os.path.join(f"{storage_dir}", f"{attributes['file_name']}"),
                )
        
        logger.info("Whitelist directories successfully downloaded")