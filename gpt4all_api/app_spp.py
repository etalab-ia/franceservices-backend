import os
import random
import string
from datetime import timedelta

import meilisearch
from flask import (Flask, Response, jsonify, redirect, render_template,
                   request, session, stream_with_context, url_for)
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from gpt4all import GPT4All
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
                prompt, max_tokens=700, temp=float(user.temperature), streaming=True, callback=StopGen(username).callback
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

    # Text search index
    client = meilisearch.Client("http://localhost:7700", "masterKey")
    text_index = client.index(index_name)

    data = request.get_json()
    if "q" not in data:
        error = {"message": 'Attribute "q" is missing'}
        return jsonify(error), 400

    if index_name == "experiences":
        retrieves = ["title", "description", "intitule_typologie_1", "reponse_structure_1"]
    elif index_name == "sheets":
        retrieves = ["title", "url", "introduction"]
    elif index_name == "chunks":
        retrieves = ["title", "url", "introduction", "text", "context"]
    else:
        raise NotImplementedError

    res = text_index.search(data["q"], {"limit": data.get("n", 3), "attributesToRetrieve": retrieves})

    # print("total hit ~ %s" % res["estimatedTotalHits"])
    response = jsonify(res["hits"])
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    return redirect(url_for("fabrique"))


# @app.teardown_appcontext
# def teardown_db(exception=None):
#    db.terminate()


if __name__ == "__main__":
    app.run(threaded=True, debug=True)
