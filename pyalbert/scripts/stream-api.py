import json
import os

import requests

import pyalbert.config as config


def log_and_raise_for_status(response: requests.Response):
    if not response.ok:
        try:
            error_detail = response.json().get("detail")
        except Exception:
            error_detail = response.text
        print(f"Error: Albert API Error Detail: {error_detail}")
        response.raise_for_status()


def new_chat(api_url, api_token) -> int:
    headers = {
        "Authorization": f"Bearer {api_token}",
    }

    data = {
        "chat_type": "qa",
    }
    response = requests.post(f"{api_url}/chat", headers=headers, json=data)
    log_and_raise_for_status(response)
    chat_id = response.json()["id"]
    return chat_id


if __name__ == "__main__":
    query = "Quelles sont les dates limite pour déclarer sa déclaration d'impots sur le revenu ?"

    api_token = os.getenv("ALBERT_API_KEY")
    api_url = config.API_URL
    api_model = "AgentPublic/llama3-instruct-8b"
    api_mode = "rag"
    with_history = False
    chat_id = None

    # Create Stream:
    headers = {
        "Authorization": f"Bearer {api_token}",
    }
    data = {
        "query": query,
        "model_name": api_model,
        "mode": api_mode,
        "with_history": with_history,
        # "postprocessing": ["check_url", "check_mail", "check_number"],
    }
    if with_history:
        if not chat_id:
            chat_id = new_chat(api_url, api_token)
            print("chat id:", chat_id)
        response = requests.post(f"{api_url}/stream/chat/{chat_id}", headers=headers, json=data)
    else:
        response = requests.post(f"{api_url}/stream", headers=headers, json=data)
    log_and_raise_for_status(response)

    stream_id = response.json()["id"]

    # Start Stream:
    # @TODO: implement non-streaming response
    data = {"stream_id": stream_id}
    response = requests.get(
        f"{api_url}/stream/{stream_id}/start", headers=headers, json=data, stream=True
    )
    log_and_raise_for_status(response)

    answer = ""
    for line in response.iter_lines():
        if not line:
            continue

        decoded_line = line.decode("utf-8")
        _, _, data = decoded_line.partition("data: ")
        try:
            text = json.loads(data)
            if text == "[DONE]":
                break
            answer += text
            print(text, end="", flush=True)
        except json.decoder.JSONDecodeError as e:
            # Should never happen...
            print("\nDATA: " + data)
            print("\nERROR:")
            raise e

    print()
