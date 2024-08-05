from fastapi import APIRouter, Depends, HTTPException, Request

from api.app.clients.keycloak_mail_client import KeycloakMailClient
from api.app.keycloak.clients import client_admin, client_openid
from app import crud, schemas
from app.deps import get_current_user

router = APIRouter()
keycloak_admin = client_admin()
keycloak_openid = client_openid()
keycloak_mail_client = KeycloakMailClient()


@router.post("/sign_in", tags=["public", "login"])
def sign_in(
    form_data: schemas.SignInForm,
):
    username = form_data.username
    password = form_data.password
    
    user = crud.user.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_confirmed:
        raise HTTPException(status_code=400, detail="User not confirmed")
    # user needs to be enabled on keycloak
    token = crud.user.login_user(username, password)

    if not token:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return token


@router.post("/sign_out", tags=["login"])
def sign_out(
    req: Request,
    current_user = Depends(get_current_user),
) -> dict[str, str]:
    try:
        bearer_refresh = req.headers.get("refresh_token")

        if not bearer_refresh:
            raise HTTPException(status_code=400, detail="Refresh token header must be provided")

        refresh_token = bearer_refresh.split(" ")[1]

        crud.user.logout_user(refresh_token)

        return {"msg": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/send_reset_password_email", tags=["login"])
def send_reset_password_email(
    form_data: schemas.SendResetPasswordEmailForm,
) -> dict[str, str]:
    try:
        email = form_data.email
        
        user = crud.user.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        keycloak_mail_client.send_reset_password_email(user.id)

        return {"msg": "Password recovery email sent"}

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=400, detail=str(e))
