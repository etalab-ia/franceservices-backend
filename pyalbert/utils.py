import functools
import json
import time
from typing import Generator

from requests import Response


def retry(tries: int = 3, delay: int = 2):
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
                # @TODO: Catch network error.
                #except (requests.exceptions.RequestException, httpx.RequestError) as e:
                except Exception as e:
                    print(f"Error: {e}, retrying in {delay} seconds...")
                    time.sleep(delay)
                    attempts -= 1
            # Final attempt without catching exceptions
            return func(*args, **kwargs)

        return wrapper

    return decorator_retry


def log_and_raise_for_status(response: Response, msg_on_error: str = "API Error detail"):
    # response from requests module
    if not response.ok:
        try:
            error_detail = response.json().get("detail")
        except Exception:
            error_detail = response.text
        print(f"{msg_on_error}: {error_detail}\n")
        response.raise_for_status()


#
# Openai stream SSE decoder
#

def sse_decode_chunk(chunk:bytes) -> str:
    text = ""

    decoded_line = chunk.decode("utf-8")
    for data in decoded_line.split("\n\n"):
        _, _, data = data.partition("data: ")
        if not data:
            continue
        if data == "[DONE]":
            break

        event = json.loads(data)
        if event == "[DONE]":
            break
        if (
            not event.get("choices")
            or not event["choices"][0].get("delta")
            or not event["choices"][0]["delta"].get("content")
        ):
            continue

        text += event["choices"][0]["delta"]["content"]

    return text

def sse_decoder(generator) -> Generator:
    for chunk in generator:
        if not chunk:
            continue

        try:
            data = {}
            data["text"] = sse_decode_chunk(chunk)
            yield data
        except (json.decoder.JSONDecodeError, KeyError) as e:
            print(f"\nSSE decoder error: {e}")
            print(f"  DATA: {data}\n")
            raise e
