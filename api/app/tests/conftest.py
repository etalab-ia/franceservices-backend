import os
import subprocess
import time
from typing import Generator
from urllib.parse import urlparse

import pytest
import requests
from fastapi.testclient import TestClient

os.environ["ENV"] = "unittest"
from app.db.create_admin_user import get_or_create_admin_user
from app.db.session import SessionLocal
from app.main import app

from pyalbert.config import ELASTIC_PORT, LLM_TABLE, QDRANT_REST_PORT

if len(LLM_TABLE) > 0:
    LLM_HOST, LLM_PORT = urlparse(LLM_TABLE[0][1]).netloc.split(":")


def start_mock_server(command, health_route="/healthcheck", timeout=10, interval=1):
    """Starts a mock server using subprocess.Popen and waits for it to be ready
    by polling a health check endpoint.
    """
    process = subprocess.Popen(command)

    try:
        end_time = time.time() + timeout
        while True:
            try:
                host = "localhost"
                port = command[-1]
                response = requests.get(f"http://{host}:{port}" + health_route)
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


@pytest.fixture(scope="session")
def mock_server1():
    process = start_mock_server(
        ["uvicorn", "app.tests.mockups.elasticsearch:app", "--port", ELASTIC_PORT]
    )
    yield
    process.kill()


@pytest.fixture(scope="session")
def mock_server2():
    process = start_mock_server(
        ["uvicorn", "app.tests.mockups.qdrant:app", "--port", QDRANT_REST_PORT]
    )
    yield
    process.kill()


@pytest.fixture(scope="session")
def mock_server3():
    process = start_mock_server(["uvicorn", "app.tests.mockups.llm:app", "--port", LLM_PORT])
    yield
    process.kill()


#
# Api client
#


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c


#
# DB
#


@pytest.fixture(scope="session")
def db() -> Generator:
    print("Setup session...")
    try:
        session = SessionLocal()
        yield session
    finally:
        session.close()
    print("Teardown session.")
