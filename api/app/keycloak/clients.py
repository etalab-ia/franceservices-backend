import os

from keycloak import KeycloakAdmin, KeycloakOpenID, KeycloakOpenIDConnection


def client_openid():
    return KeycloakOpenID(
        server_url=os.environ["KEYCLOAK_API_URL"],
        client_id=os.environ["KEYCLOAK_CLIENT_ID"],
        client_secret_key=os.environ["KEYCLOAK_SECRET_KEY"],
        realm_name=os.environ["KEYCLOAK_REALM"],
        verify=False,
    )


def client_admin():
    keycloak_connection = KeycloakOpenIDConnection(
        server_url=os.environ["KEYCLOAK_API_URL"],
        client_id=os.environ["KEYCLOAK_CLIENT_ID"],
        client_secret_key=os.environ["KEYCLOAK_SECRET_KEY"],
        realm_name=os.environ["KEYCLOAK_REALM"],
        username=os.environ["KEYCLOAK_ADMIN_USERNAME"],
        password=os.environ["KEYCLOAK_ADMIN_PASSWORD"],
        verify=False,
    )

    return KeycloakAdmin(connection=keycloak_connection)
