import os
import shutil
import traceback

from huggingface_hub import snapshot_download

from pyalbert import Logging


def download_models(
    storage_dir: str, hf_repo_id: str, force_download: bool = True, debug: bool = False
):
    """Download huggingface models to the given storage path.

    Args:
        storage_dir (str): path where to download the files. Cache will be stored here too.
        hf_repo_id (str): huggingface repository id to download the models from.
        force_download (bool, optional): force download the model repository if they already exist. Defaults to True.
        debug (bool, optional): print debug logs. Defaults to False.
    """

    logging = Logging(level="DEBUG" if debug else "INFO")
    logger = logging.get_logger()

    # create the storage path if it does not exist
    os.makedirs(os.path.join(storage_dir), exist_ok=True)
    local_dir = os.path.join(storage_dir, hf_repo_id)

    if os.path.exists(local_dir):
        if force_download:
            logger.debug(f"{hf_repo_id} already exists, removing it.")
            shutil.rmtree(local_dir)

        else:
            logger.info(f"{hf_repo_id} already exists, skipping.")
            return

    os.makedirs(local_dir, exist_ok=True)

    params = {
        "repo_id": hf_repo_id,
        "local_dir": local_dir,
        "force_download": force_download,
        "cache_dir": local_dir,
    }

    try:
        logger.info(f"downloading {hf_repo_id}...")
        snapshot_download(**params)

    except Exception:
        shutil.rmtree(local_dir)
        logger.error(traceback.print_exc())
        exit(1)

    logger.info("models files successfuly downloaded")
