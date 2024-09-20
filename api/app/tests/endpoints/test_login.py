from fastapi.testclient import TestClient

import app.tests.utils.login as login
import app.tests.utils.user as user
from app.tests.test_api import TestApi

from pyalbert.config import (
    KEYCLOAK_ADMIN_EMAIL,
    KEYCLOAK_ADMIN_PASSWORD,
    KEYCLOAK_ADMIN_USERNAME,
)


class TestEndpointsLogin(TestApi):
    def test_sign_in(self, client: TestClient):
        username = KEYCLOAK_ADMIN_USERNAME
        password = KEYCLOAK_ADMIN_PASSWORD
        response = login.sign_in(client, username, password)
        assert response.status_code == 200
        response_json = response.json()
        assert "access_token" in response_json
        assert "refresh_token" in response_json
        self.access_token = "Bearer " + response_json["access_token"]
        self.refresh_token = "Bearer " + response_json["refresh_token"]

    def test_read_user_me(self, client: TestClient):
        self.test_sign_in(client)
        response = user.read_user_me(client, self.access_token, self.refresh_token)
        assert response.status_code == 200
        response_json = response.json()
        assert "username" in response_json
        assert response_json["username"] == KEYCLOAK_ADMIN_USERNAME

    def test_send_reset_password_email(self, client: TestClient):
        response = login.send_reset_password_email(client, KEYCLOAK_ADMIN_EMAIL)
        assert response.status_code == 200

    def test_sign_in_with_bad_password(self, client: TestClient):
        response = login.sign_in(client, KEYCLOAK_ADMIN_USERNAME, "new_password123")
        assert response.status_code == 400

    def test_sign_out(self, client: TestClient):
        self.test_sign_in(client)
        response = login.sign_out(client, self.access_token, self.refresh_token)
        assert response.status_code == 200
