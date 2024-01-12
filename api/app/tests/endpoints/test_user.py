from fastapi.testclient import TestClient

from app.config import FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD
from app.tests.test_class import TestClass
from app.tests.utils.login import sign_in
from app.tests.utils.user import confirm_user, create_user_me, read_pending_users, read_user_me


class TestEndpointsUser(TestClass):
    # TODO: add assert on response json
    def test_user(self, client: TestClient):
        # Create User Me:
        response = create_user_me(client, "jean.dupont", "jean.dupont@test.fr", "abcde12345")
        assert response.status_code == 200

        # Sign In:
        response = sign_in(client, "jean.dupont@test.fr", "abcde12345")
        assert response.status_code == 400

        # Admin - Sign In:
        response = sign_in(client, FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD)
        assert response.status_code == 200
        admin_token = response.json()["token"]

        # Admin - Confirm User:
        response = confirm_user(client, admin_token, "jean.dupont@test.fr", True)
        assert response.status_code == 200

        # Sign In:
        response = sign_in(client, "jean.dupont@test.fr", "abcde12345")
        assert response.status_code == 200
        token = response.json()["token"]

        # Read User Me:
        response = read_user_me(client, token)
        assert response.status_code == 200

    def test_password_errors(self, client: TestClient):
        response = create_user_me(client, "jean.dupont", "jean.dupont@test.fr", "Abcde")
        assert response.status_code == 422

        response = create_user_me(client, "jean.dupont", "jean.dupont@test.fr", "A" * 129)
        assert response.status_code == 422

        response = create_user_me(client, "jean.dupont", "jean.dupont@test.fr", "Abcdef123456)")
        assert response.status_code == 422

        response = create_user_me(client, "jean.dupont", "jean.dupont@test.fr", "Abcdef123456#+=._-@")
        assert response.status_code == 200

    def test_confirm_user(self, client: TestClient):
        # Create User Me:
        response = create_user_me(client, "jean.dupont", "jean.dupont@test.fr", "abcde12345")
        assert response.status_code == 200

        # Admin - Sign In:
        response = sign_in(client, FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD)
        assert response.status_code == 200
        admin_token = response.json()["token"]

        # Admin - Read pending users:
        response = read_pending_users(client, admin_token)
        assert response.status_code == 200

        # Admin - Confirm User:
        response = confirm_user(client, admin_token, "jean.dupont@test.fr", True)
        assert response.status_code == 200

        # Admin - Confirm User:
        response = confirm_user(client, admin_token, "jean.dupont@test.fr", True)
        assert response.status_code == 400

        # Admin - Read pending users:
        response = read_pending_users(client, admin_token)
        assert response.status_code == 200
