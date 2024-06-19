import os

from keycloak import KeycloakAdmin, KeycloakOpenID, KeycloakOpenIDConnection


def client_openid():
    return KeycloakOpenID(
        server_url=os.environ["KEYCLOAK_API_URL"],
        client_id="fastapi-albert-client",
        client_secret_key="7IlmNOFvXNdMZT1hXT9CJHAy9gMlyYq6",
        realm_name="albert",
    )


def client_admin():
    keycloak_connection = KeycloakOpenIDConnection(
        server_url=os.environ["KEYCLOAK_API_URL"],
        client_id="fastapi-albert-client",
        client_secret_key="7IlmNOFvXNdMZT1hXT9CJHAy9gMlyYq6",
        realm_name="albert",
        username="admin",
        password="admin",
    )

    return KeycloakAdmin(connection=keycloak_connection)
