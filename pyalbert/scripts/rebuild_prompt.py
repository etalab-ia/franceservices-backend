#!/bin/python
import os
import sys

sys.path.append(".")

from pyalbert.clients import AlbertClient
from pyalbert.prompt import get_prompter

if __name__ == "__main__":
    config = dict(
        api_url="https://franceservices.etalab.gouv.fr/",
        api_version="/api/v2",
        username=os.getenv("FIRST_ADMIN_USERNAME"),
        password=os.getenv("FIRST_ADMIN_PASSWORD"),
    )

    client = AlbertClient(**config)

    # Rebuild a single rag prompt
    # Note: retroactive, sensitive to changes in prompt template
    stream_id = 3
    stream = client.get_stream(stream_id)
    prompter = get_prompter(stream["model_name"], stream["mode"])
    prompt = prompter.make_prompt(**stream)
    print(prompt)

    # Rebuild the full raw prompt (with potenial history/coversation)
    # Note: no retroactive, insensitive to changes in prompt template
    stream_id = 3
    full_prompt = client.review_prompt(stream_id)
    print(full_prompt)
