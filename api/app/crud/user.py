from typing import Dict, List, Optional

from keycloak import KeycloakError

from app import schemas
from app.keycloak.clients import client_admin, client_openid

keycloak_admin = client_admin()
keycloak_openid = client_openid()


def userSerializer(user: dict) -> dict:
    attributes = user.get("attributes", {})
    
    def get_bool_attribute(attr_name: str) -> bool:
        attr_value = attributes.get(attr_name, ["false"])
        return attr_value[0].lower() == "true" if attr_value else False

    serialized_user = {
        "id": user.get("id"),
        "username": user.get("username"),
        "email": user.get("email"),
        "is_confirmed": user.get("emailVerified", False),
        "is_admin": get_bool_attribute("is_admin"),
        "created_at": user.get("createdTimestamp"),
        "accept_cookie": get_bool_attribute("accept_cookie"),
    }

    serialized_user = {k: v for k, v in serialized_user.items() if v is not None}

    user = schemas.User(**serialized_user)
    return user


def get_pending_users() -> List[schemas.User]:
    try:
        users = keycloak_admin.get_users({})
        unconfirmed_users = [userSerializer(user) for user in users if not user.get("emailVerified")]

        sorted_users = sorted(unconfirmed_users, key=lambda x: x.id)
        return sorted_users
    except KeycloakError as e:
        print(f"An error occurred: {e}")
        return []


def create_user(user) -> Optional[schemas.User]:
    try:
        user_id = keycloak_admin.create_user(user)
        user = get_user(user_id)
        return user
    except Exception as e:
        print("An error occurred while creating user", e)
        return None


def get_user(user_id: str) -> Optional[schemas.User]:
    try:
        user = keycloak_admin.get_user(user_id)
        return userSerializer(user)
    except KeycloakError:
        return None


def get_user_by_username(username: str) -> Optional[schemas.User]:
    try:
        users = keycloak_admin.get_users({"username": username})
        if users:
            user = userSerializer(users[0])
            return user
        else:
            return None
    except Exception as e:
        print("An error occurred while getting user by username", e)
        return None


def get_user_by_email(email: str) -> Optional[schemas.User]:
    try:
        users = keycloak_admin.get_users({"email": email})
        if users:
            user = userSerializer(users[0])
            return user
        else:
            return None
    except Exception:
        return None


def confirm_user(email: str) -> None:
    try:
        user = get_user_by_email(email)
        return keycloak_admin.update_user(user.id, {"emailVerified": True})
    except KeycloakError as e:
        print("An error occurred: %s", e)
        return None
    except Exception as e:
        print("An unexpected error occurred: ", e)
        return None


def resolve_user_token(token: str) -> Optional[schemas.User]:
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


def login_user(username: str, password: str) -> Optional[Dict[str, str]]:
    try:
        token = keycloak_openid.token(username, password)
        return token
    except KeycloakError as e:
        print(f"An error occurred: {e}")
        return None


def logout_user(token: str) -> None:
    try:
        return keycloak_openid.logout(token)
    except KeycloakError as e:
        print(f"An error occurred: {e}")


def refresh_user_token(refresh_token: str) -> Optional[Dict[str, str]]:
    try:
        token = keycloak_openid.refresh_token(refresh_token)
        return token
    except KeycloakError as e:
        print(f"An error occurred: {e}")
        return None
