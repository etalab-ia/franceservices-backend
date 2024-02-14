#!/bin/python

import json
import sys

import requests

sys.path.append(".")
from commons import get_prompter

prompter = get_prompter("albert-light", mode="rag")

while 1:
    query = input(">>> Dis-moi quelque chose : ")
    # Prompter
    # --
    # limit: the max number of hit the RAG should return
    # llama_chat: format pompt with llama2 chat syntax (eos, bos, inst etc)
    dialog = prompter.make_prompt(query=query, limit=4)
    #print(dialog)

    # Send POST request with string parameter
    url = "http://localhost:8082"
    headers = {"Content-Type": "application/json"}
    data = {
        "prompt": dialog,
        "max_tokens": 2048,
        "temperature": 0.2,
        "stream": True,
    }
    # response = requests.post(url + "/api/fabrique", data=data, headers=headers, verify=False)

    # Open server-sent-event stream
    try:
        response = requests.post(url + "/generate", json=data, stream=True, verify=False)
    except Exception as e:
        print("Error: Request failed with message - %s" % e)
        continue

    # Print the streamed response
    prev_len = 0
    for chunk in response.iter_lines(decode_unicode=False, delimiter=b"\0"):
        if not chunk:
            continue

        data = json.loads(chunk.decode("utf-8"))
        output = data["text"][0]
        # yield output
        print(output[prev_len:], end="", flush=True)
        prev_len = len(output)

    print()
