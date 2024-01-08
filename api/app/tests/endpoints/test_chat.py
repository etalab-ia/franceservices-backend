from fastapi.testclient import TestClient
import pytest

from app.config import FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD
from app.tests.test_class import TestClass
from app.tests.utils.login import sign_in
from app.tests.utils.chat import create_chat, read_chat, read_chats


class TestEndpointsChat(TestClass):
    # TODO: add assert on response json
    @pytest.mark.asyncio
    def test_chat(self, client: TestClient):
        # Sign In:
        response = sign_in(client, FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD)
        assert response.status_code == 200
        token = response.json()["token"]

        # Read Chats:
        response = read_chats(client, token)
        assert response.status_code == 200

        # Create Chat:
        response = create_chat(client, token, "qa")
        assert response.status_code == 200
        chat_id = response.json()["id"]

        # Read Chat:
        response = read_chat(client, token, chat_id)
        assert response.status_code == 200
