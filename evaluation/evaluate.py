import json
import multiprocessing
import os
from pprint import pprint

import numpy as np
import pandas as pd
import requests

from .extract import extract


class EVAL(object):
    ROUTES = {
        "miaou": {"url": "http://localhost:8081", "prompt_maker": "_make_prompt"},
        "reference": {"url": "http://localhost:8081", "prompt_maker": "_make_prompt_2"},
    }

    def __init__(self, model, version, limit=None, yes=False, n_async=70):
        self.model = model
        self.version = version
        self.outdir = f"_data/x/{model}-{version}/"
        self.N = limit  # number of generation
        self.n_async = n_async
        self.settings_vllm = {
            "max_tokens": 500,
            "temperature": 0.2,
            "stream": False,
        }
        self.yes = yes

    @staticmethod
    def _make_prompt(exp: dict, **kwargs) -> str:
        prompt = f"""Question soumise au service {exp["intitule_typologie_1"]}: {exp["description"]}
    ---Réponse : """
        return prompt

    @staticmethod
    def _make_prompt_2(exp: dict, mode="simple", **kwargs) -> str:
        # TO COMPLETE
        if mode == "simmle":
            prompt = f"""Question soumise au service {exp["intitule_typologie_1"]}: {exp["description"]}
        ---Réponse : """
        else:
            raise NotImplementedError(mode)
        return prompt

    def generate(url, conf, text):
        headers = {"Content-Type": "application/json"}
        c = conf.copy()
        c["prompt"] = text
        response = requests.post(url + "/generate", json=c, stream=True, verify=False)
        res = b""
        for r in response:
            res += r
        ans = json.loads(res.decode("utf-8"))
        ans = ans["text"][0]
        return ans

    def run(self):
        # Input validation
        # --
        if self.model not in EVAL.ROUTES:
            print("Model unknwon: %s" % self.model)
            exit()

        if os.path.exists(self.outdir):
            if not self.yes:
                user_input = input(
                    f"Path {self.outdir} already exists. Evaluation data will be overwritten.\nDo you want to continue? (Y/n): "
                )
                if user_input.lower() in ["n", "q", "c", "x", "no"]:
                    exit()
        else:
            os.makedirs(self.outdir)

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
                "outdir": self.outdir,
            }
            for i in hazard
        ]
        pool = multiprocessing.Pool(self.n_async)
        _ = pool.map(eval_one, eval_args)

    def to_csv(self):
        rows = []
        for filename in os.listdir(self.outdir):
            if not filename.endswith(".txt"):
                continue

            expid = filename.split(".")[0]
            with open(self.outdir + f"{filename}", "r") as f:
                answer = f.read()

            try:
                data_x = extract(answer)
            except:
                print(expid)
                continue

            rows.append(
                {
                    "id":expid,
                    "words": data_x["words"],
                    "ttr": data_x["ttr"],
                    "artefacts": len(data_x["artefacts"]),
                    "emails": len(data_x["emails"]),
                    "urls": len(data_x["urls"]),
                    "phones": len(data_x["phones"]),
                }
            )

        df = pd.DataFrame(rows)
        df.to_csv(self.outdir + 'res.csv', index=False)


# async
def eval_one(args: dict):
    model = args["model"]
    settings_vllm = args["settings_vllm"]
    route = EVAL.ROUTES[model]
    url = route["url"]
    doc = args["exp"]
    outdir = args["outdir"]

    # Make prompt
    make_prompt = getattr(EVAL, route["prompt_maker"])
    prompt = make_prompt(doc)

    # Generate answer
    answer = EVAL.generate(url, settings_vllm, prompt)

    # Save answer
    with open(f'{outdir}/{doc["id_experience"]}.txt', "w", encoding="utf-8") as f:
        f.write(answer)


def evaluate(
    model: str, version: str, limit: int = None, yes: bool = False, to_: str = None
) -> None:
    """Model evaluation"""

    # Settings
    # --

    eva = EVAL(model, version, limit, yes)

    if to_:
        eva.to_csv()
    else:
        np.random.seed(2)
        eva.run()
