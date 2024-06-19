from keycloak import KeycloakError

from app import schemas
from app.keycloak.clients import client_admin, client_openid

keycloak_admin = client_admin()
keycloak_openid = client_openid()


def get_pending_users():
    try:
        users = keycloak_admin.get_users({})
        unconfirmed_users = list(
            userSerializer(user)
            for user in users
            if user.get("attributes", {}).get("is_confirmed") == ["None"] and user.get("email")
        )

        sorted_users = sorted(unconfirmed_users, key=lambda x: x["id"])
        return sorted_users
    except KeycloakError as e:
        print(f"An error occurred: {e}")
        return []


# TODO: validate user data
def create_user(user):
    user_id = keycloak_admin.create_user(user)
    user = get_user(user_id)
    return user


def get_user(user_id):
    user = keycloak_admin.get_user(user_id)
    user = userSerializer(user)
    return user


def get_user_by_username(username: str):
    try:
        users = keycloak_admin.get_users({"username": username})
        if users:
            user = userSerializer(users[0])
            return user
        else:
            return None
    except KeycloakError:
        return None


def get_user_by_email(email: str):
    try:
        users = keycloak_admin.get_users({"email": email})
        if users:
            user = userSerializer(users[0])
            return user
        else:
            return None
    except KeycloakError as e:
        print(f"An error occurred: {e}")
        return None


def confirm_user(user_id: str, is_confirmed: bool):
    try:
        user = keycloak_admin.get_user(user_id)

        attributes = user.get("attributes", {})
        attributes["is_confirmed"] = str(is_confirmed)

        keycloak_admin.update_user(user_id=user_id, payload={"attributes": attributes})
    except KeycloakError as e:
        print(f"An error occurred: {e}")


#
# Tokens
#


def resolve_user_token(token: str):
    try:
        userinfo = keycloak_openid.userinfo(token)
        user = get_user(userinfo["sub"])

        return user
    except KeycloakError as e:
        print("An error occurred: %s", e)
        return None
    except Exception as e:
        print("An unexpected error occurred: ", e)
        return None


def login_user(username: str, password: str):
    try:
        token = keycloak_openid.token(username, password)
        return token
    except KeycloakError as e:
        print(f"An error occurred: {e}")
        return None


def logout_user(token: str):
    try:
        keycloak_openid.logout(token)
    except KeycloakError as e:
        print(f"An error occurred: {e}")


def refresh_user_token(refresh_token: str):
    try:
        token = keycloak_openid.refresh_token(refresh_token)
        return token
    except KeycloakError as e:
        print(f"An error occurred: {e}")
        return None


def userSerializer(user):
    attributes = user.pop("attributes", {})
    user.update(attributes)
    user = transform_dict(user)
    user = schemas.User(**user)
    return user


# transform value to a valid Boolean
def transform_value(key, value):
    key_list = ["is_confirmed", "is_admin", "accept_cookie"]

    if key not in key_list:
        return value

    value = value[0].lower()

    if value == "true":
        return True
    elif value == "false":
        return False
    else:
        return value


def transform_dict(dictionary):
    for key, value in dictionary.items():
        dictionary[key] = transform_value(key, value)
    return dictionary
