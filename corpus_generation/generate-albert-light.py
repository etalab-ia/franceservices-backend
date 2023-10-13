import json
import multiprocessing
import os
import sys

import pandas as pd

sys.path.append(".")

from commons import get_prompter


def run():
    # Load the data (LLM generated Q/A)
    fn = "_data/gpt_corpus-20kq&A.xlsx"
    df = pd.read_excel(fn, sheet_name="results", usecols="A:B")

    data = []
    for i, doc in df.iterrows():
        d = {"description": doc["question"]}
        print(".", end="", flush=True)
        prompt = get_prompter("albert-light").make_prompt(question=doc["question"], limit=3)
        data.append(
            {
                "prompt": prompt,
                "answer": doc["answer"],
            }
        )

        if i > 10:
            break

    # df = pd.DataFrame(data).to_csv("_data/training_miaou-qa_20k.csv", index=False)
    df = pd.DataFrame(data).to_json(
        "_data/training_albert-light.json", orient="records", indent=2, force_ascii=False
    )


def run_async(n_async=50):
    # Load the data (LLM generated Q/A)
    fn = "_data/gpt_corpus-20kq&A.xlsx"
    df = pd.read_excel(fn, sheet_name="results", usecols="A:B")

    def eval_one(args):
        doc = args["doc"]
        print(".", end="", flush=True)
        prompt = get_prompter("albert-light").make_prompt(question=doc["question"], limit=3)
        item = {
            "prompt": prompt,
            "answer": doc["answer"],
        }

        with open(f'{args["outdir"]}/{args["id"]}.json', "w") as f:
            json.dump(item, f)

    # Run inference in parallel
    os.makedirs("temp_prompt")
    eval_args = [{"doc": doc, "outdir": "temp_prompt", "id": i} for i, doc in df.iterrows()]
    pool = multiprocessing.Pool(n_async)
    _ = pool.map(eval_one, eval_args)


if __name__ == "__main__":
    # run_async()
    run()
