#!/usr/bin/env python

"""The Albert CLI.

Usage:
    pyalbert create_whitelist [--config-file=<path>] [--storage-dir=<path>] [--debug]
    pyalbert download_rag_sources [--config-file=<path>] [--storage-dir=<path>] [--debug]
    pyalbert make_chunks [--structured] [--chunk-size N] [--chunk-overlap N] [--storage-dir=<path>]
    pyalbert index <index_name> [--index-type=<index_type>] [--batch-size N] [--recreate] [--storage-dir=<path>]
    pyalbert show_indexes

Commands:
    create_whitelist           Create a whitelist file for postprocessing. By default, files are stored under /data/whitelist directory.

    download_rag_sources       Download public services source of data. Downloaded data should consitute the inputs for the further processing steps that feed the RAG.

    make_chunks                Parse XML files from data.gouv (public service sheets), located in the DIRECTORY folder to transform them into sheets in Json format.
                               Each Json element corresponds to a piece of sheet with a length of 1000 characters called chunk, cut while keeping sentences intact.
                               Chunks are created under <path>/sheets_as_chunks.json

    index                      Create the given index to search relevant document given a query, loading data from <path>. Each index is created using a specific sourcs as ground-truth.
                               See the docs to see which sources are used by which index.
    show_indexes               Show search engines indexes.

Options:
    --storage-dir=<path>       Storage path for downloaded ressources.
    --config-file=<path>       Path to the config file containing the routing table. By default, use corresponding file in config directory.
    --structured               Parse strategy that exploit the xml sheet structure.
    --chunk-size N             The maximum size of the chunks (token count...) [default: 1100]
    --chunk-overlap N          The size of the overlap between chunks [default: 200]
    --batch-size N             The embedding batch size when creating a collection [default: 10]
    --index-type=<index_type>  The type of index to create (elasticsearch, qdrant) [default: elasticsearch]
    --recreate                 Force collection/index recreation
    --debug                    optional, print debug logs. By default, False.

Examples:
    pyalbert create_whitelist --storage-dir <path>
    pyalbert download_rag_sources --storage-dir <path>
    pyalbert make_chunks --chunk-size 500 --chunk-overlap 20
    pyalbert make_chunks --structured --storage-dir <path>
    pyalbert index experiences --storage-dir <path>  # assumes <path>/export-expa-c-riences.json exists
    pyalbert index sheets --storage-dir <path>       # assumes <path>/data.gouv/ + _data/fiches-travail.json exist
    pyalbert index chunks --storage-dir <path>       # assumes <path>/sheets_as_chunks.json + _data/fiches-travail.json exist
"""

import sys
from pathlib import Path

from docopt import docopt

# Allow `python pyalbert/albert.py` and `cd pyalbert/python ./albert.py` to work whithout needed to edit the PYTHONPATH
local_parent_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(local_parent_dir))


from pyalbert import __version__, get_logger
from pyalbert.config import SHEET_SOURCES

logger = get_logger()


def main():
    # Parse CLI arguments
    args = docopt(__doc__, version=__version__)
    debug = True if args["--debug"] else False

    if args["create_whitelist"]:
        from pyalbert.whitelist import create_whitelist, download_directory

        # if --storage-dir is not provided, use default path /data/whitelist
        storage_dir = "/data/whitelist" if args["--storage-dir"] is None else args["--storage-dir"]

        # @DEBUG: this modularity has side effect since the whiltelist path is hardcoded
        #         in the prompt.postprocessing module that uses this file...
        config_file = (
            Path(__file__).resolve().parent / "config" / "whitelist_config.json"
            if args["--config-file"] is None
            else args["--config-file"]
        )  # if --config-file is not provided, use default path /config/whitelist_config.json
        download_directory(storage_dir=storage_dir, config_file=config_file, debug=debug)
        create_whitelist(storage_dir=storage_dir, config_file=config_file, debug=debug)

    elif args["download_rag_sources"]:
        from pyalbert.corpus import download_rag_sources

        # if --storage-dir is not provided, use default path /data/sources
        storage_dir = "/data/sources" if args["--storage-dir"] is None else args["--storage-dir"]

        config_file = (
            Path(__file__).resolve().parent / "config" / "rag_sources.json"
            if args["--config-file"] is None
            else args["--config-file"]
        )

        download_rag_sources(storage_dir=storage_dir, config_file=config_file)
    elif args["make_chunks"]:
        from pyalbert.corpus import make_chunks

        # if --storage-dir is not provided, use default path /data/sources
        storage_dir = "/data/sources" if args["--storage-dir"] is None else args["--storage-dir"]

        make_chunks(
            storage_dir=storage_dir,
            structured=args["--structured"],
            chunk_size=int(args["--chunk-size"]),
            chunk_overlap=int(args["--chunk-overlap"]),
            sources=SHEET_SOURCES,
        )

    elif args["index"]:
        from pyalbert.index import create_index

        # if --storage-dir is not provided, use default path /data/sources
        storage_dir = "/data/sources" if args["--storage-dir"] is None else args["--storage-dir"]

        known_indexes = [
            "spp_experiences",
            "chunks",
            "sheets",
        ]
        if args["<index_name>"] not in known_indexes:
            raise ValueError("Unknown index name. Index supportere are %s" % known_indexes)

        create_index(
            args["<index_name>"],
            args["--index-type"],
            recreate=args["--recreate"],
            batch_size=int(args["--batch-size"]),
            storage_dir=storage_dir,
        )
    elif args["show_indexes"]:
        from pyalbert.index import list_indexes

        list_indexes()
    else:
        raise NotImplementedError


if __name__ == "__main__":
    main()
