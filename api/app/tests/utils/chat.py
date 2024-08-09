from fastapi.testclient import TestClient

from pyalbert.config import API_PREFIX_V2

ROOT_PATH = API_PREFIX_V2


def read_chats(client: TestClient, access_token, refresh_token):
    return client.get(
        f"{ROOT_PATH}/chats",
        headers={"access_token": access_token, "refresh_token": f"{refresh_token}"},
    )


def create_chat(client: TestClient, access_token, refresh_token, chat_type):
    return client.post(
        f"{ROOT_PATH}/chat",
        headers={"access_token": access_token, "refresh_token": refresh_token},
        json={
            "chat_type": chat_type,
        },
    )


def read_chat(client: TestClient, access_token, refresh_token, chat_id):
    return client.get(
        f"{ROOT_PATH}/chat/{chat_id}",
        headers={"access_token": access_token, "refresh_token": f"{refresh_token}"},
    )


def update_chat(client: TestClient, access_token, refresh_token, chat_id, **data):
    return client.post(
        f"{ROOT_PATH}/chat/{chat_id}",
        headers={"access_token": access_token, "refresh_token": f"{refresh_token}"},
        json=data,
    )


def read_archive(client: TestClient, access_token, refresh_token, chat_id):
    return client.get(
        f"{ROOT_PATH}/chat/archive/{chat_id}",
        headers={"access_token": access_token, "refresh_token": f"{refresh_token}"},
    )


def delete_chat(client: TestClient, access_token, refresh_token, chat_id):
    return client.delete(
        f"{ROOT_PATH}/chat/delete/{chat_id}",
        headers={"access_token": access_token, "refresh_token": f"{refresh_token}"},
    )
