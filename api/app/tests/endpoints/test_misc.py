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
        # Read models:
        response = misc.get_models(client)
        assert response.status_code == 200

        # Read institutions:
        response = misc.get_institutions(client)
        assert response.status_code == 200

        # Read mfs organization:
        response = misc.get_mfs_organizations(client)
        assert response.status_code == 200
