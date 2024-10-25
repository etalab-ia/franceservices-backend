from fastapi.testclient import TestClient

from pyalbert.config import API_PREFIX_V2

ROOT_PATH = API_PREFIX_V2


def get_models(client: TestClient):
    return client.get(
        f"{ROOT_PATH}/models",
    )


def get_institutions(client: TestClient):
    return client.get(
        f"{ROOT_PATH}/institutions",
    )


def get_mfs_organizations(client: TestClient):
    return client.get(
        f"{ROOT_PATH}/organizations/mfs",
    )
