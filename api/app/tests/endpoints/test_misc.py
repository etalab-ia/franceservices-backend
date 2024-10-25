import pytest
from fastapi.testclient import TestClient
import requests

import app.tests.utils.misc as misc
from app.tests.test_api import TestApi
from pyalbert.config import PROCONNECT_URL


class TestEndpointsMisc(TestApi):
    # TODO: add assert on response json
    @pytest.mark.asyncio
    @pytest.mark.usefixtures("mock_server_proconnect")
    def test_misc(self, client: TestClient):
        # Sign In:
        login_response = requests.get(f"{PROCONNECT_URL}/mocked-login")
        assert login_response.status_code == 200
        assert "session" in login_response.cookies

        # Attach session cookie to client
        session_cookie = login_response.cookies["session"]
        client.cookies.set("session", session_cookie)

        # Read models:
        response = misc.get_models(client)
        assert response.status_code == 200

        # Read institutions:
        response = misc.get_institutions(client)
        assert response.status_code == 200

        # Read mfs organization:
        response = misc.get_mfs_organizations(client)
        assert response.status_code == 200
