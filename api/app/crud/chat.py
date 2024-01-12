from sqlalchemy.orm import Session, joinedload

from app import models, schemas


def get_chat(db: Session, chat_id: int) -> models.Chat:
    return db.query(models.Chat).filter(models.Chat.id == chat_id).first()


def get_chat_archive(db: Session, chat_id: int) -> models.Chat:
    db_chat = (
        db.query(models.Chat)
        .filter(models.Chat.id == chat_id)
        .options(joinedload(models.Chat.streams))
        .first()
    )

    return db_chat


def get_chats(
    db: Session, user_id: str, skip: int = 0, limit: int = 100, desc: bool = False
) -> list[models.Chat]:
    query = db.query(models.Chat).filter(models.Chat.user_id == user_id)
    if desc:
        query = query.order_by(models.Chat.id.desc())
    else:
        query = query.order_by(models.Chat.id.asc())
    return query.offset(skip).limit(limit).all()


def create_chat(db: Session, chat: schemas.ChatCreate, user_id: int, commit=True) -> models.Chat:
    chat = chat.model_dump()
    db_chat = models.Chat(**chat, user_id=user_id)
    db.add(db_chat)
    if commit:
        db.commit()
        db.refresh(db_chat)
    return db_chat


def update_chat(
    db: Session, db_chat: models.Chat, chat_updates: schemas.ChatUpdate, commit=True
) -> models.Chat:
    chat_updates = chat_updates.model_dump()
    for k, v in chat_updates.items():
        setattr(db_chat, k, v) if v is not None else None

    if commit:
        db.commit()

    return db_chat
