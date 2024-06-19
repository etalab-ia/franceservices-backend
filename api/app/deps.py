from api.app import schemas
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


def get_current_user(request: Request) -> schemas.User:
    """Get keycloak authenticated user from the Bearer authorization header"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(400, detail="Authorization header must be provided")

    try:
        token = auth_header.split(" ")[1]
    except Exception as e:
        raise HTTPException(401, detail="Unauthorized") from e

    try:
        user = decode_api_token(token)

        if not user:
            raise NotImplementedError
    except Exception as e:
        raise HTTPException(401, detail="Unauthorized") from e

    if not user:
        raise HTTPException(404, detail="User not found")
    if not user.is_confirmed:
        raise HTTPException(400, detail="User not confirmed")
    return user
