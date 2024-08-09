from fastapi.testclient import TestClient

from pyalbert.config import API_PREFIX_V2

ROOT_PATH = API_PREFIX_V2


def read_feedbacks(client: TestClient, access_token, refresh_token):
    return client.get(
        f"{ROOT_PATH}/feedbacks",
        headers={"access_token": access_token, "refresh_token": refresh_token},
    )


def create_feedback(client: TestClient, access_token, refresh_token, stream_id, data):
    return client.post(
        f"{ROOT_PATH}/feedback/add/{stream_id}",
        headers={"access_token": access_token, "refresh_token": refresh_token},
        json=data,
    )


def read_feedback(client: TestClient, access_token, refresh_token, feedback_id):
    return client.get(
        f"{ROOT_PATH}/feedback/{feedback_id}",
        headers={"access_token": access_token, "refresh_token": refresh_token},
    )


def delete_feedback(client: TestClient, access_token, refresh_token, feedback_id):
    return client.delete(
        f"{ROOT_PATH}/feedback/delete/{feedback_id}",
        headers={"access_token": access_token, "refresh_token": refresh_token},
    )
