#!/bin/python

""" Manage the legal information assistant.

Usage:
    gpt.py download_directory
    gpt.py make_chunks [--structured] [--chunk-size N] [--chunk-overlap N] DIRECTORY
    gpt.py make_questions DIRECTORY
    gpt.py make_embeddings
    gpt.py index (experiences | sheets | chunks) [--index-type=INDEX_TYPE]
    gpt.py finetune MODEL VERSION
    gpt.py evaluate MODEL VERSION [-n N] [-y] [--csv]
    gpt.py evaluate -o OUTPUT (--merge MODEL VERSION)...

Commands:
    download_directory  Download official directorier to build whitelists. Files are stored under _data/directory/.
    make_chunks     Parse les fichiers XML issue de data.gouv (fiches service publique), situé dans le repertoir DIRECTORY pour les transformer en fiches sous format Json.
                    Chaque élement Json correspond à un bout de fiche d'une longueur de 1000 caractères appelé chunk, découpé en conservant les phrases intacts.
                    Chunks are created under _data/sheets_as_chunks.json.

    make_questions  Create a corpus of questions from the XML SP sheets.

    make_embeddings Build the embeddings matrix to be used with e5 index.

    index           Create the given index to search relevant document given a query. Each index is created using a specific file as ground-truth.
                    See doc to see which files are used by which index.

    finetune        (NOT IMPLEMENTED) Fine-tune the given model. Parameters will be read from fine_tuning/x/{MODEL}-{VERSION}/.
                    Results will be saved in _data/x/{MODEL}-{VERSION}.

    evaluate        Run evaluation for the given llm model.
                    Results will be saved in _data/x/{MODEL}-{VERSION}.
                    if --merge is used, a json containing the list of prompts + generations under _data/{p,x} directory will be saved
                    using the the list of the {MODEL-VERSION} couples given.


Options:
    --chunk-size N           The maximum size of the chunks (token count...) [default: 1100]
    --chunk-overlap N        The size of the overlap between chunks [default: 200]
    --index-type INDEX_TYPE  The type of index to create (bm25, bucket, e5) [default: bm25]
    --size N, -n N           Limit the number of generations/inferences.
    --output OUTPUT, -o OUTPUT    A ouput name, to save result to.
    --yes, -y                assumes yes for every user input question.
    --csv                    Make a csv table


Examples:
    ./gpt.py download_directory
    ./gpt.py make_chunks --chunk-size 500 --chunk-overlap 20 _data/data.gouv/vos-droits-et-demarche/
    ./gpt.py make_chunks --structured _data/data.gouv/vos-droits-et-demarche/
    ./gpt.py make_questions _data/data.gouv/vos-droits-et-demarche/
    !make institutions          # Generate the french institution list
    ./gpt.py index experiences  # assumes _data/export-expa-c-riences.json exists
    ./gpt.py index sheets       # assumes _data/data.gouv/vos-droits-et-demarche/ + _data/fiches-travail.json exist
    ./gpt.py index chunks       # assumes _data/sheets_as_chunks.json + _data/fiches-travail.json exist
    ./gpt.py evaluate miaou v0  # Run the inference
    ./gpt.py evaluate miaou v0 --csv  # make an result table with inference file found in data/x/{model}-{version}
    ./gpt.py evaluate --merge albert-light-simple v0 --merge albert-light-rag v0 -o albert-light-v0
"""


from docopt import docopt

try:
    from app.config import SHEET_SOURCES
except ModuleNotFoundError as e:
    from api.app.config import SHEET_SOURCES

if __name__ == "__main__":
    # Parse CLI arguments
    args = docopt(__doc__, version="0")

    # Run command
    if args["make_chunks"]:
        from xml_parsing import make_chunks

        make_chunks(
            args["DIRECTORY"],
            structured=args["--structured"],
            chunk_size=int(args["--chunk-size"]),
            chunk_overlap=int(args["--chunk-overlap"]),
            sources=SHEET_SOURCES,
        )
    elif args["make_questions"]:
        from xml_parsing import make_questions

        make_questions(args["DIRECTORY"])
    elif args["make_embeddings"]:
        from ir import make_embeddings

        make_embeddings()

    elif args["download_directory"]:
        from evaluation.download_directory import (create_whitelist,
                                                   download_directory)

        download_directory()
        create_whitelist()

    elif args["index"]:
        from ir import create_index

        indexes = ["experiences", "chunks", "sheets"]
        for name in indexes:
            if name in args and args[name]:
                create_index(args["--index-type"], name)
    elif args["finetune"]:
        raise NotImplementedError
    elif args["evaluate"]:
        from evaluation import evaluate, merge_eval

        if args.get("--merge", 0) == 0:
            # run evaluation
            evaluate(
                args["MODEL"][0],
                args["VERSION"][0],
                limit=args["--size"],
                yes=args["--yes"],
                to_=args["--csv"],
            )
        else:
            # Merge evaluation results into a final json file
            merge_eval(args["MODEL"], args["VERSION"], args["--output"])
    else:
        raise NotImplementedError
