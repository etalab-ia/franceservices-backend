import pytest
from api.app.crud.user import login_user
from fastapi.testclient import TestClient

import app.tests.utils.chat as chat
from app.tests.test_api import TestApi

from pyalbert.config import KEYCLOAK_ADMIN_PASSWORD, KEYCLOAK_ADMIN_USERNAME


class TestEndpointsChat(TestApi):
    # TODO: add assert on response json
    @pytest.mark.asyncio
    def test_chat(self, client: TestClient):
        # Sign In:
        response = login_user(KEYCLOAK_ADMIN_USERNAME, KEYCLOAK_ADMIN_PASSWORD)
        assert response["access_token"]

        access_token = "Bearer " + response["access_token"]
        refresh_token = "Bearer " + response["refresh_token"]

        # Read Chats:
        response = chat.read_chats(client, access_token, refresh_token)
        assert response.status_code == 200

        # Create Chat:
        response = chat.create_chat(client, access_token, refresh_token, "qa")
        assert response.status_code == 200
        chat_id = response.json()["id"]

        # Read Chat:
        response = chat.read_chat(client, access_token, refresh_token, chat_id)
        assert response.status_code == 200

        # Update Chat:
        response = chat.update_chat(
            client, access_token, refresh_token, chat_id, chat_name="My new chat name", chat_type="meeting"
        )
        assert response.status_code == 200

        # Read Chat:
        response = chat.read_chat(client, access_token, refresh_token, chat_id)
        assert response.status_code == 200

        # Delete Chat:
        response = chat.delete_chat(client, access_token, refresh_token, chat_id)
        assert response.status_code == 200
