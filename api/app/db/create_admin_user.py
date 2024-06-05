from sqlalchemy.orm import Session

from app import crud
from app.models import User

from pyalbert.config import FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD, FIRST_ADMIN_USERNAME


def get_or_create_admin_user(db: Session) -> User:
    admin_user = crud.user.get_user_by_email(db, FIRST_ADMIN_EMAIL)
    if not admin_user:
        admin_user = User(
            username=FIRST_ADMIN_USERNAME,
            email=FIRST_ADMIN_EMAIL,
            hashed_password=crud.user.get_hashed_password(FIRST_ADMIN_PASSWORD),
            is_confirmed=True,
            is_admin=True,
        )
        db.add(admin_user)
        db.commit()
    return admin_user
