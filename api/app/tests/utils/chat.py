from fastapi.testclient import TestClient

from pyalbert.config import API_PREFIX_V2

ROOT_PATH = API_PREFIX_V2


def read_chats(client: TestClient, token):
    return client.get(f"{ROOT_PATH}/chats", headers={"Authorization": f"Bearer {token}"})


def create_chat(client: TestClient, token, chat_type):
    return client.post(
        f"{ROOT_PATH}/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "chat_type": chat_type,
        },
    )


def read_chat(client: TestClient, token, chat_id):
    return client.get(f"{ROOT_PATH}/chat/{chat_id}", headers={"Authorization": f"Bearer {token}"})


def update_chat(client: TestClient, token, chat_id, **data):
    return client.post(
        f"{ROOT_PATH}/chat/{chat_id}", headers={"Authorization": f"Bearer {token}"}, json=data
    )


def read_archive(client: TestClient, token, chat_id):
    return client.get(
        f"{ROOT_PATH}/chat/archive/{chat_id}", headers={"Authorization": f"Bearer {token}"}
    )


def delete_chat(client: TestClient, token, chat_id):
    return client.delete(
        f"{ROOT_PATH}/chat/delete/{chat_id}", headers={"Authorization": f"Bearer {token}"}
    )
