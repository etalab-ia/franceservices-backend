from keycloak import KeycloakAdmin, KeycloakOpenID, KeycloakOpenIDConnection
from pyalbert.config import (
    KEYCLOAK_API_URL,
    KEYCLOAK_CLIENT_ID,
    KEYCLOAK_SECRET_KEY,
    KEYCLOAK_REALM,
    KEYCLOAK_ADMIN_USERNAME,
    KEYCLOAK_ADMIN_PASSWORD,
)

def client_openid():
    return KeycloakOpenID(
        server_url=KEYCLOAK_API_URL,
        client_id=KEYCLOAK_CLIENT_ID,
        client_secret_key=KEYCLOAK_SECRET_KEY,
        realm_name=KEYCLOAK_REALM,
        verify=False,
    )


def client_admin():
    keycloak_connection = KeycloakOpenIDConnection(
        server_url=KEYCLOAK_API_URL,
        client_id=KEYCLOAK_CLIENT_ID,
        client_secret_key=KEYCLOAK_SECRET_KEY,
        realm_name=KEYCLOAK_REALM,
        username=KEYCLOAK_ADMIN_USERNAME,
        password=KEYCLOAK_ADMIN_PASSWORD,
        verify=False,
    )

    return KeycloakAdmin(connection=keycloak_connection)
