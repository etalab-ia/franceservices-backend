import os
import time

import openai

if "OPENAI_API_KEY" in os.environ:
    openai.api_key = os.environ["OPENAI_API_KEY"]

if "OPENAI_ORG_KEY" in os.environ:
    openai.organization = os.environ["OPENAI_ORG_KEY"]


def get_embeddings(values: list[str], model: str = "text-embedding-ada-002"):
    try:
        res = openai.Embedding.create(model=model, input=values)
    except Exception:
        # Try once more
        print("OpenAI request failed, trying one more time...")
        time.sleep(1)
        res = openai.Embedding.create(model=model, input=values)

    if isinstance(values, str):
        return res["data"][0]["embedding"]
    else:
        embeddings = []
        for i, v in enumerate(values):
            embd = res["data"][i]
            if embd["index"] != i:
                print("Error: Embeddings index not consistent")
                exit(2)
            embeddings.append(embd["embedding"])
        return embeddings


def get_embedding(text: str):
    return get_embeddings([text])[0]


def chat_completion(
    dialog: list[dict], temperature: float | None = None, model: str = "gpt-3.5-turbo", **kwargs
):
    try:
        res = openai.ChatCompletion.create(model=model, messages=dialog, temperature=temperature)
    except Exception:
        # Try once more
        print("OpenAI request failed, trying one more time...")
        time.sleep(1)
        res = openai.ChatCompletion.create(model=model, messages=dialog, temperature=temperature)

    text_out = res.choices[0].message.content
    # finish_reason = res.choices[0].finish_reason
    return text_out
