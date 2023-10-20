from fastapi.testclient import TestClient
import pytest

from app.config import FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD
from app.tests.test_class import TestClass
from app.tests.utils.login import sign_in
from app.tests.utils.stream import (
    create_stream,
    read_stream,
    read_streams,
    start_stream,
    stop_stream,
)


class TestEndpointsStream(TestClass):
    # TODO: add assert on response json
    @pytest.mark.asyncio
    def test_stream(self, client: TestClient):
        # Sign In:
        response = sign_in(client, FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD)
        assert response.status_code == 200
        token = response.json()["token"]

        # Read Streams:
        response = read_streams(client, token)
        assert response.status_code == 200

        # Create Stream:
        response = create_stream(
            client, token, "fabrique-miaou", "Merci pour le service Service-Public+. Bien à vous."
        )
        assert response.status_code == 200
        stream_id = response.json()["id"]

        # Read Stream:
        response = read_stream(client, token, stream_id)
        assert response.status_code == 200

        # Start Stream:
        start_stream(token, stream_id)

        # Stop Stream:
        response = stop_stream(client, token, stream_id)
        assert response.status_code == 200
