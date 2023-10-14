import json
import multiprocessing
import os
import shutil
import sys

import numpy as np
import pandas as pd

sys.path.append(".")

from commons import get_prompter
from commons.openai_api import chat_completion

# Task: Add the answer field
# --
# Add an answer field to the dataset generated from openai
# chat completion calls.


def run_one(args):
    doc = args["doc"]

    # Format the prompt,in openai format.
    dialog = [{"role": "user", "content": doc["prompt"]}]
    # generate the answer
    answer = chat_completion(dialog, temperature=0.5)
    # save the answer
    item = {"answer": answer}

    with open(f'{args["tempdir"]}/{args["id"]}.json', "w") as f:
        json.dump(item, f)

    print(".", end="", flush=True)


def run_parallel(n_async=25, N=None, overwrite=False):
    # Load the data (LLM generated Q/A)
    df = pd.read_json("_data/training_albert-light.json")
    if not overwrite:
        # Only take nan values...
        indexes = df[(df["answer"] == "nan") | df["answer"].isna()].index
    else:
        indexes = df.index

    # Sampling
    size_corpus = len(indexes)
    if size_corpus == 0:
        print("Nothing to compute."); exit()
    if N:
        N = N if size_corpus >= N else size_corpus
        hazard = np.random.choice(indexes, size=int(N), replace=False)
    else:
        hazard = indexes

    # Run inference in parallel
    tempdir = "_data/temp_prompt"
    os.makedirs(tempdir, exist_ok=True)
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
            final.append(json.load(f)["answer"])

    # Update the frame
    # --
    df["answer"] = df["answer"].astype(str)
    for i, index in enumerate(order):
        df.loc[index, "answer"] = final[i]

    df.to_json("_data/training_albert-light.json", orient="records", indent=2, force_ascii=False)

    # Remove temporary folder
    shutil.rmtree(tempdir)


if __name__ == "__main__":
    np.random.seed(42)
    run_parallel(10, 1000)
