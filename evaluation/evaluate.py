import json
import multiprocessing
import os
from pprint import pprint

import numpy as np
import pandas as pd

from commons import generate, get_prompter

from .extract import extract


class EVAL(object):
    SPEC = {
        "miaou": {
            "url": "http://localhost:8081",
            "prompt_maker": "_make_prompt",
            "temperature": 0.2,
            "max_tokens": 500,
        },
        "reference-simple": {
            "url": "http://localhost:8001",
            "prompt_maker": "_make_prompt_2",
            "mode": "simple",
            "temperature": 0.2,
            "max_tokens": 500,
        },
        "reference-experience": {
            "url": "http://localhost:8001",
            "prompt_maker": "_make_prompt_2",
            "mode": "experience",
            "temperature": 0.2,
            "max_tokens": 4096,
        },
        "reference-expert": {
            "url": "http://localhost:8001",
            "prompt_maker": "_make_prompt_2",
            "mode": "expert",
            "temperature": 0.2,
            "max_tokens": 4096,
        },
    }

    def __init__(self, model, version, limit=None, yes=False, n_async=70):
        if model not in self.SPEC:
            print("Model unknwon: %s" % model)
            exit()

        self.model = model
        self.version = version
        self.outdir_p = f"_data/p/{model}-{version}/"
        self.outdir_x = f"_data/x/{model}-{version}/"
        self.N = limit  # number of generation
        self.n_async = n_async
        self.settings_vllm = {
            "max_tokens": self.SPEC[model]["max_tokens"],
            "temperature": self.SPEC[model]["temperature"],
        }
        self.yes = yes

    @staticmethod
    def _make_prompt(exp: dict, **kwargs) -> str:
        return get_prompter("fabrique-miaou").make_prompt(
            experience=exp["description"], institution=exp["intitule_typologie_1"]
        )

    @staticmethod
    def _make_prompt_2(exp: dict, mode="simple", **kwargs) -> str:
        return get_prompter("fabrique-reference", mode=mode).make_prompt(
            experience=exp["description"], institution=exp["intitule_typologie_1"], skip_first=True
        )

    def has_data(self):
        return os.path.exists(self.outdir_x)

    def run(self):
        """Generate answers in parallel (see self.n_async) for evaluation purpose."""
        # Input validation
        # --
        if self.has_data():
            if not self.yes:
                user_input = input(
                    f"Path {self.outdir_x} already exists. Evaluation data will be overwritten.\nDo you want to continue? (Y/n): "
                )
                if user_input.lower() in ["n", "q", "c", "x", "no"]:
                    exit()
        else:
            os.makedirs(self.outdir_x)
            os.makedirs(self.outdir_p)

        # Inference
        # --
        with open("_data/export-expa-c-riences.json") as f:
            documents = json.load(f)
        documents = dict((d["id_experience"], d) for d in documents)

        with open("_data/evaluation_experiences.json") as f:
            experience_ids = json.load(f)

        size_corpus = len(experience_ids)
        if self.N:
            hazard = np.random.choice(size_corpus, size=int(self.N), replace=False)
        else:
            hazard = np.arange(size_corpus)

        # Run inference in parallel
        eval_args = [
            {
                "model": self.model,
                "settings_vllm": self.settings_vllm,
                "exp": documents[experience_ids[i]],
                "outdir_p": self.outdir_p,
                "outdir_x": self.outdir_x,
            }
            for i in hazard
        ]
        pool = multiprocessing.Pool(self.n_async)
        _ = pool.map(eval_one, eval_args)

    def to_csv(self):
        """Save evaluation result to a csv file"""
        rows = []
        for filename in os.listdir(self.outdir_x):
            if not filename.endswith(".txt"):
                continue

            expid = filename.split(".")[0]
            with open(self.outdir_x + f"{filename}", "r") as f:
                answer = f.read()

            try:
                data_x = extract(answer)
            except:
                print(expid)
                continue

            rows.append(
                {
                    "id": expid,
                    "words": data_x["words"],
                    "ttr": data_x["ttr"],
                    "emails": len(data_x["emails"]),
                    "urls": len(data_x["urls"]),
                    "phones": len(data_x["phones"]),
                    "dates": len(data_x["dates"]),
                    "hours": len(data_x["hours"]),
                    "prices_": len(data_x["prices_"]),
                    "number_artefacts": len(data_x["numbers_"]),
                    "prompt_artefacts": len(data_x["artefacts"]),
                }
            )

        df = pd.DataFrame(rows)
        df.to_csv(self.outdir_x + "res.csv", index=False)


# async
def eval_one(args: dict):
    # Settings
    model = args["model"]
    settings_vllm = args["settings_vllm"]
    doc = args["exp"]
    outdir_p = args["outdir_p"]
    outdir_x = args["outdir_x"]
    route = EVAL.SPEC[model]
    url = route["url"]

    # Add an options to only run --missing exp
    # if os.path.exists(f'{outdir_x}/{doc["id_experience"]}.txt'):
    #    return

    # Make prompt
    make_prompt = getattr(EVAL, route["prompt_maker"])
    prompt = make_prompt(doc, mode=route.get("mode"))

    # Save prompt
    with open(f'{outdir_p}/{doc["id_experience"]}.txt', "w", encoding="utf-8") as f:
        f.write(prompt)

    # Generate answer
    answer = generate(url, settings_vllm, prompt)

    # Save answer
    with open(f'{outdir_x}/{doc["id_experience"]}.txt', "w", encoding="utf-8") as f:
        f.write(answer)


def evaluate(
    model: str, version: str, limit: int = None, yes: bool = False, to_: str = None
) -> None:
    """Model evaluation"""

    eva = EVAL(model, version, limit, yes)

    if not eva.has_data() or not to_:
        # Re-run if no data or if --csv is not passed (overwrite)
        np.random.seed(2)  # @warning: this does not control the LLM seed (remote API)
        eva.run()

    if to_:
        eva.to_csv()
