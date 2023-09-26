# pylint: disable=too-many-arguments

from fastapi.testclient import TestClient

from app.main import app


def read_streams(client: TestClient, token):
    return client.get("/streams", headers={"Authorization": f"Bearer {token}"})


def create_stream(
    client: TestClient,
    token,
    user_text,
    context="",
    institution="",
    links="",
    temperature=20,
):
    return client.post(
        "/stream",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "user_text": user_text,
            "context": context,
            "institution": institution,
            "links": links,
            "temperature": temperature,
        },
    )


async def start_stream(token, stream_id):
    async with TestClient(app) as client:
        await client.get(
            f"/stream/{stream_id}/start",
            headers={"Authorization": f"Bearer {token}"},
            stream=True,
        )


def stop_stream(client: TestClient, token, stream_id):
    return client.post(f"/stream/{stream_id}/stop", headers={"Authorization": f"Bearer {token}"})


def read_stream(client: TestClient, token, stream_id):
    return client.get(f"/stream/{stream_id}", headers={"Authorization": f"Bearer {token}"})
