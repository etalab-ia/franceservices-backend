from fastapi.testclient import TestClient


def get_models(client: TestClient, token):
    return client.get("/models", headers={"Authorization": f"Bearer {token}"})


def get_institutions(client: TestClient, token):
    return client.get("/institutions", headers={"Authorization": f"Bearer {token}"})


def get_mfs_organizations(client: TestClient, token):
    return client.get("/organizations/mfs", headers={"Authorization": f"Bearer {token}"})
