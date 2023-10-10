from passlib.context import CryptContext
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_hashed_password(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_pending_users(db: Session):
    return (
        db.query(models.User)
        .filter(models.User.is_confirmed.is_(None))
        .order_by(models.User.id)
        .all()
    )


def create_user(db: Session, user: schemas.UserCreate, commit=True):
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


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: EmailStr):
    return db.query(models.User).filter(models.User.email == email).first()


def confirm_user(db: Session, db_user: models.User, is_confirmed: bool, commit=True):
    db_user.is_confirmed = is_confirmed
    if commit:
        db.commit()
