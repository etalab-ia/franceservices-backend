from fastapi.testclient import TestClient

from pyalbert.config import API_PREFIX_V2

ROOT_PATH = API_PREFIX_V2


def read_pending_users(client: TestClient, token):
    return client.get(f"{ROOT_PATH}/users/pending", headers={"Authorization": f"Bearer {token}"})


def create_user_me(client: TestClient, username, email, password, **kwargs):
    data = {
        "username": username,
        "email": email,
        "password": password,
    }
    if kwargs:
        data.update(kwargs)

    return client.post(f"{ROOT_PATH}/user/me", json=data)


def read_user_me(client: TestClient, token):
    return client.get(f"{ROOT_PATH}/user/me", headers={"Authorization": f"Bearer {token}"})


def confirm_user(client: TestClient, token, email, is_confirmed):
    return client.post(
        f"{ROOT_PATH}/user/confirm",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": email,
            "is_confirmed": is_confirmed,
        },
    )


def create_token(client: TestClient, token, name):
    return client.post(
        f"{ROOT_PATH}/user/token/new",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": name,
        },
    )


def read_tokens(client: TestClient, token):
    return client.get(
        f"{ROOT_PATH}/user/token",
        headers={"Authorization": f"Bearer {token}"},
    )


def delete_token(client: TestClient, token, hash):
    return client.delete(
        f"{ROOT_PATH}/user/token/{hash}",
        headers={"Authorization": f"Bearer {token}"},
    )
