import asyncio

import pytest
from fastapi.testclient import TestClient
import requests

import app.tests.utils.chat as chat
import app.tests.utils.feedback as feedback
import app.tests.utils.stream as stream
from app.tests.test_api import TestApi, _load_case, _pop_time_ref, log_and_assert
from pyalbert.config import PROCONNECT_URL

class TestEndpointsStream(TestApi):
    # TODO: add assert on response json
    @pytest.mark.asyncio
    @pytest.mark.usefixtures("mock_server_proconnect")
    def test_user_stream(self, client: TestClient):
       # Read Streams:
        response = stream.read_streams(client)
        assert response.status_code == 200

        # Create User Stream:
        response = stream.create_user_stream(
            client,
            model_name=self.model_name,
            query="Bonjour, comment allez-vous ?",
        )
        log_and_assert(response, 200)
        stream_id = response.json()["id"]

        # Read Stream:
        response = stream.read_stream(client, stream_id)
        assert response.status_code == 200

        # Start Stream:
        response = asyncio.run(stream.start_stream(client, stream_id, client.cookies))
        assert response.status_code == 200

        # Stop Stream:
        response = stream.stop_stream(client, stream_id)
        assert response.status_code == 200

    # TODO: add assert on response json
    @pytest.mark.asyncio
    @pytest.mark.usefixtures("mock_server_proconnect")
    def test_chat_stream(self, client: TestClient):
        # Read Streams:
        response = stream.read_streams(client)
        assert response.status_code == 200

        # Create Chat:
        response = chat.create_chat(client, "meeting")
        print("response: ",response)
        assert response.status_code == 200
        chat_id = response.json()["id"]

        # Create Chat Stream:
        response = stream.create_chat_stream(
            client,
            chat_id,
            model_name=self.model_name,
            query="Bonjour, comment allez-vous ?\ntest@test.test 0000000000",
        )
        assert response.status_code == 200
        stream_id = response.json()["id"]

        # Read Stream:
        response = stream.read_stream(client, stream_id)
        assert response.status_code == 200

        # Start Stream:
        response = asyncio.run(stream.start_stream(client, stream_id, client.cookies))
        assert response.status_code == 200

        # Stop Stream:
        response = stream.stop_stream(client, stream_id)
        assert response.status_code == 200

        # Send feedbacks
        response = feedback.create_feedback(
            client, stream_id, {"is_good": True}
        )
        assert response.status_code == 200

        response = feedback.create_feedback(
            client, stream_id, {"message": "that is excelent !"}
        )
        assert response.status_code == 200
        feedback_id = response.json()["id"]

        ## Create another "rag" stream
        #
        # Create Chat Stream:
        response = stream.create_chat_stream(
            client,
            chat_id,
            model_name=self.model_name,
            query="Bonjour, comment allez-vous ?\ntest@test.test 0000000000",
            mode="rag",
            with_history=True,
        )
        assert response.status_code == 200
        stream_id = response.json()["id"]

        # Start Stream:
        response = asyncio.run(stream.start_stream(client, stream_id, client.cookies))
        assert response.status_code == 200

        # Read Archive:
        response = chat.read_archive(client, chat_id)
        assert response.status_code == 200
        d = response.json()

        archive = _pop_time_ref(d)
        archive_true = _pop_time_ref(_load_case("archive"))

        # Utility code to inspecthe the true and got archive response
        # ---
        def sort_recursively(d):
            if isinstance(d, dict):
                return {k: sort_recursively(v) for k, v in sorted(d.items())}
            elif isinstance(d, list):
                return [sort_recursively(i) for i in d]
            else:
                return d

        archive_true = sort_recursively(archive_true)
        archive = sort_recursively(archive)
        # Keep the folloing  commented code for debug purpose
        # with open("archive_got.json", "w") as f:
        #    json.dump(archive, f)
        # print("==== Achive True ====")
        # print(json.dumps(archive_true, indent=2))
        # print("==== Achive GOT ====")
        # print(json.dumps(archive, indent=2))
        # WARNING: change file to adapt API change...
     
        def compare_structures_ignore_ids(d1, d2):
            if isinstance(d1, dict) and isinstance(d2, dict):
                if set(d1.keys()) != set(d2.keys()):
                    return False
                return all(compare_structures_ignore_ids(v1, d2[k]) for k, v1 in d1.items() if k != 'user_id')
            elif isinstance(d1, list) and isinstance(d2, list):
                return len(d1) == len(d2) and all(compare_structures_ignore_ids(v1, v2) for v1, v2 in zip(d1, d2))
            else:
                return d1 == d2
            
        assert compare_structures_ignore_ids(archive, archive_true)

        # Delete feedback:
        response = feedback.delete_feedback(client, feedback_id)
        assert response.status_code == 200
