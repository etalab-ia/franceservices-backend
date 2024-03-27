import time

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models
from pyalbert.config import (
    ACCESS_TOKEN_TTL,
    FIRST_ADMIN_EMAIL,
    FIRST_ADMIN_PASSWORD,
    PASSWORD_RESET_TOKEN_TTL,
)
from app.tests.test_api import TestApi
import app.tests.utils.login as login
import app.tests.utils.user as user


class TestEndpointsLogin(TestApi):
    # TODO: add assert on response json
    def test_login(self, client: TestClient):
        # Sign In:
        response = login.sign_in(client, FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD)
        assert response.status_code == 200
        token = response.json()["token"]

        # Sign Out:
        response = login.sign_out(client, token)
        assert response.status_code == 200

        # Read User Me:
        response = user.read_user_me(client, token)
        assert response.status_code == 401

        # Send Reset Password Email:
        response = login.send_reset_password_email(client, FIRST_ADMIN_EMAIL)
        assert response.status_code == 200

        # Reset Password:
        password_reset_token = login.get_password_reset_token()
        response = login.reset_password(client, password_reset_token, "new_password123")
        assert response.status_code == 200

        # Sign In:
        response = login.sign_in(client, FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD)
        assert response.status_code == 400

        # Sign In:
        response = login.sign_in(client, FIRST_ADMIN_EMAIL, "new_password123")
        assert response.status_code == 200

    def test_purge_blacklist_tokens(self, client: TestClient, db: Session):
        # Sign In / Sign Out - Expired:
        response = login.sign_in(client, FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD)
        token_1 = response.json()["token"]
        login.sign_out(client, token_1)

        time.sleep(ACCESS_TOKEN_TTL // 2 + 1)

        # Sign In / Sign Out - Not expired:
        response = login.sign_in(client, FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD)
        token_2 = response.json()["token"]
        login.sign_out(client, token_2)

        blacklist_tokens = db.query(models.BlacklistToken).all()
        assert len(blacklist_tokens) == 2
        assert blacklist_tokens[0].token == token_1
        assert blacklist_tokens[1].token == token_2

        time.sleep(ACCESS_TOKEN_TTL // 2 + 1)

        login.sign_in(client, FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD)
        blacklist_tokens = db.query(models.BlacklistToken).all()
        assert len(blacklist_tokens) == 1
        assert blacklist_tokens[0].token == token_2

    def test_reset_password_errors(self, client: TestClient):
        # Send Reset Password Email:
        response = login.send_reset_password_email(client, FIRST_ADMIN_EMAIL)
        assert response.status_code == 200

        time.sleep(PASSWORD_RESET_TOKEN_TTL + 1)

        # Reset Password:
        password_reset_token = login.get_password_reset_token()
        response = login.reset_password(client, password_reset_token, "new_password123")
        assert response.status_code == 400
