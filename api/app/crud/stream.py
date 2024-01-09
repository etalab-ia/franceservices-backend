from app import models, schemas
from sqlalchemy.orm import Session


def get_streams(db: Session, user_id: str, skip: int = 0, limit: int = 100, chat_id: int | None = None) -> list[models.Stream]:
    if chat_id is not None:
        query = db.query(models.Stream).filter(models.Stream.chat_id == chat_id)
    else:
        query = db.query(models.Stream).filter(models.Stream.user_id == user_id)
    return (
        query.order_by(models.Stream.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_stream(
    db: Session,
    stream: schemas.StreamCreate,
    user_id: int | None = None,
    chat_id: int | None = None,
    commit=True,
) -> models.Stream:
    stream = stream.model_dump()

    # @DEBUG: How to not have to that manually while avoiding the following exception:
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


def get_stream(db: Session, stream_id: int) -> models.Stream:
    return db.query(models.Stream).filter(models.Stream.id == stream_id).first()


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
