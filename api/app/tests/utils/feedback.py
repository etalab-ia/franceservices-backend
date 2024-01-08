# pylint: disable=too-many-arguments

from fastapi.testclient import TestClient


def read_feedbacks(client: TestClient, token):
    return client.get("/feedbacks", headers={"Authorization": f"Bearer {token}"})


def create_feedback(client: TestClient, token, stream_id, data):
    return client.post(f"/feedback/add/{stream_id}", headers={"Authorization": f"Bearer {token}"}, json=data)


def read_feedback(client: TestClient, token, feedback_id):
    return client.get(f"/feedback/{feedback_id}", headers={"Authorization": f"Bearer {token}"})
