import os
import re

from fastapi.testclient import TestClient

from app.mockups.mailjet_mockup import MAILJET_FOLDER


def get_password_reset_token():
    email_filename = sorted(os.listdir(MAILJET_FOLDER))[-1]
    email_path = os.path.join(MAILJET_FOLDER, email_filename)
    with open(email_path, mode="r") as f:
        email = f.read()
    p = r"[0-9a-f]{8}[0-9a-f]{4}[0-9a-f]{4}[0-9a-f]{4}[0-9a-f]{12}"
    password_reset_token = re.search(p, email).group()
    return password_reset_token


def sign_in(client: TestClient, email, password):
    return client.post("/sign_in", json={"email": email, "password": password})


def sign_out(client: TestClient, token):
    return client.post("/sign_out", headers={"Authorization": f"Bearer {token}"})


def send_reset_password_email(client: TestClient, email):
    return client.post("/send_reset_password_email", json={"email": email})


def reset_password(client: TestClient, token, password):
    return client.post("/reset_password", json={"token": token, "password": password})
