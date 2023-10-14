import json
import multiprocessing
import os
import sys

import pandas as pd

sys.path.append(".")

from commons import get_prompter


def run_one(args):
    doc = args["doc"]
    print(".", end="", flush=True)
    prompter = get_prompter("albert-light")
    prompt = prompter.make_prompt(question=doc["question"], limit=3)
    item = {
        "query": doc["question"],
        "prompt": prompt,
        "answer": doc["answer"],  # /!\ it has been regenrated separetely
        "sources": prompter.sources,
    }

    with open(f'{args["tempdir"]}/{args["id"]}.json', "w") as f:
        json.dump(item, f)


def run_parallel(n_async=25):
    # Load the data (LLM generated Q/A)
    fn = "_data/gpt_corpus-20kq&A.xlsx"
    df = pd.read_excel(fn, sheet_name="results", usecols="A:B")

    # Run inference in parallel
    tempdir = "temp_prompt"
    os.makedirs(tempdir)
    eval_args = [{"doc": doc, "tempdir": "temp_prompt", "id": i} for i, doc in df.iterrows()]
    pool = multiprocessing.Pool(n_async)
    _ = pool.map(run_one, eval_args)

    # Merge results

    # Get a list of all json files in the directory
    json_files = [file for file in os.listdir(tempdir) if file.endswith(".json")]

    # Load, merge, and save json temporary results.
    final = []
    for file in json_files:
        with open(file) as f:
            final.apend(json.load(f))

    # pd.DataFrame(data).to_csv("_data/training_miaou-qa_20k.csv", index=False)
    pd.DataFrame(final).to_json(
        "_data/training_albert-light.json", orient="records", indent=2, force_ascii=False
    )


if __name__ == "__main__":
    run_parallel(25)
