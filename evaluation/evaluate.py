import json
import multiprocessing
import os
from pprint import pprint

import numpy as np
import pandas as pd
from elasticsearch import Elasticsearch
from qdrant_client import QdrantClient
from qdrant_client import models as QdrantModels

from .extract import extract
from .utils import generate, get_embedding_e5


def embed(text: str) -> list:
    return get_embedding_e5(text)


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
        institution = exp["intitule_typologie_1"]
        institution_ = institution + " " if institution else ""
        prompt = f'Question soumise au service {institution_}: {exp["description"]}\n---Réponse : '
        return prompt

    @staticmethod
    def _make_prompt_2(exp: dict, mode="simple", **kwargs) -> str:
        institution = exp["intitule_typologie_1"]
        institution_ = institution + " " if institution else ""
        text = exp["description"]

        prompt = []
        if mode == "simple":
            prompt.append("Mode simple")
            prompt.append(f"Question soumise au service {institution_}: {text}")
            prompt.append("###Réponse : \n")
            prompt = "\n\n".join(prompt)
        elif mode == "experience":
            prompt.append("Mode expérience")
            prompt.append(f"Question soumise au service {institution_}: {text}")

            # Rag
            retrieves = ["id_experience", "description"]
            _extract = lambda x: dict((r, x[r]) for r in retrieves)
            embedding = embed(text)
            client = QdrantClient(url="http://localhost:6333", grpc_port=6334, prefer_grpc=True)
            index_name = "experiences"
            # Filter on institution
            query_filter = None
            if institution:
                query_filter = QdrantModels.Filter(
                    must=[
                        QdrantModels.FieldCondition(
                            key="intitule_typologie_1",
                            match=QdrantModels.MatchValue(
                                value=institution,
                            ),
                        )
                    ]
                )
            res = client.search(
                collection_name=index_name,
                query_vector=embedding,
                query_filter=query_filter,
                limit=3,
            )
            es = Elasticsearch("http://localhost:9202", basic_auth=("elastic", "changeme"))
            # @Debug : qdrant doesnt accept the hash id as string..
            _uid = lambda x: x
            hits = [_extract(es.get(index=index_name, id=_uid(x.id))["_source"]) for x in res if x]
            chunks = [f'{x["id_experience"]} : {x["description"]}' for x in hits]
            chunks = "\n\n".join(chunks)
            prompt.append(f"Expériences :\n\n{chunks}")

            prompt.append("###Réponse : \n")
            prompt = "\n\n".join(prompt)
        elif mode == "expert":
            prompt.append("Mode expert")
            prompt.append(f"Expérience : {text}")
            # Get reponse...
            rep1 = generate(
                EVAL.SPEC["miaou"]["url"],
                {"max_tokens": 500, "temperature": 0.2},
                EVAL._make_prompt(exp),
            )
            rep1 = "".join(rep1)
            prompt.append(f"Réponse :\n\n{rep1}")

            # Rag
            retrieves = ["title", "url", "text", "context"]
            _extract = lambda x: dict((r, x[r]) for r in retrieves)
            embedding = embed(text)
            client = QdrantClient(url="http://localhost:6333", grpc_port=6334, prefer_grpc=True)
            index_name = "chunks"
            res = client.search(
                collection_name=index_name, query_vector=embedding, query_filter=None, limit=3
            )
            es = Elasticsearch("http://localhost:9202", basic_auth=("elastic", "changeme"))
            # @Debug : qdrant doesnt accept the hash id as string..
            _uid = lambda x: bytes.fromhex(x.replace("-", "")).decode("utf8")
            hits = [_extract(es.get(index=index_name, id=_uid(x.id))["_source"]) for x in res if x]
            chunks = [
                f'{x["url"]} : {x["title"] + (" > "+x["context"]) if x["context"] else ""}\n{x["text"]}'
                for x in hits
            ]
            chunks = "\n\n".join(chunks)
            prompt.append(f"Fiches :\n\n{chunks}")

            prompt.append("###Réponse : \n")
            prompt = "\n\n".join(prompt)
        else:
            raise NotImplementedError(mode)

        return prompt

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
