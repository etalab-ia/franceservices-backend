import json
import multiprocessing
import os
import shutil
import sys

import numpy as np
import pandas as pd

sys.path.append(".")

from commons import get_prompter


def run_one(args):
    doc = args["doc"]
    print(".", end="", flush=True)

    prompter = get_prompter("albert-light")
    prompt = prompter.make_prompt(question=doc["question"], limit=4)
    item = {
        "query": doc["question"],
        "prompt": prompt,
        "answer": None,  # /!\ answer are regenrated separetely (see update-albert-light.py)
        "old_answer": doc["answer"],
        "sources": prompter.sources,
    }

    with open(f'{args["tempdir"]}/{args["id"]}.json', "w") as f:
        json.dump(item, f)


def run_parallel(n_async=25, N=None):
    # Load the data (LLM generated Q/A)
    df = pd.read_excel("_data/gpt_corpus-20kq&A.xlsx", sheet_name="results", usecols="A:B")

    # Sampling
    size_corpus = len(df)
    if N:
        hazard = np.random.choice(size_corpus, size=int(N), replace=False)
    else:
        hazard = np.arange(size_corpus)

    # Run inference in parallel
    tempdir = "_data/temp_prompt"
    os.mkdir(tempdir)
    eval_args = [{"doc": df.loc[i], "tempdir": tempdir, "id": i} for i in hazard]
    pool = multiprocessing.Pool(n_async)
    _ = pool.map(run_one, eval_args)

    # Merge results
    # --
    # Get a list of all json files in the directory
    json_files = [file for file in os.listdir(tempdir) if file.endswith(".json")]
    # Load, merge, and save json temporary results.
    final, order = [], []
    for file in json_files:
        order.append(int(file.split(".")[0]))
        with open(os.path.join(tempdir, file)) as f:
            final.append(json.load(f))

    # Order the same as the orginal data...
    final = [final[i] for i in np.argsort(order)]

    # Save/replace the frame
    # --
    # pd.DataFrame(data).to_csv("_data/training_miaou-qa_20k.csv", index=False)
    pd.DataFrame(final).to_json(
        "_data/training_albert-light.json", orient="records", indent=2, force_ascii=False
    )

    # Remove temporary folder
    shutil.rmtree(tempdir)


if __name__ == "__main__":
    np.random.seed(42)
    run_parallel(25, 1000)
