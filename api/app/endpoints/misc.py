from app.core.institutions import INSTITUTIONS
from app.deps import get_current_user
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse


router = APIRouter()


@router.get("/healthcheck")
def get_healthcheck():
    return {"msg": "OK"}


# ****************
# * Institutions *
# ****************


@router.get("/institutions")
def get_institutions(
    current_user: models.User = Depends(get_current_user),  # noqa
):
    return JSONResponse(INSTITUTIONS)


