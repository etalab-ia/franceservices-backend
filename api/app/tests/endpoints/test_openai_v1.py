import asyncio

import pytest
from fastapi.testclient import TestClient

import app.tests.utils.login as login
import app.tests.utils.openai as openai
from app.tests.test_api import TestApi

from pyalbert.config import FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD

# Define multiple test cases for conversations
conversations = [
    {
        "model": "albert",
        "messages": [{"role": "user", "content": "Hello tests."}],
    },
    {
        "model": "albert",
        "messages": [
            {"role": "system", "content": "You are a knowledgeable assistant."},
            {"role": "user", "content": "What is the capital of France?"},
        ],
        "max_tokens": 100,
        "temperature": 0.5,
    },
    {
        "model": "albert",
        "messages": [
            {"role": "user", "content": "Tell me a joke."},
            {"role": "assistant", "content": "No"},
            {"role": "user", "content": "Please do !"},
        ],
    },
    {
        "model": "albert",
        "messages": [
            {"role": "system", "content": "You are a friendly assistant."},
            {"role": "user", "content": "Tell me a joke."},
            {"role": "assistant", "content": "No"},
            {"role": "user", "content": "Please do !"},
        ],
    },
]

rag_testcases = [
    {},
    {"rag": "last"},
    {"rag": "last", "limit": 10},
    {"rag": "last", "limit": 10, "mode": "rag"},
]


class TestEndpointsUser(TestApi):
    def test_chat_completion_auth(self, client: TestClient):
        # Define the data payload with role/message structure
        conversation = {
            "model": "albert",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello tests."},
            ],
        }

        # Unauthenticated user
        response = openai.chat_completion(client, None, conversation)
        assert response.status_code == 400

    @pytest.mark.parametrize("conversation", conversations)
    @pytest.mark.parametrize("rag", rag_testcases)
    @pytest.mark.parametrize("stream", [True, False])
    def test_chat_completion(self, client: TestClient, conversation, rag, stream):
        conversation["stream"] = stream
        conversation.update(rag)

        # Sign In:
        response = login.sign_in(client, FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD)
        assert response.status_code == 200
        token = response.json()["token"]

        # Authenticated user
        if stream:
            response = asyncio.run(openai.chat_completion_stream(client, token, conversation))
        else:
            response = openai.chat_completion(client, token, conversation)

        assert response.status_code == 200

        if not stream:
            response_json = response.json()
            assert "choices" in response_json
            assert len(response_json["choices"]) > 0
            assert "message" in response_json["choices"][0]
            assert "content" in response_json["choices"][0]["message"]
