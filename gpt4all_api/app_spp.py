from flask import (Flask, Response, render_template, request,
                   stream_with_context)
from gpt4all import GPT4All

app = Flask(__name__)


# Default model
model = GPT4All("ggml-model-fabrique-q4_K.bin", model_path="model")



# Default value for the form.
user_text = "Le service chat a été très facile à utiliser et la policière était très gentille, elle a répondu à toutes mes questions et es très patiente merci de son aide et de l'aide du système.  ri le 02/07/2023 à 59130 Lambersart  Posté par La personne concernée"
context = "La plateforme ma Sécurité permet de mettre en relation les citoyens avec des policières et ds policiers 24h sur 24"
institution = "moncommissariat.fr"
links = "https://www.masecurite.interieur.gouv.fr/fr"
temperature = "0.5"
isStreaming = False


@app.route("/stream_chat")
def stream_chat():
    global user_text
    global context
    global institution
    global links
    global temperature

    # Route that stream the generation results
    def generate():
        prompt = f"""Question soumise au service {institution} : {user_text}
            \rPrompt: {context} {links}
            \r---Réponse : """

        acc = []
        for t in model.generate(prompt, max_tokens=700, temp=float(temperature), streaming=True):
            # t = t.replace("\n", "<br>") # Better to  use <pre> to format generated text
            acc.append(t)
            if t.endswith((" ", "\n")) or t.startswith((" ", "\n")):
                yield "data: " + "".join(acc) + "\n\n"
                acc = []

        if len(acc) > 0:
            yield "data: " + "".join(acc) + "\n\n"

        yield "data: [DONE]\n\n"
        print("finished")

    return Response(generate(), mimetype="text/event-stream")


@app.route("/", methods=["GET", "POST"])
def index():
    global user_text
    global context
    global institution
    global links
    global temperature
    global isStreaming

    if request.method == "POST":
        user_text = request.form["user_text"]
        context = request.form["context"]
        institution = request.form["institution"]
        links = request.form["links"]
        temperature = request.form["temperature"]
        isStreaming = True

    return render_template(
        "index.html",
        user_text=user_text,
        institution=institution,
        context=context,
        links=links,
        temperature=temperature,
        isStreaming=isStreaming,
    )


if __name__ == "__main__":
    app.run(threaded=True, debug=True)
