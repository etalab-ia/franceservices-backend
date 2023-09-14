import os
import random
import string
from datetime import timedelta

import meilisearch
from elasticsearch import Elasticsearch
from flask import (Flask, Response, jsonify, redirect, render_template,
                   request, session, stream_with_context, url_for)
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from gpt4all import GPT4All
from qdrant_client import QdrantClient
from sqlalchemy import Boolean, Column, Integer, String, Text

app = Flask(__name__)
CORS(app, supports_credentials=True)
# CORS(app, origins=['https://127.0.0.1:5173, https://localhost:5173'])
app.secret_key = "secret4all"
app.permanent_session_lifetime = timedelta(hours=24)
cache_db_name = "gptcache.db"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(os.getcwd(), cache_db_name)


# Default model
N_THREADS = 4
model = GPT4All("ggml-model-fabrique-q4_K.bin", model_path="model", n_threads=N_THREADS)


#
# Database
#

db = SQLAlchemy(app)


class User(db.Model):
    # uniquely identify a user/client.
    username = Column(String(80), primary_key=True)
    # Use by the llm generator callback to stop the stream.
    is_streaming = Column(Boolean, default=False)
    # Limit the max number of allowed stream.
    concurent_stream = Column(Integer, default=0)

    # Fabrique parameters
    # --
    user_text = Column(
        Text,
        default="Le service chat a été très facile à utiliser et la policière était très gentille, elle a répondu à toutes mes questions et es très patiente merci de son aide et de l'aide du système.  ri le 02/07/2023 à 59130 Lambersart  Posté par La personne concernée",
    )
    context = Column(
        Text,
        default="La plateforme ma Sécurité permet de mettre en relation les citoyens avec des policières et ds policiers 24h sur 24",
    )
    institution = Column(Text, default="moncommissariat.fr")
    links = Column(Text, default="https://www.masecurite.interieur.gouv.fr/fr")
    temperature = Column(String(5), default="0.5")

    def __init__(self, username):
        self.username = username

    def __repr__(self):
        return "<User %r : is_streaming=%s>" % (self.username, self.is_streaming)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        db.session.commit()

    @staticmethod
    def addUser(username):
        user = User(username)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def getUser(username):
        return db.session.get(User, username)

    @staticmethod
    def getIsStreaming(username):
        user = db.session.get(User, username)
        if user:
            return user.is_streaming
        else:
            return False

    def setIsStreaming(self, is_streaming):
        self.is_streaming = bool(is_streaming)

        if is_streaming:
            self.concurent_stream += 1
        elif self.concurent_stream > 0:
            self.concurent_stream -= 1

        db.session.commit()


with app.app_context():
    db.create_all()


#
# Utils
#


def random_username(length=8):
    """Help uniquely identify client"""
    characters = string.ascii_letters + "_-" + string.digits
    return "".join(random.choice(characters) for _ in range(length))


class StopGen:
    """Callback to pass to the generator"""

    def __init__(self, username):
        self.username = username

    def callback(self, token_id, token_string):
        with app.app_context():
            is_streaming = User.getIsStreaming(self.username)
            return is_streaming


#
# @TODO: Move this to the GPU API
#

import numpy as np
import torch
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer
from torch import Tensor
from transformers import AutoModel, AutoTokenizer

with_gpu = False
device_map = None
if torch.cuda.is_available():
    with_gpu = True
    device_map = "cuda:0"


# @PERF: The following embedding/encoding function seems to give slighly different results than SentenceTransformer.embed()
# (probably negligible) AND then batching of sentenceTransformer seems i) fastrer and ii) consume way less memory.
# see SentenceTransformer code:
# - https://www.sbert.net/docs/package_reference/SentenceTransformer.html
# - https://github.com/UKPLab/sentence-transformers/blob/master/sentence_transformers/SentenceTransformer.py


def average_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]


