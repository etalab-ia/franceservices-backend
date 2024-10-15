import json
from pathlib import Path

from fastapi.testclient import TestClient
from pytest import fail
from sqlalchemy.orm import Session

from app.db.base_class import Base
from app.db.create_admin_user import get_or_create_admin_user
from app.db.init_db import init_db
from app.db.session import engine
from app.main import app
from app.mockups import install_mockups
from app.mockups.mailjet_mockup import remove_mailjet_folder

from pyalbert.clients import AlbertClient, LlmClient
from pyalbert.config import API_PREFIX_V2, LLM_TABLE

# Mocked-up model name
MODEL_NAME = ""
if len(LLM_TABLE) > 0:
    MODEL_NAME = LLM_TABLE[0]["model"]


def log_and_assert(response, code):
    if code != 200:
        assert response.status_code == code
        return

    if response.status_code != 200:
        fail(
            f"Expected status code 200, but got {response.status_code}.\nError details: {response.text if isinstance(response.text, str) else response}"
        )


def _fetch(self, method, route, headers=None, json_data=None, stream=None):
    # Just change the method fetch method of the Api/Abert client
    # by overwriting the original model. It allows to make request using
    # the fastapi test client instead of http request.
    # {stream} is ignored and handled with httpx directly in the test functions.
    with TestClient(app) as c:
        d = {
            "POST": c.post,
            "GET": c.get,
            "PUT": c.put,
            "DELETE": c.delete,
        }
        url = "/" + API_PREFIX_V2.strip("/") if API_PREFIX_V2 else "/"
        response = d[method](f"{url}{route}", headers=headers, json=json_data)
        response.raise_for_status()
        return response


def _pop_time_ref(d):
    keys_to_remove = ["created_at", "updated_at"]
    if isinstance(d, dict):
        for key in keys_to_remove:
            d.pop(key, None)
        for key in d:
            _pop_time_ref(d[key])
    elif isinstance(d, list):
        for item in d:
            _pop_time_ref(item)

    return d


def _load_case(name, path="cases"):
    local_dir = Path(__file__).parent
    basename = local_dir / path / name
    payload = None
    with open(f"{basename}.json") as f:
        payload = json.load(f)

    return payload


class TestApi:
    model_name = MODEL_NAME

    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        db: Session = init_db()
        install_mockups()
        get_or_create_admin_user(db)

        AlbertClient._fetch = _fetch

    def teardown_method(self):
        remove_mailjet_folder()

    def test_mockup(self, mock_server_es, mock_server_qdrant, mock_server_models):
        # Start the server
        pass
