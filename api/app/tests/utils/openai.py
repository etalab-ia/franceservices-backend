import httpx
from fastapi.testclient import TestClient
import requests

from app.main import app

from pyalbert.config import API_PREFIX_V1, PROCONNECT_URL

ROOT_PATH = API_PREFIX_V1


def chat_completions(client: TestClient, data, key=None):
    headers = None
    if key:
        headers = {"Authorization": "Bearer " + key}

    return client.post(
        f"{ROOT_PATH}/chat/completions",
        headers=headers,
        json=data,
    )


async def chat_completion_stream(client: TestClient, data, key=None):
    headers = None
    if key:
        headers = {"Authorization": "Bearer " + key}
    # async with TestClient(app) as client:
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        login_response = requests.get(f"{PROCONNECT_URL}/mocked-login")
        # Set session cookie
        session_cookie = login_response.cookies["session"]
        client.cookies.set("session", session_cookie)
        
        # Set CSRF token in both cookie and header
        csrf_token = login_response.cookies["csrftoken"]
        client.cookies.set("csrftoken", csrf_token)
        client.headers["csrftoken"] = csrf_token

        async with client.stream(
            "POST",
            f"{ROOT_PATH}/chat/completions",
            headers=headers,
            json=data,
        ) as response:
            response.encoding = "utf-8"
            content = await response.aread()
            return response, content


def create_embeddings(client: TestClient, data, key=None):
    headers = None
    if key:
        headers = {"Authorization": "Bearer " + key}
    return client.post(
        f"{ROOT_PATH}/embeddings",
        headers=headers,
        json=data,
    )
