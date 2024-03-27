from fastapi.testclient import TestClient
import pytest

from pyalbert.config import FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD
from app.tests.test_api import TestApi
import app.tests.utils.login as login
import app.tests.utils.chat as chat


class TestEndpointsChat(TestApi):
    # TODO: add assert on response json
    @pytest.mark.asyncio
    def test_chat(self, client: TestClient):
        # Sign In:
        response = login.sign_in(client, FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD)
        assert response.status_code == 200
        token = response.json()["token"]

        # Read Chats:
        response = chat.read_chats(client, token)
        assert response.status_code == 200

        # Create Chat:
        response = chat.create_chat(client, token, "qa")
        assert response.status_code == 200
        chat_id = response.json()["id"]

        # Read Chat:
        response = chat.read_chat(client, token, chat_id)
        assert response.status_code == 200

        # Update Chat:
        response = chat.update_chat(
            client, token, chat_id, chat_name="My new chat name", chat_type="meeting"
        )
        assert response.status_code == 200

        # Read Chat:
        response = chat.read_chat(client, token, chat_id)
        assert response.status_code == 200
