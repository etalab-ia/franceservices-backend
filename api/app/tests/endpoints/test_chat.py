import pytest
from fastapi.testclient import TestClient

import app.tests.utils.chat as chat
import app.tests.utils.login as login
from app.tests.test_api import TestApi

from pyalbert.config import KEYCLOAK_ADMIN_USERNAME, KEYCLOAK_ADMIN_PASSWORD


class TestEndpointsChat(TestApi):
    # TODO: add assert on response json
    @pytest.mark.asyncio
    def test_chat(self, client: TestClient):
        # Sign In:
        response = login.sign_in(client, KEYCLOAK_ADMIN_USERNAME, KEYCLOAK_ADMIN_PASSWORD)
        assert response.status_code == 200
        access_token = "Bearer " + response.json()["access_token"]
        refresh_token = "Bearer " + response.json()["refresh_token"]

        # Read Chats:
        response = chat.read_chats(client, access_token, refresh_token)
        print("response read_chats", response.json())
        assert response.status_code == 200

        # Create Chat:
        response = chat.create_chat(client, access_token, refresh_token, "qa")
        print("response create_chat", response.json())
        assert response.status_code == 200
        chat_id = response.json()["id"]

        # Read Chat:
        response = chat.read_chat(client, access_token, refresh_token, chat_id)
        print("response read_chat", response.json())
        assert response.status_code == 200

        # Update Chat:
        response = chat.update_chat(
            client, access_token, refresh_token, chat_id, chat_name="My new chat name", chat_type="meeting"
        )
        print("response update_chat", response.json())
        assert response.status_code == 200

        # Read Chat:
        response = chat.read_chat(client, access_token, refresh_token, chat_id)
        print("response read_chat", response.json())
        assert response.status_code == 200

        # Delete Chat:
        response = chat.delete_chat(client, access_token, refresh_token, chat_id)
        print("response delete_chat", response.json())
        assert response.status_code == 200
