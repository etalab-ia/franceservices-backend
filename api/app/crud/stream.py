from sqlalchemy.orm import Session

from app import models, schemas


def get_stream(db: Session, stream_id: int) -> models.Stream:
    return db.query(models.Stream).filter(models.Stream.id == stream_id).first()


def get_streams(
    db: Session,
    user_id: str,
    skip: int = 0,
    limit: int | None = 100,
    chat_id: int | None = None,
    desc: bool = False,
) -> list[models.Stream]:
    query = db.query(models.Stream).filter(models.Stream.user_id == user_id)
    if chat_id is not None:
        query = query.filter(models.Stream.chat_id == chat_id)
    if desc:
        query = query.order_by(models.Stream.id.desc())
    else:
        query = query.order_by(models.Stream.id.asc())
    query = query.offset(skip)
    if limit is not None:
        query = query.limit(limit)

    return query.all()


def create_stream(
    db: Session,
    stream: schemas.StreamCreate,
    user_id: int,
    chat_id: int | None = None,
    commit=True,
) -> models.Stream:
    stream = stream.model_dump()

    # @DEBUG/HELP1: How to not have to that manually while avoiding the following exception:
    # AttributeError: 'str' object has no attribute '_sa_instance_state'
    if stream["sources"]:
        stream["sources"] = [
            models.SourceEnum(source_name=source_name) for source_name in stream["sources"]
        ]

    db_stream = models.Stream(
        **stream,
        is_streaming=False,
        user_id=user_id,
        chat_id=chat_id,
    )

    db.add(db_stream)
    if commit:
        db.commit()
        db.refresh(db_stream)
    return db_stream


def set_is_streaming(db: Session, db_stream: models.Stream, is_streaming: bool, commit=True):
    db_stream.is_streaming = is_streaming
    if commit:
        db.commit()


def set_rag_output(
    db: Session, db_stream: models.Stream, response: str, rag_sources: list[str], commit=True
):
    db_stream.response = response
    db_stream.rag_sources = rag_sources
    if commit:
        db.commit()


def set_search_sids(db: Session, db_stream: models.Stream, search_sids: list[str], commit=True):
    db_stream.search_sids = search_sids
    if commit:
        db.commit()
