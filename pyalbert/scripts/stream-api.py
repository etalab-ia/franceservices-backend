import os
import sys

sys.path.append(".")

import pyalbert.config as config
from pyalbert.clients import AlbertClient

api_key = os.getenv("ALBERT_API_KEY")

if __name__ == "__main__":
    query = "Quelles sont les dates limite pour déclarer sa déclaration d'impots sur le revenu ?"
    api_model = "AgentPublic/llama3-instruct-8b"
    api_mode = "rag"
    with_history = False

    client = AlbertClient(api_key=api_key)

    # Create Stream:
    # --
    chat_id = None
    data = {
        "query": query,
        "model_name": api_model,
        "mode": api_mode,
        "with_history": with_history,
        # "postprocessing": ["check_url", "check_mail", "check_number"],
    }
    if with_history:
        if not chat_id:
            chat_id = client.new_chat(chat_type="qa")
            print("chat id:", chat_id)
    else:
        chat_id = None
    stream_id = client.new_stream(chat_id=chat_id, **data)

    # Start Stream
    stream = client.generate(stream_id, stream=True)
    for c in stream:
        print(c, end="", flush=True)

    print()
