import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import crud, schemas
from app.clients.mailjet_client import MailjetClient
from app.deps import get_db

from pyalbert.config import PASSWORD_RESET_TOKEN_TTL

router = APIRouter()


@router.post("/sign_in", tags=["public", "login"])
def sign_in(
    form_data: schemas.SignInForm,
):
    username = form_data.username
    password = form_data.password

    # user needs to be enabled on keycloak
    token = crud.user.login_user(username, password)

    if not token:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return token


@router.post("/sign_out", tags=["login"])
def sign_out(
    req: Request,
) -> dict[str, str]:
    try:
        auth_header = req.headers.get("Authorization")
        token = auth_header.split(" ")[1]
        crud.user.logout_user(token)
        return {"msg": "Success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/send_reset_password_email", tags=["login"])
def send_reset_password_email(
    form_data: schemas.SendResetPasswordEmailForm,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    email = form_data.email
    app = form_data.app
    user = crud.user.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_id = user.id
    crud.login.delete_password_reset_token(db, user_id, commit=False)
    token = uuid.uuid4().hex
    crud.login.create_password_reset_token(db, token, user_id, commit=False)
    db.commit()

    mailjet_client = MailjetClient()
    mailjet_client.send_reset_password_email(email, token, app)
    return {"msg": "Password recovery email sent"}


@router.post("/reset_password", tags=["login"])
def reset_password(
    form_data: schemas.ResetPasswordForm,
    db: Session = Depends(get_db),
) -> dict[str, str]:
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
