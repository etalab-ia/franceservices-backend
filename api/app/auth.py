from datetime import datetime, timedelta

from jose import jwt

from app import crud
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
