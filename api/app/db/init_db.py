from app import crud, models
from app.db import base  # noqa: F401
from app.db.base_class import Base
from app.db.session import SessionLocal, engine

from pyalbert.config import FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD, FIRST_ADMIN_USERNAME

# Make sure all SQL Alchemy models are imported (app.db.base) before initializing DB
# otherwise, SQL Alchemy might fail to initialize relationships properly.
# For more details: https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/28


# TODO: use alembic
def init_db():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    user = crud.user.get_user_by_email(db, FIRST_ADMIN_EMAIL)
    if not user:
        user = models.User(
            username=FIRST_ADMIN_USERNAME,
            email=FIRST_ADMIN_EMAIL,
            hashed_password=crud.user.get_hashed_password(FIRST_ADMIN_PASSWORD),
            is_confirmed=True,
            is_admin=True,
        )
        db.add(user)
        db.commit()
