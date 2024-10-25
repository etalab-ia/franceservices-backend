from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import crud

from pyalbert.config import ALBERT_API_KEY


def decode_api_token(token):
    return crud.user.resolve_user_token(str(token))


def check_api_key(
    api_key: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer(scheme_name="API key"))],
):
    if api_key.scheme != "Bearer":
        raise HTTPException(status_code=403, detail="Invalid authentication scheme")
    if api_key.credentials != ALBERT_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
