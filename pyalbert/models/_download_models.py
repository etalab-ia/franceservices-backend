import os
import json
import shutil
import traceback

from huggingface_hub import snapshot_download

from pyalbert import Logging


def download_models(storage_dir: str, config_file: str, env: str, debug: bool = False):
    """Download huggingface models to the given storage path.

    Args:
        storage_dir (str): path where to download the files. Cache will be stored here too.
        config_file (str): path to the config file containing the routing table.
        env (str): environment to use for the download.
        debug (bool, optional): print debug logs. Defaults to False.
    """

    logging = Logging(level="DEBUG" if debug else "INFO")
    logger = logging.get_logger()

    # create the storage path if it does not exist
    os.makedirs(os.path.join(storage_dir), exist_ok=True)

    # open the config file and load the routing table
    file = open(config_file, "r")
    routing_table = json.load(file)
    file.close()

    for model, attributes in routing_table.items():
        logger.debug(f"{model} env: {attributes['env']} - current env: {env}")

        if attributes["env"] != env:
            logger.debug(f"model {model} is not available for the current environment, skipping.")
            continue

        local_dir = os.path.join(storage_dir, model)

        if os.path.exists(local_dir):
            if attributes["force_download"]:
                shutil.rmtree(local_dir)

            else:
                logger.info(f"model {model} already exists, skipping.")
                continue

        os.makedirs(local_dir, exist_ok=True)

        params = {
            "repo_id": attributes["model"],
            "local_dir": local_dir,
            "force_download": attributes["force_download"],
            "cache_dir": local_dir,
        }

        try:
            logger.info(f"downloading {model}...")
            snapshot_download(**params)

        except Exception:
            shutil.rmtree(local_dir)
            logger.error(traceback.print_exc())
            exit(1)

    logger.info("models files successfuly downloaded")
