import functools
import os
import time

import requests


def retry(tries=3, delay=2):
    """
    A simple retry decorator that catch exception to retry multiple times
    @TODO: only catch only network error/timeout error.

    Parameters:
    - tries: Number of total attempts.
    - delay: Delay between retries in seconds.
    """

    def decorator_retry(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = tries
            while attempts > 1:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Error: {e}, retrying in {delay} seconds...")
                    time.sleep(delay)
                    attempts -= 1
            # Final attempt without catching exceptions
            return func(*args, **kwargs)

        return wrapper

    return decorator_retry


class LlmClientV1:
    def __init__(self, model, api_token=None):
        if "mixtral-" in model or "mistral-" in model:
            self.endpoint = "https://api.mistral.ai/v1/chat/completions"
            self.api_token = os.getenv("MISTRAL_API_KEY")
        elif "gpt-" in model:
            self.endpoint = "https://api.openai.com/v1/chat/completions"
            self.api_token = os.getenv("OPENAI_API_KEY")
        else:
            raise NotImplementedError("Unknow model")

        self.model = model
        if api_token:
            self.api_token = api_token

    @retry(tries=3, delay=2)
    def chat_completion(self, messages: list[dict], **sampling_params):
        # Headers including the Content-Type, Accept, and Authorization with the Bearer token
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }

        # Making the POST request to the API
        data = {"model": self.model, "messages": messages}
        data.update(sampling_params)
        response = requests.post(self.endpoint, json=data, headers=headers)

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            print(f"Error: {response.status_code}, {response.text}")
            response.raise_for_status()

    # TODO:
    def create_embeddings(texts: str | list[str], doc_type: str | None = None):
        raise NotImplementedError
