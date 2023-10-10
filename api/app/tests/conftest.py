# pylint: disable=wrong-import-position

import os

os.environ["ENV"] = "unittest"
from typing import Generator

from fastapi.testclient import TestClient
import pytest

from app.db.session import SessionLocal
from app.main import app


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def db() -> Generator:
    yield SessionLocal()
