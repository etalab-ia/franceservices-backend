import random
import string
from datetime import timedelta

from flask import (Flask, Response, render_template, request, session,
                   stream_with_context)
from gpt4all import GPT4All

app = Flask(__name__)
app.secret_key = "secret4all"
app.permanent_session_lifetime = timedelta(hours=2)


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

# Cache data
db = {}

#
# Utils
#


def random_username(length=8):
    characters = string.ascii_letters + "_-" + string.digits
    return "".join(random.choice(characters) for _ in range(length))


class StopGen:
    def __init__(self, db, username):
        self.db = db
        self.username = username

    def isStreaming(self):
        if self.username not in self.db:
            return False

        return self.db[self.username]["isStreaming"]

    def callback(self, token_id, token_string):
        return self.isStreaming()


#
# App
#


@app.route("/", methods=["GET", "POST"])
def index():
    global user_text
    global context
    global institution
    global links
    global temperature

    if len(db) > 20000:
        db.clear()

    if "username" not in session:
        username = random_username()
        session["username"] = username
        db[username] = {}
    else:
        username = session["username"]
        db[username] = {}

    if request.method == "POST":
        user_text = request.form["user_text"]
        context = request.form["context"]
        institution = request.form["institution"]
        links = request.form["links"]
        temperature = request.form["temperature"]
        session["isStreaming"] = True
    else:
        session["isStreaming"] = False

    return render_template(
        "index.html",
        user_text=user_text,
        institution=institution,
        context=context,
        links=links,
        temperature=temperature,
        isStreaming=session["isStreaming"],
    )


@app.route("/stream_chat")
def stream_chat():
    global user_text
    global context
    global institution
    global links
    global temperature

    if "username" in session:
        username = session["username"]
        db[username]["isStreaming"] = session["isStreaming"]
    else:
        # user need to "login"
        return

    # Route that stream the generation results
    def generate():
        try:
            prompt = f"""Question soumise au service {institution} : {user_text}
                \rPrompt: {context} {links}
                \r---Réponse : """

            with app.app_context():

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
            session["isStreaming"] = False

    # return Response(generate(), mimetype="text/event-stream")
    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@app.route("/stop_generation")
def stop_generation():
    if "username" in session:
        session["isStreaming"] = False
        db[session["username"]]["isStreaming"] = False
    return "ok", 200



if __name__ == "__main__":
    app.run(threaded=True, debug=True)
