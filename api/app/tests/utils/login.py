from fastapi.testclient import TestClient

from pyalbert.config import API_PREFIX_V2 as ROOT_PATH

def sign_in(client: TestClient, email, password):
    return client.post(f"{ROOT_PATH}/sign_in", json={"email": email, "password": password})


def sign_out(client: TestClient, token):
    return client.post(f"{ROOT_PATH}/sign_out", headers={"Authorization": f"Bearer {token}"})


def send_reset_password_email(client: TestClient, email):
    return client.post(f"{ROOT_PATH}/send_reset_password_email", json={"email": email})


def reset_password(client: TestClient, token, password):
    return client.post(f"{ROOT_PATH}/reset_password", json={"token": token, "password": password})
