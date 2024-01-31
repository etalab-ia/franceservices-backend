from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app import models
from app.config import APP_VERSION
from app.core.institutions import INSTITUTIONS
from app.deps import get_current_user


router = APIRouter()


@router.get("/healthcheck", tags=["misc"])
def get_healthcheck() -> dict[str, str]:
    return {"msg": "OK", "version": APP_VERSION}


# ****************
# * Institutions *
# ****************


@router.get("/institutions", tags=["misc"])
def get_institutions(
    current_user: models.User = Depends(get_current_user),  # noqa
) -> list[str]:
    return JSONResponse(INSTITUTIONS)
