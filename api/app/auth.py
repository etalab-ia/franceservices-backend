import hashlib
from datetime import datetime, timedelta

from app import crud
from jose import jwt
from pyalbert.config import ACCESS_TOKEN_TTL, SECRET_KEY

ALGORITHM = "HS256"


def encode_token(user_id):
    dt_now = datetime.utcnow()
    payload = {
        "exp": dt_now + timedelta(seconds=ACCESS_TOKEN_TTL),
        "iat": dt_now,
        "sub": str(user_id),  # with python-jose jwt, sub must be a string
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(db, token):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if crud.login.get_blacklist_token(db, token):
        raise Exception("Blacklisted token")
    return int(payload["sub"])


def encode_api_token(token: str):
    hash = hashlib.sha256(token.encode()).hexdigest()
    return hash


def decode_api_token(db, token):
    return crud.user.resolve_user_token(db, token)
