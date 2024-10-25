from fastapi.testclient import TestClient

from pyalbert.config import API_PREFIX_V2

ROOT_PATH = API_PREFIX_V2


def read_feedbacks(client: TestClient):
    return client.get(
        f"{ROOT_PATH}/feedbacks",
    )


def create_feedback(client: TestClient, stream_id, data):
    return client.post(
        f"{ROOT_PATH}/feedback/add/{stream_id}",
        json=data,
    )


def read_feedback(client: TestClient, feedback_id):
    return client.get(
        f"{ROOT_PATH}/feedback/{feedback_id}",
    )


def delete_feedback(client: TestClient, feedback_id):
    return client.delete(
        f"{ROOT_PATH}/feedback/delete/{feedback_id}",
    )
