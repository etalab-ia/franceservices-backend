import uuid

import bcrypt
from app import models, schemas
from app.auth import encode_api_token
from pydantic import EmailStr
from sqlalchemy.orm import Session


def get_hashed_password(password: str) -> str:
    # Use solely bcrypt instead of passlib, due do this issue: see https://github.com/pyca/bcrypt/issues/684#issuecomment-1902590553
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_byte_bytes = plain_password.encode("utf-8")
    hashed_password_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password=password_byte_bytes, hashed_password=hashed_password_bytes)


def get_pending_users(db: Session):
    return (
        db.query(models.User)
        .filter(models.User.is_confirmed.is_(None))
        .order_by(models.User.id)
        .all()
    )


def create_user(db: Session, user: schemas.UserCreate, commit=True) -> models.User:
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=get_hashed_password(user.password),
    )
    db.add(db_user)
    if commit:
        db.commit()
        db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: int) -> models.User:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> models.User:
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: EmailStr) -> models.User:
    return db.query(models.User).filter(models.User.email == email).first()


def confirm_user(db: Session, db_user: models.User, is_confirmed: bool, commit=True):
    db_user.is_confirmed = is_confirmed
    if commit:
        db.commit()


#
# Tokens
#


def resolve_user_token(db: Session, token: str) -> models.User:
    hash = encode_api_token(token)
    user = (
        db.query(models.User)
        .join(models.User.api_tokens)
        .filter(models.ApiToken.hash == hash)
        .first()
    )
    return user


def get_user_token(db: Session, token: str) -> models.ApiToken:
    hash = encode_api_token(token)
    return db.query(models.ApiToken).filter(models.ApiToken.hash == hash).first()


def get_user_tokens(db: Session, user_id: int) -> list[models.ApiToken]:
    return db.query(models.ApiToken).join(models.User).filter(models.User.id == user_id).all()


def create_user_token(
    db: Session, user_id: int, form_data: schemas.ApiTokenCreate, commit=True
) -> str:
    token = str(uuid.uuid4())
    db_token = models.ApiToken(name=form_data.name, hash=encode_api_token(token), user_id=user_id)
    db.add(db_token)
    if commit:
        db.commit()
        db.refresh(db_token)
    return token


def delete_token(db: Session, token_id: int, commit=True) -> models.ApiToken:
    result = db.query(models.ApiToken).filter(models.ApiToken.id == token_id).delete()
    if commit:
        db.commit()
    return result
