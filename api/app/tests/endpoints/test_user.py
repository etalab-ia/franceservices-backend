import json

from fastapi.testclient import TestClient

import app.tests.utils.login as login
import app.tests.utils.user as user
from app.tests.test_api import TestApi

from pyalbert.config import FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD


class TestEndpointsUser(TestApi):
    # TODO: add assert on response json
    def test_user(self, client: TestClient):
        # Create User Me:
        response = user.create_user_me(client, "jean.dupont", "jean.dupont@test.fr", "abcde12345")
        assert response.status_code == 200

        # Sign In:
        response = login.sign_in(client, "jean.dupont@test.fr", "abcde12345")
        assert response.status_code == 400

        # Admin - Sign In:
        response = login.sign_in(client, FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD)
        assert response.status_code == 200
        admin_token = response.json()["token"]

        # Admin - Confirm User:
        response = user.confirm_user(client, admin_token, "jean.dupont@test.fr", True)
        assert response.status_code == 200

        # Sign In:
        response = login.sign_in(client, "jean.dupont@test.fr", "abcde12345")
        assert response.status_code == 200
        token = response.json()["token"]

        # Read User Me:
        response = user.read_user_me(client, token)
        assert response.status_code == 200

    def test_password_errors(self, client: TestClient):
        response = user.create_user_me(client, "jean.dupont", "jean.dupont@test.fr", "Abcde")
        assert response.status_code == 422

        response = user.create_user_me(client, "jean.dupont", "jean.dupont@test.fr", "A" * 129)
        assert response.status_code == 422

        response = user.create_user_me(
            client, "jean.dupont", "jean.dupont@test.fr", "Abcdef123456)"
        )
        assert response.status_code == 422

        response = user.create_user_me(
            client, "jean.dupont", "jean.dupont@test.fr", "Abcdef123456#+=._-@"
        )
        assert response.status_code == 200

    def test_form_errors(self, client: TestClient):
        response = user.create_user_me(
            client,
            "jean.dupont",
            "jean.dupont@test.fr",
            "Abcdef123456#+=._-@",
            organization_id="",
            organization_name="",
        )
        assert response.status_code == 422

        response = user.create_user_me(
            client,
            "jean.dupont",
            "jean.dupont@test.fr",
            "Abcdef123456#+=._-@",
            organization_id="2",
            organization_name="2",
        )
        assert response.status_code == 422

        response = user.create_user_me(
            client,
            "jean.dupont",
            "jean.dupont@test.fr",
            "Abcdef123456#+=._-@",
            organization_id="2",
            organization_name="France services La Poste de Saint-Trivier-de-Courtes",
        )
        assert response.status_code == 200

    def test_confirm_user(self, client: TestClient):
        # Create User Me:
        response = user.create_user_me(client, "jean.dupont", "jean.dupont@test.fr", "abcde12345")
        assert response.status_code == 200

        # Admin - Sign In:
        response = login.sign_in(client, FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD)
        assert response.status_code == 200
        admin_token = response.json()["token"]

        # Admin - Read pending users:
        response = user.read_pending_users(client, admin_token)
        assert response.status_code == 200

        # Admin - Confirm User:
        response = user.confirm_user(client, admin_token, "jean.dupont@test.fr", True)
        assert response.status_code == 200

        # Admin - Confirm User:
        response = user.confirm_user(client, admin_token, "jean.dupont@test.fr", True)
        assert response.status_code == 400

        # Admin - Read pending users:
        response = user.read_pending_users(client, admin_token)
        assert response.status_code == 200

    def test_user_tokens(self, client: TestClient):
        # Create User Me:
        response = user.create_user_me(client, "jean.dupont", "jean.dupont@test.fr", "abcde12345")
        assert response.status_code == 200

        # Sign In:
        response = login.sign_in(client, "jean.dupont@test.fr", "abcde12345")
        assert response.status_code == 400

        # Admin - Sign In:
        response = login.sign_in(client, FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD)
        assert response.status_code == 200
        admin_token = response.json()["token"]

        # Admin - Confirm User:
        response = user.confirm_user(client, admin_token, "jean.dupont@test.fr", True)
        assert response.status_code == 200

        # Sign In:
        response = login.sign_in(client, "jean.dupont@test.fr", "abcde12345")
        assert response.status_code == 200
        token = response.json()["token"]

        # Create token
        response = user.create_token(client, token, "my_token")
        assert response.status_code == 200
        hash = json.loads(response.text)

        # Create token error
        response = user.create_token(client, token, "my token")
        assert response.status_code == 422

        # Read tokens
        response = user.read_tokens(client, token)
        assert response.status_code == 200
        tokens = response.json()
        assert len(tokens) == 1

        # Try token
        response = user.read_user_me(client, hash)
        assert response.status_code == 200

        # delete token
        response = user.delete_token(client, token, hash)
        assert response.status_code == 200

        # Read tokens
        response = user.read_tokens(client, token)
        assert response.status_code == 200
        tokens = response.json()
        assert len(tokens) == 0

        # Try token
        response = user.read_user_me(client, hash)
        assert response.status_code == 401
