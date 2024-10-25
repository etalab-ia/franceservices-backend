from fastapi.testclient import TestClient

from pyalbert.config import API_PREFIX_V2

ROOT_PATH = API_PREFIX_V2


def read_chats(client: TestClient):
    return client.get(
        f"{ROOT_PATH}/chats",
    )


def create_chat(client: TestClient, chat_type):
    return client.post(
        f"{ROOT_PATH}/chat",
        json={
            "chat_type": chat_type,
        },
    )


def read_chat(client: TestClient, chat_id):
    return client.get(
        f"{ROOT_PATH}/chat/{chat_id}",
    )


def update_chat(client: TestClient, chat_id, **data):
    return client.post(
        f"{ROOT_PATH}/chat/{chat_id}",
        json=data,
    )


def read_archive(client: TestClient, chat_id):
    return client.get(
        f"{ROOT_PATH}/chat/archive/{chat_id}",
    )


def delete_chat(client: TestClient, chat_id):
    return client.delete(
        f"{ROOT_PATH}/chat/delete/{chat_id}",
    )
