from sqlalchemy.orm import Session

from app import models, schemas


def get_streams(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Stream)
        .filter(models.Stream.user_id == user_id)
        .order_by(models.Stream.id)
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
):
    db_stream = models.Stream(
        **stream.model_dump(),
        is_streaming=False,
        user_id=user_id,
        chat_id=chat_id,
    )
    db.add(db_stream)
    if commit:
        db.commit()
        db.refresh(db_stream)
    return db_stream


def get_stream(db: Session, stream_id: int):
    return db.query(models.Stream).filter(models.Stream.id == stream_id).first()


def set_is_streaming(db: Session, db_stream: models.Stream, is_streaming: bool, commit=True):
    db_stream.is_streaming = is_streaming
    if commit:
        db.commit()
