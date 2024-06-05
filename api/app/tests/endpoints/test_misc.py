import app.tests.utils.login as login
import app.tests.utils.misc as misc
import pytest
from app.tests.test_api import TestApi
from fastapi.testclient import TestClient
from pyalbert.config import FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD


class TestEndpointsMisc(TestApi):
    # TODO: add assert on response json
    @pytest.mark.asyncio
    def test_misc(self, client: TestClient):
        # Sign In:
        response = login.sign_in(client, FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD)
        assert response.status_code == 200
        token = response.json()["token"]

        # Read models:
        response = misc.get_models(client, token)
        assert response.status_code == 200

        # Read institutions:
        response = misc.get_institutions(client, token)
        assert response.status_code == 200

        # Read mfs organization:
        response = misc.get_mfs_organizations(client, token)
        assert response.status_code == 200
