"""CLI for manage the Albert assistant.

Usage:
    albert.py download_models (--config-file=<path>) (--env=<arg>) [--storage-dir=<path>] [--debug]

Commands:
    download_models     Download models from huggingface thanks to config file. By default, files are stored under /data/models directory.

Options:
    --storage-dir=<path>    Storage path for downloaded ressources.
    --config-file=<path>    Path to the config file containing the routing table.
    --env=<arg>             Environment to use for the download.
    --debug                 Print debug logs.

Examples:
    ./albert.py download_models
"""

from docopt import docopt

if __name__ == "__main__":
    # parse CLI arguments
    args = docopt(__doc__, version="0")

    if args["download_models"]:
        from pyalbert.models import download_models

        storage_dir = "/data/models" if args["--storage-dir"] is None else args["--storage-dir"] # if --storage-dir is not provided, use default path /data/models
        debug = True if args["--debug"] else False
        download_models(storage_dir=storage_dir, config_file=args["--config-file"], env=args["--env"], debug=debug)
