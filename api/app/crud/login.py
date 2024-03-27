from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app import models
from pyalbert.config import ACCESS_TOKEN_TTL


# ******************
# * BlacklistToken *
# ******************


def create_blacklist_token(db: Session, token: str, commit=True):
    db_blacklist_token = models.BlacklistToken(token=token)
    db.add(db_blacklist_token)
    if commit:
        db.commit()
        db.refresh(db_blacklist_token)
    return db_blacklist_token


def get_blacklist_token(db: Session, token: str):
    return db.query(models.BlacklistToken).filter(models.BlacklistToken.token == token).first()


def delete_expired_blacklist_tokens(db: Session, commit=True):
    dt_ttl = datetime.utcnow() - timedelta(seconds=ACCESS_TOKEN_TTL)
    rows = (
        db.query(models.BlacklistToken).filter(models.BlacklistToken.created_at < dt_ttl).delete()
    )
    if commit:
        db.commit()
    return rows


# **********************
# * PasswordResetToken *
# **********************


def create_password_reset_token(db: Session, token: str, user_id: int, commit=True):
    db_password_reset_token = models.PasswordResetToken(token=token, user_id=user_id)
    db.add(db_password_reset_token)
    if commit:
        db.commit()
        db.refresh(db_password_reset_token)
    return db_password_reset_token


def get_password_reset_token(db: Session, token: str):
    return (
        db.query(models.PasswordResetToken).filter(models.PasswordResetToken.token == token).first()
    )


def delete_password_reset_token(db: Session, user_id: int, commit=True):
    rows = (
        db.query(models.PasswordResetToken)
        .filter(models.PasswordResetToken.user_id == user_id)
        .delete()
    )
    if commit:
        db.commit()
    return rows
