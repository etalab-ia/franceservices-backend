from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app import models
from app.config import APP_VERSION, LLM_TABLE
from app.core.institutions import INSTITUTIONS
from app.deps import get_current_user

router = APIRouter()


@router.get("/healthcheck", tags=["misc"])
def get_healthcheck() -> dict[str, str]:
    return {"msg": "OK", "version": APP_VERSION}


# **********
# * Models *
# **********
@router.get("/models", tags=["misc"])
def get_models(
    current_user: models.User = Depends(get_current_user),  # noqa
) -> list[str]:
    models = [model[0] for model in LLM_TABLE]
    return JSONResponse(models)


# ****************
# * Institutions *
# ****************


@router.get("/institutions", tags=["misc"])
def get_institutions(
    current_user: models.User = Depends(get_current_user),  # noqa
) -> list[str]:
    return JSONResponse(INSTITUTIONS)
