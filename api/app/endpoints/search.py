from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core.indexes import get_document, search_indexes
from app.deps import get_current_user, get_db

from pyalbert import get_logger

logger = get_logger()

router = APIRouter()


# ***********
# * Indexes *
# ***********


def get_document_safe(index_name: str, uid: str) -> dict:
    try:
        return get_document(index_name, uid)
    except Exception as err:
        logger.error(f"Chunk or document not found: {err}")
        return {}


# TODO: rename to /search !?
@router.post("/indexes", tags=["search"])
def search(
    index: schemas.Index,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = index.query

    hits = search_indexes(
        index.name,
        query,
        index.limit,
        index.similarity,
        index.institution,
        index.sources,
        index.should_sids,
        index.must_not_sids,
        do_expand_acronyms=index.expand_acronyms
    )

    if index.stream_id:
        # Save the sheets references in the given stream
        db_stream = crud.stream.get_stream(db, index.stream_id)
        if db_stream is None:
            raise HTTPException(404, detail="Stream not found")

        if current_user.id not in (db_stream.user_id, getattr(db_stream.chat, "user_id", None)):
            raise HTTPException(403, detail="Forbidden")

        search_sids = [h["sid"] for h in hits]
        crud.stream.set_search_sids(db, db_stream, search_sids)

    return JSONResponse(hits)


@router.get("/get_chunk/{uid}", tags=["search"])
def get_chunk(
    uid: str,
    current_user: models.User = Depends(get_current_user),  # noqa
):
    hit = get_document_safe("chunks", uid)
    return JSONResponse(hit)


@router.get("/get_sheet/{uid}", tags=["search"])
def get_sheet(
    uid: str,
    current_user: models.User = Depends(get_current_user),  # noqa
):
    hit = get_document_safe("sheets", uid)
    return JSONResponse(hit)


@router.post("/get_chunks", tags=["search"])
def get_chunks(
    uids: schemas.QueryDocs,
    current_user: models.User = Depends(get_current_user),  # noqa
):
    hits = []
    for uid in uids.uids:
        hits.append(get_document_safe("chunks", uid))

    return JSONResponse(hits)


@router.post("/get_sheets", tags=["search"])
def get_sheets(
    uids: schemas.QueryDocs,
    current_user: models.User = Depends(get_current_user),  # noqa
):
    hits = []
    for uid in uids.uids:
        hits.append(get_document_safe("sheets", uid))

    return JSONResponse(hits)
