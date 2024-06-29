from fastapi.testclient import TestClient

from pyalbert.config import API_PREFIX_V2

ROOT_PATH = API_PREFIX_V2


def get_models(client: TestClient, token):
    return client.get(f"{ROOT_PATH}/models", headers={"Authorization": f"Bearer {token}"})


def get_institutions(client: TestClient, token):
    return client.get(f"{ROOT_PATH}/institutions", headers={"Authorization": f"Bearer {token}"})


def get_mfs_organizations(client: TestClient, token):
    return client.get(
        f"{ROOT_PATH}/organizations/mfs", headers={"Authorization": f"Bearer {token}"}
    )
