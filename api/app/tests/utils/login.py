from fastapi.testclient import TestClient

from pyalbert.config import API_PREFIX_V2 as ROOT_PATH


def sign_in(client: TestClient, username, password):
    return client.post(f"{ROOT_PATH}/sign_in", json={"username": username, "password": password})


def sign_out(client: TestClient, access_token, refresh_token):
    return client.post(
        f"{ROOT_PATH}/sign_out",
        headers={"access_token": access_token, "refresh_token": f"{refresh_token}"},
    )


def send_reset_password_email(client: TestClient, email):
    return client.post(f"{ROOT_PATH}/send_reset_password_email", json={"email": email})
