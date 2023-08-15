#!/bin/python

""" Manage the legal information assistant.

Usage:
    gpt.py chunks [--chunk-size INT] [--chunk-overlap INT] DIRECTORY

Commands:
    chunks DIRECTORY    Parse les fichiers Xml issue de data.gouv, situé dans le repertoir DIRECTORY pour les transformer en fiches sous format Json.
                        Chaque élement Json correspond à un bout de fiche d'une longueur de 1000 caractères appelé chunk, découpé en conservant les phrases intacts.

Options:
    --chunk-size INT      The maximum size of the chunks (token count...) [default: 1100]
    --chunk-overlap INT   The size of the overlap between chunk [default: 200]


Examples:
    ./gpt.py chunks --chunk-size 500 --chunk-overlap 20 ../../data.gouv/vos-droits-et-demarche/
"""


from docopt import docopt

from xml_parsing import make_chunks

if __name__ == "__main__":
    # Parse CLI arguments
    args = docopt(__doc__, version="0")

    # Run command
    if args["chunks"]:
        make_chunks(args["DIRECTORY"], chunk_size=int(args["--chunk-size"]), chunk_overlap=int(args["--chunk-overlap"]))
    else:
        raise NotImplementedError
