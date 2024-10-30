import pytest
from fastapi.testclient import TestClient
import requests

import app.tests.utils.chat as chat
from app.tests.test_api import TestApi
from pyalbert.config import PROCONNECT_URL

class TestEndpointsChat(TestApi):
    @pytest.mark.asyncio
    @pytest.mark.usefixtures("mock_server_proconnect")
    def test_chat(self, client: TestClient):
        # Read Chats:
        response = chat.read_chats(client)
        assert response.status_code == 200
       
        assert isinstance(response.json(), list), "Expected a list of chats"

        # Create Chat:
        response = chat.create_chat(client, "qa")
        assert response.status_code == 200
        chat_data = response.json()
     
        assert "id" in chat_data, "Expected chat_id in response"
        chat_id = chat_data["id"]
        assert chat_data["chat_type"] == "qa", "Chat type should be 'qa'"

        # Read Chat:
        response = chat.read_chat(client, chat_id)
        assert response.status_code == 200
        assert response.json()["id"] == chat_id, "Chat ID should match"

        # Update Chat:
        new_chat_name = "My new chat name"
        new_chat_type = "meeting"
        response = chat.update_chat(
            client, chat_id, chat_name=new_chat_name, chat_type=new_chat_type
        )
        assert response.status_code == 200
        updated_chat = response.json()
       
        assert updated_chat["chat_name"] == new_chat_name, "Chat name should be updated"
        assert updated_chat["chat_type"] == new_chat_type, "Chat type should be updated"

        # Read Chat again to verify updates:
        response = chat.read_chat(client, chat_id)
        assert response.status_code == 200
        read_chat = response.json()
        assert read_chat["chat_name"] == new_chat_name, "Updated chat name should persist"
        assert read_chat["chat_type"] == new_chat_type, "Updated chat type should persist"

        # Delete Chat:
        response = chat.delete_chat(client, chat_id)
        assert response.status_code == 200

        # Verify chat is deleted:
        response = chat.read_chat(client, chat_id)
        assert response.status_code == 404, "Chat should not be found after deletion"

        # Test logout
        logout_response = requests.get(f"{PROCONNECT_URL}/mocked-logout", cookies=client.cookies)
        assert logout_response.status_code == 200
        assert "session" not in logout_response.cookies

        # Verify that we can't access chats after logout
        response = chat.read_chats(client)
      
        assert response.status_code == 401, "Should not be able to read chats after logout"
