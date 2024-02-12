"""CLI for manage the Albert assistant.

Usage:
    albert.py download_models (--env=<arg) [--config-file=<path>] [--storage-dir=<path>] [--debug]
    albert.py create_whitelist [--config-file=<path>] [--storage-dir=<path>] [--debug]

Commands:
    download_models     Download models from huggingface thanks to config file. By default, files are stored under /data/models directory.
    create_whitelist    Create a whitelist file for postprocessing. By default, files are stored under /data/whitelist directory.

Options:
    --storage-dir=<path>    Optional, storage path for downloaded ressources.
    --config-file=<path>    Optional, path to the config file containing the routing table. By default, use corresponding file in config directory.
    --env=<arg>             Environment to use for the download models.
    --debug                 Optional, print debug logs.

Examples:
    ./albert.py download_models --config-file=/path/to/config.yml --env env --storage-dir=/path/to/storage --debug
    ./albert.py create_whitelist --config-file=/path/to/config.yml --storage-dir=/path/to/storage --debug
"""

import os
from pathlib import Path

from docopt import docopt

if __name__ == "__main__":
    # parse CLI arguments
    args = docopt(__doc__, version="0")
    debug = True if args["--debug"] else False

    if args["download_models"]:
        from pyalbert.models import download_models

        storage_dir = (
            "/data/models" if args["--storage-dir"] is None else args["--storage-dir"]
        )  # if --storage-dir is not provided, use default path /data/models
        config_file = (
            os.path.join(Path().absolute(), "config", "vllm_routing_table.json")
            if args["--config-file"] is None
            else args["--config-file"]
        ) # if --config-file is not provided, use default path /config/vllm_routing_table.json

        download_models(
            storage_dir=storage_dir,
            config_file=args["--config-file"],
            env=args["--env"],
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
            os.path.join(Path().absolute(), "config", "whitelist_config.json")
            if args["--config-file"] is None
            else args["--config-file"]
        ) # if --config-file is not provided, use default path /config/whitelist_config.json

        download_directory(
            storage_dir=storage_dir, config_file=args["--config-file"], debug=debug
        )
        create_whitelist(
            storage_dir=storage_dir, config_file=args["--config-file"], debug=debug
        )
