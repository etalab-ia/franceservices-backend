import json
import multiprocessing
import os
from pprint import pprint
from typing import List

import numpy as np
import pandas as pd

from commons import generate, get_prompter

from .extract import extract


class EVAL(object):
    SPEC = {
        "miaou": {
            "url": "http://localhost:8081",
            "prompt_maker": "_make_prompt",
            "prompt_args": {},
            "sampling_args": {"temperature": 20, "max_tokens": 500},
            "type": "fabrique",
        },
        "reference-simple": {
            "url": "http://localhost:8082",
            "prompt_maker": "_make_prompt_2",
            "prompt_args": {"mode": "simple"},
            "sampling_args": {"temperature": 20, "max_tokens": 500},
            "type": "fabrique",
        },
        "reference-experience": {
            "url": "http://localhost:8082",
            "prompt_maker": "_make_prompt_2",
            "prompt_args": {"mode": "experience"},
            "sampling_args": {"temperature": 20, "max_tokens": 4096},
            "type": "fabrique",
        },
        "reference-expert": {
            "url": "http://localhost:8082",
            "prompt_maker": "_make_prompt_2",
            "prompt_args": {"mode": "expert"},
            "sampling_args": {"temperature": 20, "max_tokens": 4096},
            "type": "fabrique",
        },
        "albert-light-rag": {
            "url": "http://localhost:8081",
            "prompt_maker": "_make_prompt_3",
            "prompt_args": {"mode": "rag"},
            "sampling_args": {"temperature": 30, "max_tokens": 1024},
            "type": "chat",
        },
        "albert-light-simple": {
            "url": "http://localhost:8081",
            "prompt_maker": "_make_prompt_3",
            "prompt_args": {"mode": "simple"},
            "sampling_args": {"temperature": 30, "max_tokens": 1024},
            "type": "chat",
        },
    }

    def __init__(self, model, version, limit=None, yes=False, n_async=70):
        if model not in self.SPEC:
            print("Model unknwon: %s" % model)
            exit()

        self.model = model
        self.version = version
        self.name = "-".join((model, version))
        self.outdir_p = f"_data/p/{self.name}/"
        self.outdir_x = f"_data/x/{self.name}/"
        self.N = limit  # number of generation
        self.n_async = n_async
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

    @staticmethod
    def _make_prompt_3(doc, **kwargs) -> str:
        return get_prompter("albert-light", mode=kwargs.get("mode")).make_prompt(
            query=doc["question"], **kwargs
        )

    def has_data(self):
        return os.path.exists(self.outdir_x)

    def run(self):
        """Generate answers in parallel (see self.n_async) for evaluation purpose."""
        do_overwrite = False

        # Input validation
        # --
        if self.has_data():
            if not self.yes:
                user_input = input(
                    f"Path {self.outdir_x} already exists. Keep going with missing entries (1) or overwrite data (2). Enter 1 or 2: "
                )
                if user_input.lower() in ["2"]:
                    do_overwrite = True
        else:
            os.makedirs(self.outdir_x)
            os.makedirs(self.outdir_p)

        # Load data
        # --
        route = EVAL.SPEC[self.model]
        if route["type"] == "fabrique":
            with open("_data/export-expa-c-riences.json") as f:
                documents = json.load(f)
            documents = dict((d["id_experience"], d) for d in documents)

            with open("_data/evaluation_experiences.json") as f:
                doc_ids = json.load(f)
        elif route["type"] == "chat":
            df = pd.read_excel("_data/gpt_corpus-20kq&A.xlsx", sheet_name="results", usecols="A:B")
            documents = dict((i, df.loc[i]) for i in df.index)
            doc_ids = df.index
            del df
        else:
            raise ValueError("Model type unknown")

        # Sampling
        # --
        size_corpus = len(doc_ids)
        if self.N:
            hazard = np.random.choice(size_corpus, size=int(self.N), replace=False)
        else:
            hazard = np.arange(size_corpus)

        # Run inference in parallel
        eval_args = [
            {
                "model": self.model,
                "settings_vllm": route["sampling_args"],
                "doc": documents[doc_ids[i]],
                "id": i,
                "outdir_p": self.outdir_p,
                "outdir_x": self.outdir_x,
            }
            for i in hazard if (not os.path.exists(f"{self.outdir_x}/{i}.txt") or do_overwrite)
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
            except Exception as e:
                print(expid, "(%s)" % e)
                continue

            rows.append({"id": expid, **data_x})

        df = pd.DataFrame(rows)
        df.to_csv(self.outdir_x + "res.csv", index=False)


# async
def eval_one(args: dict) -> None:
    # Settings
    model = args["model"]
    settings_vllm = args["settings_vllm"]
    doc = args["doc"]
    outdir_p = args["outdir_p"]
    outdir_x = args["outdir_x"]
    route = EVAL.SPEC[model]
    url = route["url"]

    # @future add an id for chat data has the hash of questions
    if "id_experience" in doc:
        id_ = doc["id_experience"]
    else:
        id_ = args["id"]

    # Add an options to only run --missing doc
    # if os.path.exists(f'{outdir_x}/{id_}.txt'):
    #    return

    # Make prompt
    make_prompt = getattr(EVAL, route["prompt_maker"])
    prompt = make_prompt(doc, **route.get("prompt_args"))

    # Save prompt
    with open(f"{outdir_p}/{id_}.txt", "w", encoding="utf-8") as f:
        f.write(prompt)

    # Generate answer
    answer = generate(url, settings_vllm, prompt)

    # Save answer
    with open(f"{outdir_x}/{id_}.txt", "w", encoding="utf-8") as f:
        f.write(answer)

    print(".", end="", flush=True)


#
# Fire
#


def evaluate(
    model: str, version: str, limit: int = None, yes: bool = False, to_: str = None
) -> None:
    """Model evaluation"""

    eva = EVAL(model, version, limit=limit, yes=yes, n_async=40)

    if not eva.has_data() or not to_:
        # Re-run if no data or if --csv is not passed (overwrite)
        np.random.seed(42)  # @warning: this does not control the LLM seed (remote API)
        eva.run()

    if to_:
        eva.to_csv()


def merge_eval(models: List[str], versions: List[str], output=str) -> None:
    names = [couple for couple in zip(models, versions)]
    result = []

    for i, (model, version) in enumerate(names):
        eva = EVAL(model, version)
        name = eva.name
        prompt_path = eva.outdir_p
        answer_path = eva.outdir_x

        prompt_files = os.listdir(prompt_path)
        # answer_files = os.listdir(answer_path)
        for j, file in enumerate(prompt_files):
            prompt_file_path = os.path.join(prompt_path, file)
            answer_file_path = os.path.join(answer_path, file)

            with open(prompt_file_path, "r") as prompt_file, open(
                answer_file_path, "r"
            ) as answer_file:
                prompt_content = prompt_file.read()
                answer_content = answer_file.read()

                if i == 0:
                    result.append(
                        {f"prompt_{name}": prompt_content, f"answer_{name}": answer_content}
                    )
                else:
                    item = result[j]
                    item.update(
                        {f"prompt_{name}": prompt_content, f"answer_{name}": answer_content}
                    )
                    result[j] = item

    output = output if output.endswith(".json") else output + ".json"
    with open(output, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
