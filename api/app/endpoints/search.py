from app import models, schemas
from app.core.embeddings import make_embeddings
from app.core.indexes import search_indexes, get_document
from app.deps import get_current_user
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from commons.prompt_base import Prompter

router = APIRouter()


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


# TODO: rename to /search !?
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
        index.name,
        query,
        index.limit,
        index.similarity,
        index.institution,
        index.sources,
        index.should_sids,
        index.must_not_sids,
    )
    return JSONResponse(hits)


@router.get("/get_chunk/{chunkid}")
def get_chunk(
    chunkid: str,
    current_user: models.User = Depends(get_current_user),  # noqa
):
    hit = get_document("chunks", chunkid)
    return JSONResponse(hit)


@router.get("/get_sheet/{sheetid}")
def get_sheet(
    sheetid: str,
    current_user: models.User = Depends(get_current_user),  # noqa
):
    hit = get_document("sheets", sheetid)
    return JSONResponse(hit)
