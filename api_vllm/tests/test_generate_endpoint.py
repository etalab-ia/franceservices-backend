import argparse
import requests
import json
import traceback
import logging

parser = argparse.ArgumentParser(description="Test the response of a LLM model.")
parser.add_argument("--port", type=int, default=8082, help="Model port")
parser.add_argument(
    "--host", type=str, default="localhost", help="Model host (default: localhost)"
)
parser.add_argument(
    "--prompt", type=str, default="Hello, world!", help="Prompt to use for the model"
)
parser.add_argument("--debug", action="store_true", help="Print debug logs")

if __name__ == "__main__":
    args = parser.parse_args()

    level = "DEBUG" if args.debug else "INFO"
    logging.basicConfig(
        format="%(asctime)s:%(levelname)s: %(message)s",
        level=logging.getLevelName(level),
    )
    logger = logging.getLogger(__name__)

    endpoint = f"http://{args.host}:{args.port}/generate"
    data = {
        "prompt": args.prompt,
        "max_tokens": 100,
        "temperature": 0,
        "stream": False,
    }

    response = requests.post(endpoint, json=data, verify=False)
    for chunk in response.iter_lines(decode_unicode=False, delimiter=b"\0"):
        try:
            text = json.loads(chunk.decode("utf-8"))["text"][0].strip()
            logger.info(text)
        except Exception:
            logger.error(traceback.format_exc())

    logger.info(f"Response: {response.text}")

    logger.debug(f"Response status code: {response.status_code}")
    logger.debug(f"Response headers: {response.headers}")
    logger.debug(f"Response content: {response.content}")

    assert response.status_code == 200, "invalid response status code"
