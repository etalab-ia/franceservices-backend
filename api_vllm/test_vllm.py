#!/bin/python

import json

import requests

url = "http://localhost:8081"
user_text = """Question soumise au service: Merci pour le service Service-Public+. Bien à vous.
###Réponse : """

# Send POST request with string parameter
headers = {"Content-Type": "application/json"}
data = {
    "prompt": user_text,
    "max_tokens": 500,
    "temperature": 0.2,
    "stream": True,
}
# response = requests.post(url + "/api/fabrique", data=data, headers=headers, verify=False)

# Open server-sent-event stream
response = requests.post(url + "/generate", json=data, stream=True, verify=False)

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
