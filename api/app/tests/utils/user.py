from fastapi.testclient import TestClient


def read_pending_users(client: TestClient, token):
    return client.get("/users/pending", headers={"Authorization": f"Bearer {token}"})


def create_user_me(client: TestClient, username, email, password, **kwargs):
    data = {
        "username": username,
        "email": email,
        "password": password,
    }
    if kwargs:
        data.update(kwargs)

    return client.post("/user/me", json=data)


def read_user_me(client: TestClient, token):
    return client.get("/user/me", headers={"Authorization": f"Bearer {token}"})


def confirm_user(client: TestClient, token, email, is_confirmed):
    return client.post(
        "/user/confirm",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": email,
            "is_confirmed": is_confirmed,
        },
    )


def create_token(client: TestClient, token, name):
    return client.post(
        "/user/token/new",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": name,
        },
    )


def read_tokens(client: TestClient, token):
    return client.get(
        "/user/token",
        headers={"Authorization": f"Bearer {token}"},
    )


def delete_token(client: TestClient, token, hash):
    return client.delete(
        f"/user/token/{hash}",
        headers={"Authorization": f"Bearer {token}"},
    )