def _embed(tokenizer, model, texts, batch_size=1):
    # Sentence transformers for E5 like model
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch_dict = tokenizer(
            texts[i : i + batch_size],
            max_length=512,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        if with_gpu:
            batch_dict.to("cuda")

        outputs = model(**batch_dict)

        vectors = average_pool(outputs.last_hidden_state, batch_dict["attention_mask"])
        vectors = F.normalize(vectors, p=2, dim=1)
        # print(type(vectors)) -> Tensor
        # print(vectors.shape) -> (n_doc X size_embedding)
        if with_gpu:
            embeddings.append(vectors.detach().cpu().numpy())
        else:
            embeddings.append(vectors.detach().numpy())
        # torch.cuda.empty_cache()

    # return torch.cat(embeddings) # burn memory
    return np.vstack(embeddings)


# Load E5 Model
model_name_ebd = "intfloat/multilingual-e5-base"

# Model with SentenceTransformer approach
# model = SentenceTransformer(model_name_ebd, device="cuda" if with_gpu else "cpu")
# --
# Model with manual encoding approch
tokenizer_ebd = AutoTokenizer.from_pretrained(model_name_ebd)
model_ebd = AutoModel.from_pretrained(model_name_ebd, device_map=device_map)


def embed(query):
    # SentenceTransformer
    # return model.encode([query], normalize_embeddings=True, batch_size=32)[0]
    # --
    # Manual encoding
    return _embed(tokenizer_ebd, model_ebd, [query])[0]


#
# App
#


@app.route("/api/fabrique_stream")
def fabrique_stream():
    if "username" in session:
        username = session["username"]
        user = User.getUser(username)
        user.setIsStreaming(session["is_streaming"])
    else:
        return "user need to POST on / before streaming", 400

    # Route that stream the generation results
    def generate():
        try:
            prompt = f"""Question soumise au service {user.institution} : {user.user_text}
                \rPrompt : {user.context} {user.links}
                \r---Réponse : """

            acc = []
            for t in model.generate(
                prompt, max_tokens=500, temp=float(user.temperature), streaming=True, callback=StopGen(username).callback
            ):
                # t = t.replace("\n", "<br>") # Better to  use <pre> to format generated text
                acc.append(t)
                if t.endswith((" ", "\n")) or t.startswith((" ", "\n")):
                    yield "data: " + "".join(acc) + "\n\n"
                    acc = []

            if len(acc) > 0:
                yield "data: " + "".join(acc) + "\n\n"

            yield "data: [DONE]\n\n"
        finally:
            session["is_streaming"] = False
            user.setIsStreaming(False)

    # return Response(generate(), mimetype="text/event-stream")
    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@app.route("/api/fabrique_stop")
def fabrique_stop():
    if "username" in session:
        session["is_streaming"] = False
        User.getUser(session["username"]).setIsStreaming(False)

    return "ok", 200


@app.route("/api/fabrique", methods=["GET", "POST"])
def fabrique():
    # @TODO: rolling database / forget user after a certain amount of times...
    # if len(db) > 20000:
    #    db.clear()

    if "username" not in session:
        username = random_username()
        session["username"] = username
        user = User.addUser(username)
    elif not User.getUser(session["username"]):
        username = session["username"]
        user = User.addUser(username)
    else:
        username = session["username"]
        user = User.getUser(session["username"])

    if request.method == "POST":
        user.update(**request.form)
        session["is_streaming"] = True
    else:
        session["is_streaming"] = False

    return render_template(
        "index.html",
        user_text=user.user_text,
        institution=user.institution,
        context=user.context,
        links=user.links,
        temperature=user.temperature,
        is_streaming=session["is_streaming"],
    )


@app.route("/api/search/<string:index_name>", methods=["POST"])
def search(index_name):
    if index_name not in ["experiences", "sheets", "chunks"]:
        error = {"message": "Invalid route: index unknwown."}
        return jsonify(error), 400

    # Params
    data = request.get_json()
    if "q" not in data:
        error = {"message": 'Attribute "q" is missing'}
        return jsonify(error), 400

    q = data["q"]
    limit = int(data.get("n", 3))
    sim = data.get("similarity", "bm25")

    # What to retrieves
    if index_name == "experiences":
        retrieves = ["id_experience", "titre", "description", "intitule_typologie_1", "reponse_structure_1"]
    elif index_name == "sheets" and sim not in ["e5"]:
        retrieves = ["sid", "title", "url", "introduction"]
    elif index_name == "chunks" or (sim in ["e5"] and index_name == "sheets"):
        retrieves = ["hash", "title", "url", "introduction", "text", "context"]
    else:
        raise NotImplementedError

    _extract = lambda x: dict((r, x[r]) for r in retrieves)

    # Search
    if sim == "bucket":
        client = meilisearch.Client("http://localhost:7700", "masterKey")
        res = client.index(index_name).search(q, {"limit": limit, "attributesToRetrieve": retrieves})
    elif sim == "bm25":
        client = Elasticsearch("http://localhost:9202", basic_auth=("elastic", "changeme"))
        query = {"query": {"multi_match": {"query": q, "fuzziness": "AUTO"}}, "size": limit}
        res = client.search(index=index_name, body=query)
        hits = [_extract(x.get("_source")) for x in res["hits"]["hits"] if x]
        res = {"hits": hits}
    elif sim == "e5":
        do_unique_sheets = False
        if index_name == "sheets":
            index_name = "chunks"
            limit = limit * 5
            do_unique_sheets = True

        embedding = embed(q)
        client = QdrantClient(url="http://localhost:6333", grpc_port=6334, prefer_grpc=True)
        res = client.search(collection_name=index_name, query_vector=embedding, limit=limit)

        es = Elasticsearch("http://localhost:9202", basic_auth=("elastic", "changeme"))
        # @Debug : qdrant doesnt accept the hash id as string..
        if index_name == "chunks":
            _uid = lambda x: bytes.fromhex(x.replace("-", "")).decode("utf8")
        else:
            _uid = lambda x: x
        hits = [_extract(es.get(index=index_name, id=_uid(x.id))["_source"]) for x in res if x]
        if do_unique_sheets:
            keep_idx = []
            seen_sheets = []
            for i, d in enumerate(hits):
                if d["url"] in seen_sheets:
                    continue
                keep_idx.append(i)
                seen_sheets.append(d["url"])

            hits = [hits[i] for i in keep_idx][: limit // 5]

        res = {"hits": hits}
    else:
        error = {"message": 'Attribute "similarity" unknown'}
        return jsonify(error), 400

    # print("total hit ~ %s" % res["estimatedTotalHits"])
    response = jsonify(res["hits"])
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response


@app.route("/api/embedding", methods=["POST"])
def embedding():
    data = request.get_json()
    if "text" not in data:
        error = {"message": 'Attribute "q" is missing'}
        return jsonify(error), 400

    text = data["text"]
    embedding = embed(text)
    return jsonify(embedding.tolist())


@app.route("/", methods=["GET", "POST"])
def index():
    return redirect(url_for("fabrique"))


# @app.teardown_appcontext
# def teardown_db(exception=None):
#    db.terminate()


if __name__ == "__main__":
    app.run(threaded=True, debug=True)
