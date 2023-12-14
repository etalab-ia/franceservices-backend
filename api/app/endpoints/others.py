from app import models, schemas
from app.core.embeddings import make_embeddings
from app.core.indexes import search_indexes
from app.core.institutions import INSTITUTIONS
from app.deps import get_current_user
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from commons.prompt_base import Prompter

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


# **************
# * Embeddings *
# **************


@router.post("/embeddings")
def create_embeddings(
    embedding: schemas.Embedding,
    current_user: models.User = Depends(get_current_user),  # noqa
):
    embeddings = make_embeddings(embedding.text)
    return JSONResponse(embeddings.tolist())


# ***********
# * Indexes *
# ***********


@router.post("/indexes")
def get_indexes(
    index: schemas.Index,
    current_user: models.User = Depends(get_current_user),  # noqa
):
    query = index.query
    expand_acronyms = True
    if expand_acronyms:
        query = Prompter._expand_acronyms(index.query)

    hits = search_indexes(
        index.name, query, index.limit, index.similarity, index.institution, index.sources
    )
    return JSONResponse(hits)
