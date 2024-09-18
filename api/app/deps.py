from fastapi import HTTPException
from starlette.requests import Request

from app.auth import decode_api_token
from app.db.session import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request):
    """Get keycloak authenticated user from the Bearer access token header"""

    access_token_bearer = request.headers.get("access_token")
    refresh_token_bearer = request.headers.get("refresh_token")

    if not access_token_bearer:
        raise HTTPException(400, detail="Access token header must be provided")

    if not refresh_token_bearer:
        raise HTTPException(400, detail="Refresh token header must be provided")

    try:
        access_token = access_token_bearer.split(" ")[1]
    except Exception as e:
        raise HTTPException(401, detail="Unauthorized") from e

    try:
        user = decode_api_token(access_token)

        if not user:
            raise NotImplementedError
    except Exception as e:
        raise HTTPException(401, detail="Unauthorized") from e

    if not user:
        raise HTTPException(404, detail="User not found")
    if not user.is_confirmed:
        raise HTTPException(400, detail="User not confirmed")
    return user
