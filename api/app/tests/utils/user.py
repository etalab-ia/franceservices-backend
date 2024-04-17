from fastapi.testclient import TestClient


def read_pending_users(client: TestClient, token):
    return client.get("/users/pending", headers={"Authorization": f"Bearer {token}"})


def create_user_me(client: TestClient, username, email, password):
    return client.post(
        "/user/me",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )


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
