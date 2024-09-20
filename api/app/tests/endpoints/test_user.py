import uuid

from api.app import crud
from fastapi.testclient import TestClient

import app.tests.utils.login as login
import app.tests.utils.user as user
from app.tests.test_api import TestApi

from pyalbert.config import KEYCLOAK_ADMIN_PASSWORD, KEYCLOAK_ADMIN_USERNAME


class TestEndpointsUser(TestApi):
    # TODO: add assert on response json
    def test_user(self, client: TestClient):
        user_tests_random_nb = str(uuid.uuid4())

        mail = "jean.dupont" + user_tests_random_nb + "@test.fr"
        username = "jean.dupont" + user_tests_random_nb
        password = "abcde12345"

        response = user.create_user_me(
            client,
            username,
            mail,
            password,
        )
        assert response.status_code == 200

        # confirm user
        crud.user.confirm_user(mail)

        # Sign in as admin to confirm user
        response = login.sign_in(
            client,
            KEYCLOAK_ADMIN_USERNAME,
            KEYCLOAK_ADMIN_PASSWORD,
        )
        access_token = "Bearer " + response.json()["access_token"]
        refresh_token = "Bearer " + response.json()["refresh_token"]

        # log out from admin
        response = login.sign_out(client, access_token, refresh_token)
        assert response.status_code == 200

        # Sign In as user
        response = login.sign_in(
            client,
            username,
            password,
        )
        assert response.status_code == 200

        access_token = "Bearer " + response.json()["access_token"]
        refresh_token = "Bearer " + response.json()["refresh_token"]

        # Read User Me:
        response = user.read_user_me(client, access_token, refresh_token)
        assert response.status_code == 200

    def test_password_errors(self, client: TestClient):
        user_tests_random_nb = str(uuid.uuid4())
        username = "jean.dupont" + user_tests_random_nb
        mail = "jean.dupont" + user_tests_random_nb + "@test.fr"

        response = user.create_user_me(
            client,
            username,
            mail,
            "A" * 129,
        )
        assert response.status_code == 422

        response = user.create_user_me(
            client,
            username,
            mail,
            "Abcdef123456)",
        )
        assert response.status_code == 422

        response = user.create_user_me(
            client,
            username,
            mail,
            "Abcdef123456#+=._-@",
        )
        assert response.status_code == 200

        # Confirm user
        crud.user.confirm_user(mail)

    def test_form_errors(self, client: TestClient):
        user_tests_random_nb = str(uuid.uuid4())
        username = "jean.dupont" + user_tests_random_nb
        mail = "jean.dupont" + user_tests_random_nb + "@test.fr"

        response = user.create_user_me(
            client,
            username,
            mail,
            "Abcdef123456#+=._-@",
            organization_id="",
            organization_name="",
        )

        assert response.status_code == 422

        response = user.create_user_me(
            client,
            username,
            mail,
            "Abcdef123456#+=._-@",
            organization_id="2",
            organization_name="2",
        )
        assert response.status_code == 422

        response = user.create_user_me(
            client,
            username,
            mail,
            "Abcdef123456#+=._-@",
            organization_id="2",
            organization_name="France services La Poste de Saint-Trivier-de-Courtes",
        )
        assert response.status_code == 200

        # Confirm user
        crud.user.confirm_user(mail)

    def test_user_tokens(self, client: TestClient):
        # Create User Me:
        user_tests_random_nb = str(uuid.uuid4())

        username = "jean.dupont" + user_tests_random_nb
        email = "jean.dupont" + user_tests_random_nb + "@test.fr"
        password = "abcde12345"

        response = user.create_user_me(
            client,
            username,
            email,
            password,
        )
        assert response.status_code == 200

        # Confirm user
        crud.user.confirm_user(email)

        # Admin - Sign In:
        response = login.sign_in(
            client,
            KEYCLOAK_ADMIN_USERNAME,
            KEYCLOAK_ADMIN_PASSWORD,
        )
        assert response.status_code == 200

        access_token = "Bearer " + response.json()["access_token"]
        refresh_token = "Bearer " + response.json()["refresh_token"]

        # Admin - Pending Users:
        response = user.read_pending_users(client, access_token, refresh_token)
        assert response.status_code == 200

        # Admin Sign out
        response = login.sign_out(client, access_token, refresh_token)
        assert response.status_code == 200

        # User - Sign In:
        response = login.sign_in(client, username, password)

        assert response.status_code == 200
        access_token = "Bearer " + response.json()["access_token"]
        refresh_token = "Bearer " + response.json()["refresh_token"]

        # Try token
        response = user.read_user_me(client, access_token, refresh_token)
        assert response.status_code == 200

        # Sign Out:
        response = login.sign_out(client, access_token, refresh_token)
        assert response.status_code == 200

        # Try token
        response = user.read_user_me(client, access_token, refresh_token)
        assert response.status_code == 401
