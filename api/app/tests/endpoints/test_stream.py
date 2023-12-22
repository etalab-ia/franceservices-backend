from fastapi.testclient import TestClient
import pytest

from app.config import FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD
from app.tests.test_class import TestClass
from app.tests.utils.login import sign_in
from app.tests.utils.chat import create_chat
from app.tests.utils.stream import (
    create_chat_stream,
    create_user_stream,
    read_stream,
    read_streams,
    start_stream,
    stop_stream,
)


class TestEndpointsStream(TestClass):
    # TODO: add assert on response json
    @pytest.mark.asyncio
    def test_user_stream(self, client: TestClient):
        # Sign In:
        response = sign_in(client, FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD)
        assert response.status_code == 200
        token = response.json()["token"]

        # Read Streams:
        response = read_streams(client, token)
        assert response.status_code == 200

        # Create User Stream:
        response = create_user_stream(
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

    # TODO: add assert on response json
    @pytest.mark.asyncio
    def test_chat_stream(self, client: TestClient):
        # Sign In:
        response = sign_in(client, FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD)
        assert response.status_code == 200
        token = response.json()["token"]

        # Read Streams:
        response = read_streams(client, token)
        assert response.status_code == 200

        # Create Chat:
        response = create_chat(client, token)
        assert response.status_code == 200
        chat_id = response.json()["id"]

        # Create Chat Stream:
        response = create_chat_stream(
            client, token, chat_id, "fabrique-miaou", "Merci pour le service Service-Public+. Bien à vous."
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
