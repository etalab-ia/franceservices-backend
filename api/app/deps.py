from app import crud, models
from app.auth import decode_token
from app.db.session import SessionLocal
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(400, detail="Authorization header must be provided")

    try:
        token = auth_header.split(" ")[1]
        user_id = decode_token(db, token)
    except Exception as e:
        raise HTTPException(401, detail="Unauthorized") from e

    user = crud.user.get_user(db, user_id)
    if not user:
        raise HTTPException(404, detail="User not found")
    if not user.is_confirmed:
        raise HTTPException(400, detail="User not confirmed")
    return user
