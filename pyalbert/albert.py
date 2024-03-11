"""CLI for manage the Albert assistant.

Usage:
    albert.py download_models (--hf-repo-id=<arg>) [--storage-dir=<path>] [--force-download] [--debug]
    albert.py create_whitelist [--config-file=<path>] [--storage-dir=<path>] [--debug]

Commands:
    download_models     Download models from huggingface thanks to config file. By default, files are stored under /data/models directory.
    create_whitelist    Create a whitelist file for postprocessing. By default, files are stored under /data/whitelist directory.

Options:
    --storage-dir=<path>    optional, storage path for downloaded ressources.
    --hf-repo-id=<arg>      optional, huggingface repository id to use for the download models.
    --force-download        optional, force download the model repository if they already exist. By default, False.
    --config-file=<path>    optional, path to the config file containing the routing table. By default, use corresponding file in config directory.
    --debug                 optional, print debug logs. By default, False.

Examples:
    ./albert.py download_models --config-file=/path/to/config.yml --env env --storage-dir=/path/to/storage --debug
    ./albert.py create_whitelist --config-file=/path/to/config.yml --storage-dir=/path/to/storage --debug
"""

from pathlib import Path

from docopt import docopt

if __name__ == "__main__":
    # parse CLI arguments
    args = docopt(__doc__, version="0")
    debug = True if args["--debug"] else False
    force_download = True if args["--force-download"] else False

    if args["download_models"]:
        from pyalbert.models import download_models

        storage_dir = (
            "/data/models" if args["--storage-dir"] is None else args["--storage-dir"]
        )  # if --storage-dir is not provided, use default path /data/models

        download_models(
            storage_dir=storage_dir,
            hf_repo_id=args["--hf-repo-id"],
            force_download=force_download,
            debug=debug,
        )

    if args["create_whitelist"]:
        from pyalbert.postprocessing import download_directory, create_whitelist

        storage_dir = (
            "/data/whitelist"
            if args["--storage-dir"] is None
            else args["--storage-dir"]
        )
        config_file = (
            Path(__file__).parent.resolve() / "config" / "whitelist_config.json"
            if args["--config-file"] is None
            else args["--config-file"]
        )  # if --config-file is not provided, use default path /config/whitelist_config.json
        download_directory(
            storage_dir=storage_dir, config_file=config_file, debug=debug
        )
        create_whitelist(
            storage_dir=storage_dir, config_file=config_file, debug=debug
        )
