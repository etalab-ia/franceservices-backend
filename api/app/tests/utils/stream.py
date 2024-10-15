import httpx
from fastapi.testclient import TestClient

from app.main import app

from pyalbert.config import API_PREFIX_V2

ROOT_PATH = API_PREFIX_V2


def read_streams(client: TestClient, token):
    return client.get(f"{ROOT_PATH}/streams", headers={"Authorization": f"Bearer {token}"})


def create_user_stream(client: TestClient, token, **data):
    return client.post(
        f"{ROOT_PATH}/stream",
        headers={"Authorization": f"Bearer {token}"},
        json=data,
    )


def create_chat_stream(client: TestClient, token, chat_id, **data):
    return client.post(
        f"{ROOT_PATH}/stream/chat/{chat_id}",
        headers={"Authorization": f"Bearer {token}"},
        json=data,
    )


async def start_stream(_, token, stream_id):
    """Get the first 1000 lines from the infinite stream and test that the output is always 'y'"""
    # async with TestClient(app) as client:
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        async with client.stream(
            "GET",
            f"{ROOT_PATH}/stream/{stream_id}/start",
            headers={"Authorization": f"Bearer {token}"},
        ) as response:
            response.encoding = "utf-8"
            async for line in response.aiter_bytes():
                pass

            return response


def stop_stream(client: TestClient, token, stream_id):
    return client.post(
        f"{ROOT_PATH}/stream/{stream_id}/stop", headers={"Authorization": f"Bearer {token}"}
    )


def read_stream(client: TestClient, token, stream_id):
    return client.get(
        f"{ROOT_PATH}/stream/{stream_id}", headers={"Authorization": f"Bearer {token}"}
    )
