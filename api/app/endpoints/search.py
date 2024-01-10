from app import crud, models, schemas
from app.core.embeddings import make_embeddings
from app.core.indexes import search_indexes, get_document
from app.deps import get_current_user, get_db
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from commons.prompt_base import Prompter

router = APIRouter()


# **************
# * Embeddings *
# **************


@router.post("/embeddings")
def create_embeddings(
    embedding: schemas.Embedding, current_user: models.User = Depends(get_current_user)
):
    embeddings = make_embeddings(embedding.text)
    return JSONResponse(embeddings.tolist())


# ***********
# * Indexes *
# ***********


# TODO: rename to /search !?
@router.post("/indexes")
def search(
    index: schemas.Index,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
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

    if index.stream_id:
        db_stream = crud.stream.get_stream(db, index.stream_id)
        if db_stream is None:
            raise HTTPException(404, detail="Stream not found")

        if current_user.id not in (db_stream.user_id, getattr(db_stream.chat, "user_id", None)):
            raise HTTPException(403, detail="Forbidden")
        # Save the sheets references in the given stream
        search_sids = [h["sid"] for h in hits]
        crud.stream.set_search_sids(db, db_stream, search_sids)

    return JSONResponse(hits)


@router.get("/get_chunk/{uid}")
def get_chunk(
    uid: str,
    current_user: models.User = Depends(get_current_user),  # noqa
):
    hit = get_document("chunks", uid)
    return JSONResponse(hit)


@router.get("/get_sheet/{uid}")
def get_sheet(
    uid: str,
    current_user: models.User = Depends(get_current_user),  # noqa
):
    hit = get_document("sheets", uid)
    return JSONResponse(hit)


@router.post("/get_chunks")
def get_chunks(
    uids: schemas.QueryDocs,
    current_user: models.User = Depends(get_current_user),  # noqa
):
    hits = []
    for uid in uids.uids:
        hits.append(get_document("chunks", uid))

    return JSONResponse(hits)


@router.post("/get_sheets")
def get_sheets(
    uids: schemas.QueryDocs,
    current_user: models.User = Depends(get_current_user),  # noqa
):
    hits = []
    for uid in uids.uids:
        hits.append(get_document("sheets", uid))

    return JSONResponse(hits)
