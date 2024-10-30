import os
import subprocess
import time
from pathlib import Path
from typing import Generator
from urllib.parse import urlparse

import pytest
import requests
from fastapi.testclient import TestClient

os.environ["ENV"] = "unittest"
from app.db.session import SessionLocal
from app.main import app

from pyalbert.config import ELASTIC_PORT, LLM_TABLE, PROCONNECT_PORT, PROCONNECT_URL, QDRANT_REST_PORT

if len(LLM_TABLE) > 0:
    LLM_HOST, LLM_PORT = urlparse(LLM_TABLE[0]["url"]).netloc.split(":")

def start_mock_server(
    command, health_route="/healthcheck", health_headers=None, timeout=10, interval=1, cwd=None
):
    """Starts a mock server using subprocess.Popen and waits for it to be ready
    by polling a health check endpoint.
    """
    process = subprocess.Popen(command, cwd=cwd)
    try:
        end_time = time.time() + timeout
        while True:
            try:
                host = "localhost"
                port = command[-1]
                response = requests.get(
                    f"http://{host}:{port}" + health_route, headers=health_headers
                )
                if response.status_code == 200:
                    # Server is ready
                    break
            except requests.ConnectionError:
                # Server not ready yet
                pass

            if time.time() > end_time:
                raise RuntimeError("Timeout waiting for server to start")

            time.sleep(interval)
    except Exception as e:
        process.kill()
        raise e

    return process


#
# API mockups
#

APP_FOLDER = Path(__file__).parents[2]


@pytest.fixture(scope="session")
def mock_server_es():
    process = start_mock_server(
        ["uvicorn", "app.tests.mockups.elasticsearch:app", "--port", ELASTIC_PORT],
        cwd=APP_FOLDER,
    )
    yield
    process.kill()


@pytest.fixture(scope="session")
def mock_server_qdrant():
    process = start_mock_server(
        ["uvicorn", "app.tests.mockups.qdrant:app", "--port", QDRANT_REST_PORT],
        cwd=APP_FOLDER,
    )
    yield
    process.kill()


# @pytest.fixture(scope="session")
# def mock_server_models():
#     process = start_mock_server(["uvicorn", "app.tests.mockups.llm:app", "--port", LLM_PORT])
#     yield
#     process.kill()


@pytest.fixture(scope="session")
def mock_server_models():
    process = start_mock_server(
        ["prism", "mock", "app/tests/mockups/openai-openapi.yaml", "-p", LLM_PORT],
        health_route="/models",
        health_headers={"Authorization": "Bearer IAM_HERE"},
        cwd=APP_FOLDER,
    )
    yield
    process.kill()


#
# Api client
#


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """
    Create a test client with authentication for all tests
    """
    with TestClient(app) as test_client:
        # Login and set tokens
        login_response = requests.get(f"{PROCONNECT_URL}/mocked-login")
        assert login_response.status_code == 200
        
        # Set session cookie
        session_cookie = login_response.cookies["session"]
        test_client.cookies.set("session", session_cookie)
        
        # Set CSRF token in both cookie and header
        csrf_token = login_response.cookies["csrftoken"]
        test_client.cookies.set("csrftoken", csrf_token)
        test_client.headers["csrftoken"] = csrf_token
        
        yield test_client


#
# DB
#


@pytest.fixture(scope="session")
def db() -> Generator:
    try:
        session = SessionLocal()
        yield session
    finally:
        session.close()
    print("Teardown session.")

# proconnect
@pytest.fixture(scope="session")
def mock_server_proconnect():
    process = start_mock_server(["uvicorn", "app.tests.mockups.proconnect:app", "--port", PROCONNECT_PORT], cwd=APP_FOLDER)
    yield
    process.kill()
