from fastapi.testclient import TestClient

from pyalbert.config import API_PREFIX_V2

ROOT_PATH = API_PREFIX_V2


def read_pending_users(client: TestClient, access_token, refresh_token):
    return client.get(
        f"{ROOT_PATH}/users/pending",
        headers={"access_token": access_token, "refresh_token": refresh_token},
    )


def create_user_me(client: TestClient, username, email, password, **kwargs):
    data = {
        "username": username,
        "email": email,
        "password": password,
    }
    if kwargs:
        data.update(kwargs)

    return client.post(f"{ROOT_PATH}/user/me", json=data)


def read_user_me(client: TestClient, access_token, refresh_token):
    return client.get(
        f"{ROOT_PATH}/user/me",
        headers={"access_token": access_token, "refresh_token": refresh_token},
    )


def confirm_user(client: TestClient, access_token, refresh_token, email, is_confirmed):
    return client.post(
        f"{ROOT_PATH}/user/confirm",
        headers={"access_token": access_token, "refresh_token": refresh_token},
        json={
            "email": email,
            "is_confirmed": is_confirmed,
        },
    )
