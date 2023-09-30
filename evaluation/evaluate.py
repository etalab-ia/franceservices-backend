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
    ROUTES = {
        "miaou": {"url": "http://localhost:8081", "prompt_maker": "_make_prompt"},
        "reference": {"url": "http://localhost:8001", "prompt_maker": "_make_prompt_2"},
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
        institution = exp["intitule_typologie_1"]
        institution = institution + " " if institution else ""
        text = exp["description"]

        prompt = []
        if mode == "simple":
            prompt.append("Mode simple")
            prompt.append(f"Question soumise au service {institution}: {text}")
            prompt.append("###Réponse : \n")
            prompt = "\n\n".join(prompt)
        elif mode == "experience":
            prompt.append("Mode expérience")
            prompt.append(f"Question soumise au service {institution} : {text}")

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
            _uid = lambda x: bytes.fromhex(x.replace("-", "")).decode("utf8")
            hits = [_extract(es.get(index=index_name, id=_uid(x.id))["_source"]) for x in res if x]
            chunks = [f'{x["id_experience"]} : {x["description"]}' for x in hits]
            chunks = "\n\n".join(chunks)
            prompt.append(f"Expériences :\n\n {chunks}")

            prompt.append("###Réponse : \n")
            prompt = "\n\n".join(prompt)
        elif mode == "expert":
            prompt.append("Mode expert")
            prompt.append(f"Expérience : {text}")
            # Get reponse...
            rep1 = generate(EVAL.ROUTES["miaou"], {"max_tokens": 500, "temperature": 0.2}, text)
            rep1 = "".join(rep1)
            prompt.append(f"Réponse :\n\n {rep1}")

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
            prompt.append(f"Fiches :\n\n {chunks}")

            prompt.append("###Réponse : \n")
            prompt = "\n\n".join(prompt)
        else:
            raise NotImplementedError(mode)

        return prompt

    def has_data(self):
        return os.path.exists(self.outdir)

    def run(self):
        # Input validation
        # --
        if self.model not in EVAL.ROUTES:
            print("Model unknwon: %s" % self.model)
            exit()

        if self.has_data():
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
                    "id": expid,
                    "words": data_x["words"],
                    "ttr": data_x["ttr"],
                    "artefacts": len(data_x["artefacts"]),
                    "emails": len(data_x["emails"]),
                    "urls": len(data_x["urls"]),
                    "phones": len(data_x["phones"]),
                }
            )

        df = pd.DataFrame(rows)
        df.to_csv(self.outdir + "res.csv", index=False)


# async
def eval_one(args: dict):
    model = args["model"]
    settings_vllm = args["settings_vllm"]
    doc = args["exp"]
    outdir = args["outdir"]
    route = EVAL.ROUTES[model]
    url = route["url"]

    # Make prompt
    make_prompt = getattr(EVAL, route["prompt_maker"])
    prompt = make_prompt(doc)

    # Generate answer
    answer = generate(url, settings_vllm, prompt)

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

    if not eva.has_data() or not to_:
        # Re-run if no data or if --csv is not passed (overwrite)
        np.random.seed(2) # @warning: this does not control the LLM seed (remote API)
        eva.run()

    if to_:
        eva.to_csv()
