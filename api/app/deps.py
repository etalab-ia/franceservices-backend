from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request

from app import crud, models
from app.auth import decode_api_token, decode_token
from app.db.session import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    """Get authenticated user from the Bearer authorization header"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(400, detail="Authorization header must be provided")

    try:
        token = auth_header.split(" ")[1]
    except Exception as e:
        raise HTTPException(401, detail="Unauthorized") from e

    try:
        user = decode_api_token(db, token)
        if not user:
            raise NotImplementedError
    except Exception as e:
        try:
            user_id = decode_token(db, token)
            user = crud.user.get_user(db, user_id)
        except Exception as e2:
            raise HTTPException(401, detail="Unauthorized") from e2

    if not user:
        raise HTTPException(404, detail="User not found")
    if not user.is_confirmed:
        raise HTTPException(400, detail="User not confirmed")
    return user
