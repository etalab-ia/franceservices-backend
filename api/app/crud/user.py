import bcrypt
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app import models, schemas


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
