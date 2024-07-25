from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.clients.keycloak_mail_client import KeycloakMailClient
from app import crud, models, schemas
from app.keycloak.clients import client_admin
from app.deps import get_current_user, get_db

from pyalbert.config import CONTACT_EMAIL

router = APIRouter()

# TODO: add update / delete endpoints


@router.get("/user/me", response_model=schemas.User, tags=["user"])
def read_user_me(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    return current_user


@router.get("/users/pending", response_model=list[schemas.User], tags=["user"])
def read_pending_users(
    current_user = Depends(get_current_user),
) -> list:
    if not current_user.is_admin:
        raise HTTPException(403, detail="Forbidden")

    return crud.user.get_pending_users()


@router.post("/user/me", tags=["user"])
def create_user_me(
    form_data: schemas.UserCreate,
) -> dict[str, str]:
    try:
        username = form_data.username
        email = form_data.email
        password = form_data.password
        if not username or not email:
            raise HTTPException(status_code=400, detail="Username and email are required")

        if crud.user.get_user_by_username(username):
            raise HTTPException(status_code=400, detail="Username already exists")

        if crud.user.get_user_by_email(email):
            raise HTTPException(status_code=400, detail="Email already exists")

        user = crud.user.create_user(
            {
                "username": username,
                "email": email,
                "credentials": [{"value": password, "type": "password"}],
                "enabled": True,
                "attributes": {
                    "is_confirmed": False,
                    "created_at": datetime.utcnow().isoformat(),
                    "is_admin": False,
                    "accept_cookie": False,
                    "organization_id": "",
                    "organization_name": "",
                },
            }
        )

        keycloak_mail_client = KeycloakMailClient()
        keycloak_mail_client.send_create_user_me_email(user.id)
        return {
            "msg": "User created. First, please verify your email, then an admin must confirm the user."
        }
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/me", response_model=schemas.User, tags=["user"])
def read_user_me(
    current_user = Depends(get_current_user),
):
    return current_user


@router.get("/user/token/refresh", tags=["user"])
def create_user_token(
    request: Request,
    current_user = Depends(get_current_user),
):
    headers = request.headers
    refresh_token_bearer = headers.get("refresh_token")

    refresh_token = refresh_token_bearer.split(" ")[1]

    return crud.user.refresh_user_token(refresh_token)
