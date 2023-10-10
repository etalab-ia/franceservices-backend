from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app import models, schemas
from app.core.embeddings import make_embeddings
from app.core.indexes import search_indexes
from app.core.institutions import INSTITUTIONS
from app.deps import get_current_user

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
    name = index.name
    query = index.query
    limit = index.limit
    similarity = index.similarity
    institution = index.institution
    hits = search_indexes(name, query, limit, similarity, institution)
    return JSONResponse(hits)