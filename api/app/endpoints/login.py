import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.auth import encode_token
from app.config import PASSWORD_RESET_TOKEN_TTL
from app.clients.mailjet_client import MailjetClient
from app.deps import get_db, get_current_user

router = APIRouter()


@router.post("/sign_in")
def sign_in(
    form_data: schemas.SignInForm,
    db: Session = Depends(get_db),
):
    username = form_data.username
    email = form_data.email
    password = form_data.password
    if username:
        user = crud.user.get_user_by_username(db, username)
    else:
        user = crud.user.get_user_by_email(db, email)

    if not user or not crud.user.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    if not user.is_confirmed:
        raise HTTPException(400, detail="User not confirmed")

    crud.login.delete_expired_blacklist_tokens(db)

    token = encode_token(user.id)
    return {"token": token}


@router.post("/sign_out")
def sign_out(
    req: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),  # noqa
):
    auth_header = req.headers.get("Authorization")
    token = auth_header.split(" ")[1]
    crud.login.create_blacklist_token(db, token)
    return {"msg": "Success"}


@router.post("/send_reset_password_email")
def send_reset_password_email(
    form_data: schemas.SendResetPasswordEmailForm,
    db: Session = Depends(get_db),
):
    email = form_data.email
    user = crud.user.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = user.id
    crud.login.delete_password_reset_token(db, user_id, commit=False)
    token = uuid.uuid4().hex
    crud.login.create_password_reset_token(db, token, user_id, commit=False)
    db.commit()

    mailjet_client = MailjetClient()
    mailjet_client.send_reset_password_email(email, token)
    return {"msg": "Password recovery email sent"}


@router.post("/reset_password")
def reset_password(
    form_data: schemas.ResetPasswordForm,
    db: Session = Depends(get_db),
):
    token = form_data.token
    password = form_data.password
    password_reset_token = crud.login.get_password_reset_token(db, token)
    if not password_reset_token:
        raise HTTPException(status_code=400, detail="Invalid token")

    dt_ttl = datetime.utcnow() - timedelta(seconds=PASSWORD_RESET_TOKEN_TTL)
    if password_reset_token.created_at < dt_ttl:
        raise HTTPException(status_code=400, detail="Expired token")

    user_id = password_reset_token.user_id
    user = crud.user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Incorrect email or password")

    if not user.is_confirmed:
        raise HTTPException(400, detail="User not confirmed")

    user.hashed_password = crud.user.get_hashed_password(password)
    crud.login.delete_password_reset_token(db, user_id)
    return {"msg": "Password updated successfully"}