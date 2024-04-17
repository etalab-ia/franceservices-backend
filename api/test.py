#!/bin/python
import json
import re

import requests

from pyalbert.config import FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD

url = "http://127.0.0.1:8000"

# Sign In:
response = requests.post(
    f"{url}/sign_in", json={"email": FIRST_ADMIN_EMAIL, "password": FIRST_ADMIN_PASSWORD}
)
try:
    token = response.json()["token"]
except Exception:
    print(response, response.text)
    exit()


# Create Stream:
headers = {
    "Authorization": f"Bearer {token}",
}
data = {
    "query": "Quelles sont les conditions pour obtenir les APL? Sur quels site web de puis je faire ma demande ?",
    # "query": "Quel est la limite d'age pour voter en france, et quelle sont les échances électorales ?",
    # "query": "Qu'est ce que la DITP et la DINUM ?",
    "model_name": "AgentPublic/albert-light",
    "mode": "rag",
    # "sources": ["travail-emploi"],
    # "should_sids": ["F35789"],
    # "must_not_sids": ["F35789"],
    # "postprocessing": ["check_url", "check_mail", "check_number"],
    # "with_history": True,
}
# response = requests.post(f"{url}/stream/chat/1", json=data, headers=headers)
response = requests.post(f"{url}/stream", json=data, headers=headers)
if not response.ok:
    error_detail = response.json().get("detail")
    print(f"Error: {error_detail}")
    response.raise_for_status()

stream_id = response.json()["id"]

try:
    if json.loads(response.text)["postprocessing"]:
        postprocessing_activated = True
    else:
        postprocessing_activated = False
except KeyError:
    postprocessing_activated = False
    pass


# Start Stream:
data = {"stream_id": stream_id}
response = requests.get(f"{url}/stream/{stream_id}/start", json=data, headers=headers, stream=True)
if not response.ok:
    error_detail = response.json().get("detail")
    print(f"Error: {error_detail}")
    response.raise_for_status()

final_text = ""
print("-> Waiting for the response stream:")
for line in response.iter_lines():
    if not line:
        continue
    decoded_line = line.decode("utf-8")

    if postprocessing_activated:
        _, _, number_dict = decoded_line.partition("number_dict: ")
        number_dict, _, _ = number_dict.partition("mail_dict:")
        number_dict = re.sub(r"\'", '"', number_dict).strip()
        number_dict = json.loads(number_dict)

        _, _, mail_dict = decoded_line.partition("mail_dict: ")
        mail_dict, _, _ = mail_dict.partition("url_dict:")
        mail_dict = re.sub(r"\'", '"', mail_dict).strip()
        mail_dict = json.loads(mail_dict)

        _, _, url_dict = decoded_line.partition("url_dict: ")
        url_dict, _, _ = url_dict.partition("data:")
        url_dict = re.sub(r"\'", '"', url_dict).strip()
        url_dict = json.loads(url_dict)

    _, _, data = decoded_line.partition("data: ")

    try:
        text = json.loads(data)

        if postprocessing_activated:
            if text == "[DONE]":
                text = text.replace("[DONE]", "")
                final_text += text
                print(text, end="", flush=True)

                for i, dict in enumerate(url_dict):
                    if dict["new_url_full"]:
                        final_text = final_text.replace(
                            dict["new_url"], dict["new_url_full"], dict["new_url_index"]
                        )

                print("\n\n----------FINAL TEXT AFTER POSTPROCESSING-----------")
                print(f"\n{final_text}")
                print("\n----------POSTPROCESSING DICTIONARIES-----------", flush=True)
                print(f"\nURL:\n{url_dict}")
                print(f"\nMAIL:\n{mail_dict}")
                print(f"\nNUMBER:\n{number_dict}")

                break

            else:
                final_text += text
                print(text, end="", flush=True)

        else:
            if text == "[DONE]":
                break
            print(text, end="", flush=True)

    except json.decoder.JSONDecodeError as e:
        print("\nDATA: " + data)
        print("\nERROR:")
        raise e
