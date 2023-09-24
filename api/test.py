#!/bin/python

import json

import requests

url = "https://gpt.datascience.etalab.studio"
url = "http://localhost:4000"

user_text = "Merci pour le service Service-Public+. Bien à vous."

# Send POST request with string parameter
headers = {"Content-Type": "application/x-www-form-urlencoded"}
data = {"user_text": user_text}
response = requests.post(url + "/api/fabrique", data=data, headers=headers, verify=False)

# Keep cookie for later requests
cookies = response.cookies

print("Request Header:", response.request.headers)
print(
    f"""Response
code: {response.status_code}
header: {response.headers}
"""
    # content: {response.text[:100] if response.text else ""}
)

# Open server-sent-event stream
response = requests.get(url + "/api/fabrique_stream", stream=True, verify=False, cookies=cookies)

# Print the streamed response
print("-> Wainting for the response stream:")
for line in response.iter_lines():
    if not line:
        continue
    _, _, data = line.decode("utf-8").partition("data: ")

    text = json.loads(data)
    if text == "[DONE]":
        break
    print(text, end="", flush=True)
