import os
import random
import string
from datetime import timedelta

from flask import (Flask, Response, g, jsonify, render_template, request,
                   session, stream_with_context)
from flask_sqlalchemy import SQLAlchemy
from gpt4all import GPT4All
from sqlalchemy import Boolean, Column, Integer, String

app = Flask(__name__)
app.secret_key = "secret4all"
app.permanent_session_lifetime = timedelta(hours=24)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(os.getcwd(), "gptcache.db")


# Default model
N_THREADS = 4
model = GPT4All("ggml-model-fabrique-q4_K.bin", model_path="model", n_threads=N_THREADS)

# Default value for the form.
user_text = "Le service chat a été très facile à utiliser et la policière était très gentille, elle a répondu à toutes mes questions et es très patiente merci de son aide et de l'aide du système.  ri le 02/07/2023 à 59130 Lambersart  Posté par La personne concernée"
context = (
    "La plateforme ma Sécurité permet de mettre en relation les citoyens avec des policières et ds policiers 24h sur 24"
)
institution = "moncommissariat.fr"
links = "https://www.masecurite.interieur.gouv.fr/fr"
temperature = "0.5"

#
# Utils
#


def random_username(length=8):
    """Help uniquely identify client"""
    characters = string.ascii_letters + "_-" + string.digits
    return "".join(random.choice(characters) for _ in range(length))


class StopGen:
    """Callback to pass to the generator"""

    def __init__(self, db, username):
        self.db = db
        self.username = username

    def callback(self, token_id, token_string):
        is_streaming = getIsStreaming(self.db, self.username)
        return is_streaming


#
# Database
#

db = SQLAlchemy(app)

with app.app_context():
    db.create_all()


class User(db.Model):
    # uniquely identify a user/client.
    username = Column(String(80), primary_key=True)
    # Use by the llm generator callback to stop the stream.
    is_streaming = Column(Boolean, default=False)
    # Limit the max number of allowed stream.
    concurent_stream = Column(Integer, default=0)

    def __init__(self, username):
        self.username = username

    def __repr__(self):
        return "<User %r : is_streaming=%s>" % (self.username, self.is_streaming)


def addUser(db, username):
    with app.app_context():
        user = User(username)
        db.session.add(user)
        db.session.commit()
        return user


def setIsStreaming(db, username, is_streaming):
    with app.app_context():
        user = db.session.get(User, username)
        if not user:
            user = addUser(db, username)

        user.is_streaming = bool(is_streaming)

        if is_streaming:
            user.concurent_stream += 1
        elif user.concurent_stream > 0:
            user.concurent_stream -= 1

        db.session.commit()


def getIsStreaming(db, username):
    with app.app_context():
        user = db.session.get(User, username)
        if user:
            return user.is_streaming
        else:
            return False


with app.app_context():
    if not os.path.exists(os.path.join(os.getcwd(), "gptcache.db")):
        db.create_all()

#
# App
#


@app.route("/stream_chat")
def stream_chat():
    global user_text
    global context
    global institution
    global links
    global temperature

    if "username" in session:
        username = session["username"]
        setIsStreaming(db, username, session["is_streaming"])
    else:
        print("user need to login...")
        return

    # Route that stream the generation results
    def generate():
        try:
            prompt = f"""Question soumise au service {institution} : {user_text}
                \rPrompt : {context} {links}
                \r---Réponse : """

            acc = []
            for t in model.generate(
                prompt, max_tokens=700, temp=float(temperature), streaming=True, callback=StopGen(db, username).callback
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
            setIsStreaming(db, session["username"], False)

    # return Response(generate(), mimetype="text/event-stream")
    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@app.route("/stop_generation")
def stop_generation():
    if "username" in session:
        session["is_streaming"] = False
        setIsStreaming(db, session["username"], False)

    return "ok", 200


@app.route("/", methods=["GET", "POST"])
def index():
    global user_text
    global context
    global institution
    global links
    global temperature

    # if len(db) > 20000:
    #    db.clear()

    if "username" not in session:
        username = random_username()
        session["username"] = username
        addUser(db, username)
    elif not db.session.get(User, session["username"]):
        addUser(db, session["username"])

    if request.method == "POST":
        user_text = request.form["user_text"]
        context = request.form.get("context", context)
        institution = request.form.get("institution", institution)
        links = request.form.get("links", links)
        temperature = request.form.get("temperature", temperature)
        session["is_streaming"] = True
    else:
        session["is_streaming"] = False

    return render_template(
        "index.html",
        user_text=user_text,
        institution=institution,
        context=context,
        links=links,
        temperature=temperature,
        is_streaming=session["is_streaming"],
    )


# @app.teardown_appcontext
# def teardown_db(exception=None):
#    db.terminate()


if __name__ == "__main__":
    app.run(threaded=True, debug=True)
