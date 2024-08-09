import json
import random
import uuid

from fastapi.testclient import TestClient

import app.tests.utils.login as login
import app.tests.utils.user as user
from app.tests.test_api import TestApi

from pyalbert.config import KEYCLOAK_ADMIN_USERNAME, KEYCLOAK_ADMIN_PASSWORD


class TestEndpointsUser(TestApi):
    # TODO: add assert on response json
    def test_user(self, client: TestClient):
        user_tests_random_nb = str(uuid.uuid4())

        response = user.create_user_me(
            client,
            "jean.dupont" + user_tests_random_nb,
            "jean.dupont" + user_tests_random_nb + "@test.fr",
            "abcde12345",
        )
        assert response.status_code == 200

        # Sign in as admin to confirm user
        response = login.sign_in(
            client,
            KEYCLOAK_ADMIN_USERNAME,
            KEYCLOAK_ADMIN_PASSWORD,
        )
        access_token = "Bearer " + response.json()["access_token"]
        refresh_token = "Bearer " + response.json()["refresh_token"]

        # confirm user
        response = user.confirm_user(
            client,
            access_token,
            refresh_token,
            "jean.dupont" + user_tests_random_nb + "@test.fr",
            True,
        )
        assert response.status_code == 200

        # log out from admin
        response = login.sign_out(client, access_token, refresh_token)
        assert response.status_code == 200

        # Sign In as user
        response = login.sign_in(
            client,
            "jean.dupont" + user_tests_random_nb,
            "abcde12345",
        )
        assert response.status_code == 200
        
        access_token = "Bearer " + response.json()["access_token"]
        refresh_token = "Bearer " + response.json()["refresh_token"]

        # Read User Me:
        response = user.read_user_me(client, access_token, refresh_token)
        assert response.status_code == 200

    def test_password_errors(self, client: TestClient):
        user_tests_random_nb = str(uuid.uuid4())

        response = user.create_user_me(
            client,
            "jean.dupont" + user_tests_random_nb,
            "jean.dupont" + user_tests_random_nb + "@test.fr",
            "A" * 129,
        )
        assert response.status_code == 422

        response = user.create_user_me(
            client,
            "jean.dupont" + user_tests_random_nb,
            "jean.dupont" + user_tests_random_nb + "@test.fr",
            "Abcdef123456)",
        )
        assert response.status_code == 422

        response = user.create_user_me(
            client,
            "jean.dupont" + user_tests_random_nb,
            "jean.dupont" + user_tests_random_nb + "@test.fr",
            "Abcdef123456#+=._-@",
        )
        assert response.status_code == 200

    def test_form_errors(self, client: TestClient):
        user_tests_random_nb = str(uuid.uuid4())

        response = user.create_user_me(
            client,
            "jean.dupont" + user_tests_random_nb,
            "jean.dupont" + user_tests_random_nb + "@test.fr",
            "Abcdef123456#+=._-@",
            organization_id="",
            organization_name="",
        )

        assert response.status_code == 422

        response = user.create_user_me(
            client,
            "jean.dupont" + user_tests_random_nb,
            "jean.dupont" + user_tests_random_nb + "@test.fr",
            "Abcdef123456#+=._-@",
            organization_id="2",
            organization_name="2",
        )
        assert response.status_code == 422

        response = user.create_user_me(
            client,
            "jean.dupont" + user_tests_random_nb,
            "jean.dupont" + user_tests_random_nb + "@test.fr",
            "Abcdef123456#+=._-@",
            organization_id="2",
            organization_name="France services La Poste de Saint-Trivier-de-Courtes",
        )
        assert response.status_code == 200

    def test_confirm_user(self, client: TestClient):
        user_tests_random_nb = str(uuid.uuid4())

        username = "jean.dupont" + user_tests_random_nb
        email = "jean.dupont" + user_tests_random_nb + "@test.fr"
        password = "abcde12345"
        # Create User Me:
        response = user.create_user_me(
            client,
            username,
            email,
            password,
        )
        assert response.status_code == 200

        # Admin - Sign In:
        response = login.sign_in(client, KEYCLOAK_ADMIN_USERNAME, KEYCLOAK_ADMIN_PASSWORD)
        assert response.status_code == 200
        access_token = "Bearer " + response.json()["access_token"]
        refresh_token = "Bearer " + response.json()["refresh_token"]

        # Admin - Read pending users:
        response = user.read_pending_users(client, access_token, refresh_token)
        assert response.status_code == 200

        # Admin - Confirm User:
        response = user.confirm_user(client, access_token, refresh_token, email, True)
        assert response.status_code == 200

        # Admin - Read pending users:
        response = user.read_pending_users(client, access_token, refresh_token)
        assert response.status_code == 200

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
        print("response.json()0:", email, response.json())

        # Admin - Confirm User:
        response = user.confirm_user(client, access_token, refresh_token, email, True)
        print("response.json()1:", email, response.json())
        assert response.status_code == 200

        # Admin Sign out
        response = login.sign_out(client, access_token, refresh_token)
        assert response.status_code == 200

        # User - Sign In:
        response = login.sign_in(client, username, password)
        print("response.json()2:", username, response.json())
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
