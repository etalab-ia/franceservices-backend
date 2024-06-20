from sqlalchemy.orm import Session

from app import models

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
