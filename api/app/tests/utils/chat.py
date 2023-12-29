# pylint: disable=too-many-arguments

from fastapi.testclient import TestClient


def read_chats(client: TestClient, token):
    return client.get("/chats", headers={"Authorization": f"Bearer {token}"})


def create_chat(client: TestClient, token, chat_type):
    return client.post(
        "/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "chat_type": chat_type,
        },
    )


def read_chat(client: TestClient, token, chat_id):
    return client.get(f"/chat/{chat_id}", headers={"Authorization": f"Bearer {token}"})
