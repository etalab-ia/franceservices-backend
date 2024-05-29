from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app import models
from app.deps import get_current_user

from pyalbert.config import APP_VERSION, LLM_TABLE
from pyalbert.lexicon.institutions import INSTITUTIONS
from pyalbert.prompt import prompts_from_llm_table

router = APIRouter()


@router.get("/healthcheck", tags=["misc"])
def get_healthcheck() -> dict[str, str]:
    return {"msg": "OK", "version": APP_VERSION}


# **********
# * Models *
# **********
@router.get("/models", tags=["misc"])
def get_models(
    current_user: models.User = Depends(get_current_user), response_model=dict[str, list[str]]
) -> JSONResponse:
    model_prompts = prompts_from_llm_table(LLM_TABLE)
    model_prompts = {k: v for k, v in model_prompts.items() if [v.pop("templates")]}
    return JSONResponse(model_prompts)


# ****************
# * Institutions *
# ****************


@router.get("/institutions", tags=["misc"])
def get_institutions(
    current_user: models.User = Depends(get_current_user), response_model=list[str]
) -> JSONResponse:
    return JSONResponse(INSTITUTIONS)
