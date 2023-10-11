from elasticsearch import Elasticsearch
from qdrant_client import QdrantClient
from qdrant_client import models as QdrantModels

from commons import get_embedding_e5


def embed(text: str) -> list:
    return get_embedding_e5(text)


# @obsolete
def make_prompt_miaou(exp):
    institution = exp["intitule_typologie_1"]
    institution_ = institution + " " if institution else ""
    text = exp["description"]

    prompt = f'Question soumise au service {institution_}: {text}\n---Réponse : '
    return prompt


def make_prompt_simple(exp):
    institution = exp["intitule_typologie_1"]
    institution_ = institution + " " if institution else ""
    text = exp["description"]

    prompt = []
    prompt.append("Mode simple")
    prompt.append(f"Question soumise au service {institution_}: {text}")
    if exp.get["context"] or exp.get["links"]:  # Context
        prompt.append(f'{exp["context"]} exp["links"]')

    prompt.append("###Réponse : \n")
    prompt = "\n\n".join(prompt)
    return prompt


def make_prompt_experience(exp):
    institution = exp["intitule_typologie_1"]
    institution_ = institution + " " if institution else ""
    text = exp["description"]

    prompt = []
    prompt.append("Mode expérience")
    prompt.append(f"Question soumise au service {institution_} : {text}")

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
        collection_name=index_name, query_vector=embedding, query_filter=query_filter, limit=3
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
    return prompt


def make_prompt_expert(user):
    prompt = []
    prompt.append("Mode expert")
    prompt.append(f"Expérience : {user.user_text}")
    # Get reponse...
    rep1 = vllm_generate(prompt, max_tokens=500, temp=float(user.temperature), streaming=False)
    rep1 = "".join(rep1)
    prompt.append(f"Réponse :\n\n {rep1}")

    # Rag
    retrieves = ["title", "url", "text", "context"]
    _extract = lambda x: dict((r, x[r]) for r in retrieves)
    embedding = embed(user.user_text)
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
    return prompt
