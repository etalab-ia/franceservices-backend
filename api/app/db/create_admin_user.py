from datetime import datetime

from app import crud

from pyalbert.config import KEYCLOAK_ADMIN_EMAIL, KEYCLOAK_ADMIN_PASSWORD, KEYCLOAK_ADMIN_USERNAME


def create_admin_user():
    admin_user = crud.user.get_user_by_email(KEYCLOAK_ADMIN_EMAIL)
    if not admin_user:
        admin_user = crud.user.create_user(
            {
                "username": KEYCLOAK_ADMIN_USERNAME,
                "email": KEYCLOAK_ADMIN_EMAIL,
                "enabled": True,
                "attributes": {
                    "is_admin": True,
                    "is_confirmed": True,
                    "created_at": datetime.utcnow().isoformat(),
                },
                "credentials": [{"value": KEYCLOAK_ADMIN_PASSWORD, "type": "password"}],
            }
        )
