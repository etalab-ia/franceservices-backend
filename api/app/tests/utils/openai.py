import httpx
from fastapi.testclient import TestClient

from app.main import app

from pyalbert.config import API_PREFIX_V1

ROOT_PATH = API_PREFIX_V1


def chat_completions(client: TestClient, access_token, refresh_token, data):
    headers = None
    if access_token and refresh_token:
        headers = {"access_token": access_token, "refresh_token": refresh_token}

    return client.post(
        f"{ROOT_PATH}/chat/completions",
        headers=headers,
        json=data,
    )


async def chat_completion_stream(client: TestClient, access_token, refresh_token, data):
    headers = None
    if access_token and refresh_token:
        headers = {"access_token": access_token, "refresh_token": refresh_token}
    # async with TestClient(app) as client:
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        async with client.stream(
            "POST",
            f"{ROOT_PATH}/chat/completions",
            headers=headers,
            json=data,
        ) as response:
            response.encoding = "utf-8"
            content = await response.aread()
            return response, content


def create_embeddings(client: TestClient, data):
    return client.post(
        f"{ROOT_PATH}/embeddings",
        json=data,
    )
