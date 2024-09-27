import pytest
from api.app.crud.user import login_user
from fastapi.testclient import TestClient

import app.tests.utils.misc as misc
from app.tests.test_api import TestApi

from pyalbert.config import KEYCLOAK_ADMIN_PASSWORD, KEYCLOAK_ADMIN_USERNAME


class TestEndpointsMisc(TestApi):
    # TODO: add assert on response json
    @pytest.mark.asyncio
    def test_misc(self, client: TestClient):
        # Sign In:
        response = login_user(KEYCLOAK_ADMIN_USERNAME, KEYCLOAK_ADMIN_PASSWORD)
        assert response["access_token"]

        access_token = "Bearer " + response["access_token"]
        refresh_token = "Bearer " + response["refresh_token"]


        # Read models:
        response = misc.get_models(client, access_token, refresh_token)
        assert response.status_code == 200

        # Read institutions:
        response = misc.get_institutions(client, access_token, refresh_token)
        assert response.status_code == 200

        # Read mfs organization:
        response = misc.get_mfs_organizations(client, access_token, refresh_token)
        assert response.status_code == 200
