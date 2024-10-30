import asyncio

import pytest
from fastapi.testclient import TestClient

import app.tests.utils.openai as openai
from app.tests.test_api import TestApi, log_and_assert

from pyalbert.clients import LlmClient
from pyalbert.config import LLM_TABLE

# Define multiple test cases for conversations
conversation_testcases = [
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
    {"strategy": "last"},
    {"strategy": "last", "limit": 10},
    {"strategy": "last", "limit": 10, "mode": "rag"},
]

embedding_testcases = [
    {"model": "albert", "input": "embed this text"},
    {"model": "albert", "input": ["embed this text", "and this one"]},
]


class TestEndpointsUser(TestApi):
    @pytest.mark.usefixtures("mock_server_proconnect")
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
        response = openai.chat_completions(client, conversation)
        assert response.status_code in [400, 401, 403]

    @pytest.mark.parametrize("conversation", conversation_testcases)
    @pytest.mark.parametrize("rag", rag_testcases)
    @pytest.mark.parametrize("stream", [True, False])
    @pytest.mark.usefixtures("mock_server_proconnect")
    def test_chat_completion(self, client: TestClient, conversation, rag, stream):
        model_ = LLM_TABLE[0]
        api_key = model_["key"]

        conversation["stream"] = stream
        if rag:
            conversation["rag"] = rag
            
        # Authenticated user
        if stream:
            response, _ = asyncio.run(
                openai.chat_completion_stream(client, conversation, key=api_key)
            )
        else:
            response = openai.chat_completions(client, conversation, key=api_key)

        log_and_assert(response, 200)

        if not stream:
            response_json = response.json()
            assert "choices" in response_json
            assert len(response_json["choices"]) > 0
            assert "message" in response_json["choices"][0]
            assert "content" in response_json["choices"][0]["message"]

        # Test LlmClient
        model_name = model_["model"]
        aclient = LlmClient(model_name)
     
        try:
            result = aclient.generate(messages=conversation["messages"], rag=rag)
        except Exception as e:
            print("Exception occurred:", e)
            result = None

        if result is None:
            print("Result is None. Likely due to an authentication error or an issue with the request.")
        else:
            print("Result:", result)

        assert result is not None, "Result should not be None"
        assert hasattr(result, 'choices'), "Result should have 'choices' attribute"
        assert len(result.choices[0].message.content) > 0

    @pytest.mark.parametrize("input", embedding_testcases)
    @pytest.mark.usefixtures("mock_server_proconnect")
    def test_create_embeddings(self, client: TestClient, input):
        model_ = LLM_TABLE[0]
        api_key = model_["key"]

        # Authenticated user
        response = openai.create_embeddings(client, data=input, key=api_key)

        log_and_assert(response, 200)

        response_json = response.json()
        assert "data" in response_json
        assert len(response_json["data"]) > 0
        assert "embedding" in response_json["data"][0]
