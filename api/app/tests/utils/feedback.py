from fastapi.testclient import TestClient

from pyalbert.config import API_PREFIX_V2

ROOT_PATH = API_PREFIX_V2


def read_feedbacks(client: TestClient, token):
    return client.get(f"{ROOT_PATH}/feedbacks", headers={"Authorization": f"Bearer {token}"})


def create_feedback(client: TestClient, token, stream_id, data):
    return client.post(
        f"{ROOT_PATH}/feedback/add/{stream_id}",
        headers={"Authorization": f"Bearer {token}"},
        json=data,
    )


def read_feedback(client: TestClient, token, feedback_id):
    return client.get(
        f"{ROOT_PATH}/feedback/{feedback_id}", headers={"Authorization": f"Bearer {token}"}
    )


def delete_feedback(client: TestClient, token, feedback_id):
    return client.delete(
        f"{ROOT_PATH}/feedback/delete/{feedback_id}", headers={"Authorization": f"Bearer {token}"}
    )
