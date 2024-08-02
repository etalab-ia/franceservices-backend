from datetime import datetime

from app import crud

from pyalbert.config import FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD, FIRST_ADMIN_USERNAME


def create_admin_user():
    admin_user = crud.user.get_user_by_email(FIRST_ADMIN_EMAIL)
    if not admin_user:
        admin_user = crud.user.create_user(
            {
                "username": FIRST_ADMIN_USERNAME,
                "email": FIRST_ADMIN_EMAIL,
                "enabled": True,
                "attributes": {
                    "is_admin": True,
                    "is_confirmed": True,
                    "created_at": datetime.utcnow().isoformat(),
                },
                "credentials": [{"value": FIRST_ADMIN_PASSWORD, "type": "password"}],
            }
        )
