from fastapi.testclient import TestClient

from pyalbert.config import API_PREFIX_V2

ROOT_PATH = API_PREFIX_V2


def get_models(client: TestClient, access_token, refresh_token):
    return client.get(
        f"{ROOT_PATH}/models",
        headers={"access_token": access_token, "refresh_token": refresh_token},
    )


def get_institutions(client: TestClient, access_token, refresh_token):
    return client.get(
        f"{ROOT_PATH}/institutions",
        headers={"access_token": access_token, "refresh_token": refresh_token},
    )


def get_mfs_organizations(client: TestClient, access_token, refresh_token):
    return client.get(
        f"{ROOT_PATH}/organizations/mfs",
        headers={"access_token": access_token, "refresh_token": refresh_token},
    )
