#!/bin/python

""" Manage the legal information assistant.

Usage:
    gpt.py chunks [--structured] [--chunk-size N] [--chunk-overlap N] DIRECTORY
    gpt.py questions DIRECTORY
    gpt.py index (experiences | sheets | chunks)
    gpt.py finetune (xgen | llama) VERSION

Commands:
    chunks      Parse les fichiers Xml issue de data.gouv, situé dans le repertoir DIRECTORY pour les transformer en fiches sous format Json.
                Chaque élement Json correspond à un bout de fiche d'une longueur de 1000 caractères appelé chunk, découpé en conservant les phrases intacts.
                Chunks are created under _data/xmlfiles_as_chunks.json.

    questions   Generate a corpus of questions from the XML files.

    index       Create the given index to search relevant document given a query. Each index is created using a specific file as ground-truth.
                See doc to see which files are used by which index.

    finetune    Fine-tune the given model. Parameters will be read from fine_tuning/x/{MODEL}-{VERSION}/.
                Results will be saved in _data/x/{MODEL}-{VERSION}.


Options:
    --chunk-size N      The maximum size of the chunks (token count...) [default: 1100]
    --chunk-overlap N   The size of the overlap between chunks [default: 200]


Examples:
    ./gpt.py chunks --chunk-size 500 --chunk-overlap 20 ../../data.gouv/vos-droits-et-demarche/
    ./gpt.py questions ../../data.gouv/vos-droits-et-demarche/
"""


from docopt import docopt

if __name__ == "__main__":
    # Parse CLI arguments
    args = docopt(__doc__, version="0")

    # Run command
    if args["chunks"]:
        from xml_parsing import make_chunks

        make_chunks(
            args["DIRECTORY"],
            structured=args["--structured"],
            chunk_size=int(args["--chunk-size"]),
            chunk_overlap=int(args["--chunk-overlap"]),
        )
    elif args["questions"]:
        from xml_parsing import make_questions

        make_questions(args["DIRECTORY"])
    elif args["index"]:
        from ir import create_index

        indexes = ["experiences", "chunks", "sheets"]
        for name in indexes:
            if name in args and args[name]:
                create_index(name)
    elif args["finetune"]:
        raise NotImplementedError
    else:
        raise NotImplementedError
